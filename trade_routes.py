from flask import Blueprint, jsonify, request, session, redirect, url_for
import qmt_data
from logger_config import get_logger
from config import get_config
from functools import wraps
from authentication import login_or_signature_required, api_signature_required
from qmt_trade import is_convertible_bond, get_min_trade_unit, get_unit_name
import symbol_util


# 通用异常处理装饰器
def handle_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            log.error(f"接口异常 [{f.__name__}]: {str(e)}", exc_info=True)
            return jsonify({'error': f'接口异常: {f.__name__}', 'message': str(e)}), 500

    return decorated_function


# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'error': '未登录，请先登录'}), 401
        return f(*args, **kwargs)

    return decorated_function


# 创建交易相关的蓝图
trade_bp = Blueprint('trade', __name__, url_prefix='/qmt/trade/api')

# 获取日志记录器
log = get_logger(__name__)

# 交易器实例将通过init_trade_routes函数注入
traders = []


def init_trade_routes(traders_list):
    """初始化交易路由，注入交易器实例"""
    global traders
    traders = traders_list
    log.info(f"交易路由初始化完成，共{len(traders)}个交易器")


@trade_bp.route('/accounts')
@login_or_signature_required
@handle_exceptions
def get_accounts():
    """获取账户列表"""
    log.info("获取账户列表")
    accounts = []

    for i, trader in enumerate(traders):
        accounts.append({
            'index': i,
            'account_id': trader.account_id,
            'nick_name': trader.nick_name or f"账户{i + 1}"
        })

    return jsonify({'accounts': accounts})


@trade_bp.route('/portfolio/<int:trader_index>')
@login_or_signature_required
@handle_exceptions
def get_portfolio(trader_index):
    """获取指定账户的资产信息"""
    log.info(f"获取交易器{trader_index}的资产信息")

    if trader_index >= len(traders):
        return jsonify({'error': '无效的交易器索引'}), 400

    trader = traders[trader_index]
    portfolio = trader.get_portfolio()

    if portfolio:
        # 处理XtAsset对象或字典格式
        if hasattr(portfolio, 'total_asset'):
            portfolio_data = {
                'total_asset': portfolio.total_asset,  # 总资产
                'cash': portfolio.cash,  # 可用金额
                'frozen_cash': portfolio.frozen_cash,  # 冻结金额
                'market_value': portfolio.market_value,  # 总市值
                'profit': getattr(portfolio, 'profit', 0),  # 盈亏
                'profit_ratio': getattr(portfolio, 'profit_ratio', 0)  # 盈亏比例
            }
        else:
            portfolio_data = {
                'total_asset': portfolio.get('total_asset', 0),
                'cash': portfolio.get('cash', 0),
                'frozen_cash': portfolio.get('frozen_cash', 0),
                'market_value': portfolio.get('market_value', 0),
                'profit': portfolio.get('profit', 0),
                'profit_ratio': portfolio.get('profit_ratio', 0)
            }

        return jsonify({'portfolio': portfolio_data})
    else:
        return jsonify({'error': '无法获取资产信息'}), 500


@trade_bp.route('/positions/<int:trader_index>')
@login_or_signature_required
@handle_exceptions
def get_positions(trader_index):
    """获取指定账户的持仓信息"""
    log.info(f"获取交易器{trader_index}的持仓信息")

    if trader_index >= len(traders):
        return jsonify({'error': '无效的交易器索引'}), 400

    trader = traders[trader_index]
    positions = trader.get_position()
    position_list = []

    for symbol, pos in positions.items():
        # 处理XtPosition对象或字典格式
        if hasattr(pos, 'volume'):
            # XtPosition对象格式
            volume = getattr(pos, 'volume', 0)
            can_use_volume = getattr(pos, 'can_use_volume', 0)
            frozen_volume = getattr(pos, 'frozen_volume', 0)
            market_value = getattr(pos, 'market_value', 0)
            avg_price = getattr(pos, 'avg_price', 0)
            open_price = getattr(pos, 'open_price', 0)
            log.info(
                f"持仓信息 - 股票代码: {symbol}, 持仓数量: {volume}, 可用数量: {can_use_volume}, 冻结数量: {frozen_volume}, 市值: {market_value}, 成本价: {avg_price}, 开仓价: {open_price}")

            # 打印pos对象的所有属性（调试用）
            # log.debug(f"pos对象类型: {type(pos)}")
            # log.debug(f"pos对象所有属性: {[attr for attr in dir(pos) if not attr.startswith('_')]}")
            # pos对象所有属性: ['account_id', 'account_type', 'avg_price', 'can_use_volume', 'direction', 'float_profit', 'frozen_volume', 'instrument_name', 'last_price', 'm_dAvgPrice', 'm_dFloatProfit', 'm_dMarketValue', 'm_dOpenPrice', 'm_nAccountType', 'm_nCanUseVolume', 'm_nDirection', 'm_nFrozenVolume', 'm_nOnRoadVolume', 'm_nVolume', 'm_nYesterdayVolume', 'm_strAccountID', 'm_strStockCode', 'market_value', 'on_road_volume', 'open_date', 'open_price', 'position_profit', 'profit_rate', 'secu_account', 'stock_code', 'volume', 'yesterday_volume']
            # for attr in dir(pos):
            #     if not attr.startswith('_'):
            #         try:
            #             value = getattr(pos, attr)
            #             if not callable(value):
            #                 log.debug(f"pos.{attr} = {value} (类型: {type(value)})")
            #         except Exception as e:
            #             log.debug(f"获取pos.{attr}失败: {e}")
            # 如果market_value为0，尝试用volume * avg_price计算
            if market_value == 0 and volume > 0 and avg_price > 0:
                market_value = volume * avg_price

            # 计算盈亏和盈亏比例
            try:
                current_price = qmt_data.get_last_price(symbol)  # 获取实时价格
            except:
                current_price = avg_price
            try:
                symbol_name = qmt_data.get_instrument_detail(symbol)['InstrumentName']
            except:
                symbol_name = symbol

            cost_value = volume * avg_price if avg_price > 0 else 0
            current_value = volume * current_price if current_price > 0 else market_value
            profit = current_value - cost_value if cost_value > 0 else 0
            profit_ratio = (profit / cost_value * 100) if cost_value > 0 else 0

            position_data = {
                'symbol': symbol,
                'name': symbol_name,  # 暂时使用股票代码作为名称
                'volume': volume,  # 当前持股
                'can_use_volume': can_use_volume,  # 可用股数
                'frozen_volume': frozen_volume,  # 冻结数量
                'market_value': market_value,  # 市值
                'avg_price': avg_price,  # 成本价
                'open_price': open_price,  # 开仓价
                'current_price': current_price,  # 最新价
                'profit': profit,  # 盈亏
                'profit_ratio': profit_ratio  # 盈亏比例
            }
        else:
            # 字典格式
            volume = pos.get('volume', 0)
            can_use_volume = pos.get('can_use_volume', 0)
            frozen_volume = pos.get('frozen_volume', 0)
            market_value = pos.get('market_value', 0)
            avg_price = pos.get('avg_price', 0)
            open_price = pos.get('open_price', 0)

            # 如果market_value为0，尝试用volume * avg_price计算
            if market_value == 0 and volume > 0 and avg_price > 0:
                market_value = volume * avg_price

            # 计算盈亏和盈亏比例
            current_price = avg_price  # 暂时使用成本价作为当前价
            cost_value = volume * avg_price if avg_price > 0 else 0
            current_value = volume * current_price if current_price > 0 else market_value
            profit = current_value - cost_value if cost_value > 0 else 0
            profit_ratio = (profit / cost_value * 100) if cost_value > 0 else 0

            position_data = {
                'symbol': symbol,
                'name': symbol,
                'volume': volume,
                'can_use_volume': can_use_volume,
                'frozen_volume': frozen_volume,
                'market_value': market_value,
                'avg_price': avg_price,
                'open_price': open_price,
                'current_price': current_price,  # 最新价
                'profit': profit,  # 盈亏
                'profit_ratio': profit_ratio  # 盈亏比例
            }

        position_list.append(position_data)

    log.info(f"交易器{trader_index}持仓信息获取成功，共{len(position_list)}只股票")
    return jsonify({'positions': position_list})


@trade_bp.route('/buy', methods=['POST'])
@login_required
@handle_exceptions
def buy_stock():
    """
    按固定股数/张数买入
    支持：股票（100股为最小单位）、可转债（10张为最小单位）
    
    请求参数：
        - symbol: 股票代码 (必需)
        - price: 买入价格 (必需)
        - shares: 买入股数/张数 (必需)
        - price_type: 价格类型，默认0 (可选)
        - strategy_name: 策略名称，默认'Web界面' (可选)
        - trader_index: 交易器索引，不提供则所有交易器执行 (可选)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400

    symbol = data.get('symbol')
    price = data.get('price')
    shares = data.get('shares')
    price_type = data.get('price_type', 0)
    strategy_name = data.get('strategy_name', 'Web界面')
    trader_index = data.get('trader_index')  # ✨ 新增：支持指定交易器

    if not symbol or price is None or shares is None:
        return jsonify({'error': '缺少必要参数: symbol, price, shares'}), 400

    # 验证交易器索引
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    log.info(f"开始买入: symbol={symbol}, price={price}, shares={shares}, strategy={strategy_name}, trader_index={trader_index}")

    results = []
    for i, trader in enumerate(traders):
        # ✨ 新增：支持指定交易器执行
        if trader_index is not None and i != trader_index:
            continue
        
        try:
            log.info(f"交易器{i}开始买入")
            result = trader.trade_buy_shares(symbol, price, shares, price_type, strategy_name=strategy_name)
            results.append({'trader_index': i, 'result': result, 'status': 'success'})
            log.info(f"交易器{i}买入完成: {result}")
        except Exception as e:
            error_msg = f"交易器{i}买入失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({'trader_index': i, 'error': error_msg, 'status': 'failed'})

    return jsonify({'message': '买入执行完成', 'results': results})


@trade_bp.route('/sell', methods=['POST'])
@login_required
@handle_exceptions
def sell_stock():
    """
    卖出股票/可转债
    支持：股票（100股为最小单位）、可转债（10张为最小单位）
    
    请求参数：
        - symbol: 股票代码 (必需)
        - price: 卖出价格 (必需)
        - shares: 卖出股数/张数 (必需)
        - price_type: 价格类型，默认0 (可选)
        - strategy_name: 策略名称，默认'Web界面' (可选)
        - trader_index: 交易器索引，不提供则所有交易器执行 (可选)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400

    symbol = data.get('symbol')
    price = data.get('price')
    shares = data.get('shares')
    price_type = data.get('price_type', 0)
    strategy_name = data.get('strategy_name', 'Web界面')
    trader_index = data.get('trader_index')  # ✨ 新增：支持指定交易器

    if not symbol or price is None or shares is None:
        return jsonify({'error': '缺少必要参数: symbol, price, shares'}), 400

    # 验证交易器索引
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    log.info(f"开始卖出: symbol={symbol}, price={price}, shares={shares}, strategy={strategy_name}, trader_index={trader_index}")

    results = []
    for i, trader in enumerate(traders):
        # ✨ 新增：支持指定交易器执行
        if trader_index is not None and i != trader_index:
            continue
        
        try:
            log.info(f"交易器{i}开始卖出")
            result = trader.trade_sell(symbol, price, shares, price_type, strategy_name=strategy_name)
            results.append({'trader_index': i, 'result': result, 'status': 'success'})
            log.info(f"交易器{i}卖出完成: {result}")
        except Exception as e:
            error_msg = f"交易器{i}卖出失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({'trader_index': i, 'error': error_msg, 'status': 'failed'})

    return jsonify({'message': '卖出执行完成', 'results': results})


@trade_bp.route('/trade', methods=['POST'])
@login_required
@handle_exceptions
def trade():
    """
    按仓位比例交易
    
    请求参数：
        - symbol: 股票代码 (必需)
        - trade_price: 交易价格 (必需)
        - position_pct: 仓位比例 (必需，0-1之间)
        - pricetype: 价格类型，默认0 (可选)
        - strategy_name: 策略名称，默认'Web界面' (可选)
        - trader_index: 交易器索引，不提供则所有交易器执行 (可选)
    """

    # 获取请求参数
    data = request.get_json()
    if not data:
        log.error("请求数据为空")
        return jsonify({"error": "请求数据不能为空"}), 400

    symbol = data.get('symbol')
    trade_price = data.get('trade_price')
    position_pct = data.get('position_pct')
    pricetype = data.get('pricetype', 0)
    strategy_name = data.get('strategy_name', 'Web界面')
    trader_index = data.get('trader_index')  # ✨ 新增：支持指定交易器

    # 参数验证
    if not symbol or trade_price is None or position_pct is None:
        log.error(f"参数不完整: symbol={symbol}, trade_price={trade_price}, position_pct={position_pct}")
        return jsonify({"error": "缺少必要参数: symbol, trade_price, position_pct"}), 400

    # 验证交易器索引
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    log.info(f"开始执行交易: symbol={symbol}, trade_price={trade_price}, position_pct={position_pct}, strategy={strategy_name}, trader_index={trader_index}")

    # 执行交易
    results = []
    for i, trader in enumerate(traders):
        # ✨ 新增：支持指定交易器执行
        if trader_index is not None and i != trader_index:
            continue
        
        try:
            log.info(f"交易器{i}开始执行交易")
            result = trader.trade_target_pct(symbol, trade_price, position_pct, pricetype, strategy_name=strategy_name)
            results.append({"trader_index": i, "result": result, "status": "success"})
            log.info(f"交易器{i}交易完成: {result}")
        except Exception as e:
            error_msg = f"交易器{i}交易失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({"trader_index": i, "error": error_msg, "status": "failed"})

    log.info(f"所有交易器执行完成，结果: {results}")
    return jsonify({"message": "交易执行完成", "results": results})


@trade_bp.route('/outer/trade/<operation>', methods=['POST'])
@api_signature_required
@handle_exceptions
def outer_trade(operation):
    """
    第三方调用的交易接口（使用HMAC签名验证）
    
    支持两种交易模式：
    1. 按仓位比例交易：提供 position_pct 参数 (0-1之间的小数)
    2. 按固定股数/张数交易：提供 order_num 参数
       - 股票：必须是100的倍数
       - 可转债：必须是10的倍数
    
    请求参数：
        - operation: 'buy' 或 'sell' (URL路径参数)
        - symbol: 股票/可转债代码 (必需)
        - trade_price: 交易价格 (必需)
        - price_type: 价格类型，默认0 (可选，0:限价, 1:最新价, 2:最优五档即时成交剩余撤销, 3:本方最优, 5:对方最优)
        - position_pct: 仓位比例 (与order_num二选一)
        - order_num: 委托股数/张数 (与position_pct二选一)
        - trader_index: 交易器索引，不提供则所有交易器执行 (可选)
        - strategy_name: 策略名称 (可选)
    """
    if operation not in ['buy', 'sell']:
        return jsonify({"error": "操作类型必须是 buy 或 sell"}), 400

    # 获取请求参数
    data = request.get_json()
    if not data:
        log.error("第三方交易请求数据为空")
        return jsonify({"error": "请求数据不能为空"}), 400

    trader_index = data.get('trader_index')
    symbol = data.get('symbol')
    trade_price = data.get('trade_price')
    price_type = data.get('price_type', 0)
    position_pct = data.get('position_pct')
    order_num = data.get('order_num')
    strategy_name = data.get('strategy_name', '外部策略')

    # 基本参数验证
    if not symbol or trade_price is None:
        log.error(f"第三方{operation}交易参数不完整: symbol={symbol}, trade_price={trade_price}")
        return jsonify({"error": "缺少必要参数: symbol, trade_price"}), 400

    # 交易模式参数验证：position_pct 和 order_num 二选一
    if position_pct is None and order_num is None:
        log.error(f"第三方{operation}交易缺少交易数量参数")
        return jsonify({"error": "必须提供 position_pct 或 order_num 其中之一"}), 400
    
    if position_pct is not None and order_num is not None:
        log.error(f"第三方{operation}交易同时提供了position_pct和order_num")
        return jsonify({"error": "position_pct 和 order_num 不能同时提供，请选择其中一个"}), 400

    # 确定交易模式
    if position_pct is not None:
        trade_mode = "position_pct"
        trade_param = position_pct
        # 验证仓位比例范围
        if not (0 <= position_pct <= 1):
            log.error(f"仓位比例超出范围: {position_pct}")
            return jsonify({"error": "position_pct 必须在 0 到 1 之间"}), 400
    else:
        trade_mode = "order_num"
        trade_param = order_num
        # 验证股数/张数
        if order_num <= 0:
            log.error(f"委托数量无效: {order_num}")
            return jsonify({"error": "order_num 必须大于 0"}), 400
        
        # 根据证券类型验证最小单位
        converted_symbol = symbol_util.get_stock_id_xt(symbol)
        min_unit = get_min_trade_unit(converted_symbol)
        unit_name = get_unit_name(converted_symbol)
        
        if order_num % min_unit != 0:
            log.error(f"委托{unit_name}数不是{min_unit}的倍数: {order_num}")
            return jsonify({"error": f"order_num 必须是 {min_unit} 的倍数（{unit_name}）"}), 400

    # 验证交易器索引
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    log.info(
        f"第三方开始执行{operation}交易: symbol={symbol}, trade_price={trade_price}, "
        f"trade_mode={trade_mode}, trade_param={trade_param}, price_type={price_type}, strategy_name={strategy_name}")

    # 执行交易
    results = []
    for i, trader in enumerate(traders):
        try:
            if trader_index is not None and i != trader_index:
                continue

            log.info(f"第三方调用-交易器{i}开始执行{operation}交易 (模式: {trade_mode})")
            
            # 根据操作类型和交易模式选择对应的方法
            if operation == 'buy':
                if trade_mode == "position_pct":
                    # 按仓位比例买入
                    result = trader.trade_target_pct(symbol, trade_price, position_pct, price_type, strategy_name=strategy_name)
                else:
                    # 按固定股数买入
                    result = trader.trade_buy_shares(symbol, trade_price, order_num, price_type, strategy_name=strategy_name)
            else:  # sell
                if trade_mode == "position_pct":
                    # 按仓位比例卖出
                    result = trader.trade_sell_target_pct(symbol, trade_price, position_pct, price_type, strategy_name=strategy_name)
                else:
                    # 按固定股数卖出
                    result = trader.trade_sell(symbol, trade_price, order_num, price_type, strategy_name=strategy_name)
            
            results.append({"trader_index": i, "result": result, "status": "success"})
            log.info(f"第三方调用-交易器{i}{operation}交易完成 ({trade_mode}={trade_param}): {result}")
        except Exception as e:
            error_msg = f"第三方调用-交易器{i}{operation}交易失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({"trader_index": i, "error": error_msg, "status": "failed"})

    log.info(f"第三方调用-所有交易器{operation}执行完成，结果: {results}")
    return jsonify({
        "message": f"第三方{operation}交易执行完成",
        "operation": operation,
        "trade_mode": trade_mode,
        "trade_param": trade_param,
        "strategy_name": strategy_name,
        "results": results
    })


@trade_bp.route('/trade/allin', methods=['POST'])
@api_signature_required
@handle_exceptions
def trade_allin():
    """全仓买入接口"""
    data = request.get_json()
    symbol = data.get('symbol')
    cur_price = data.get('cur_price')
    trader_index = data.get('trader_index')

    if not symbol or cur_price is None:
        return jsonify({'error': '缺少必要参数: symbol, cur_price'}), 400

    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    results = []
    ##accounts = [traders[trader_index]] if trader_index is not None else traders
    for i, trader in enumerate(traders):
        try:
            if trader_index is not None and i != trader_index:
                continue
                
            result = trader.trade_allin(symbol, cur_price)
            results.append({'trader_index': i, 'result': result, 'status': 'success'})
        except Exception as e:
            results.append({'trader_index': i, 'error': str(e), 'status': 'failed'})

    return jsonify({'message': '全仓买入完成', 'results': results})


@trade_bp.route('/trade/nhg', methods=['POST'])
@api_signature_required
@handle_exceptions
def nhg():
    """
    逆回购接口
    
    使用可用资金购买逆回购（深圳R-001: 131810.SZ）
    
    请求参数:
        - trader_index: 交易器索引 (可选，不提供则所有交易器执行)
        - reserve_amount: 保留资金金额（元），默认0表示全部可用资金购买逆回购 (可选)
                        例如: 1000 表示保留1000元，其余资金购买逆回购
    
    示例:
        {
            "trader_index": 0,
            "reserve_amount": 1000
        }
    """
    results = []
    data = request.get_json()
    if not data:
        data = {}
    
    trader_index = data.get('trader_index')
    reserve_amount = data.get('reserve_amount', 0)  # 默认不保留资金
    
    # 验证参数
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400
    
    if reserve_amount < 0:
        log.error(f"保留金额不能为负数: {reserve_amount}")
        return jsonify({"error": "保留金额不能为负数"}), 400

    log.info(f"开始逆回购操作: trader_index={trader_index}, reserve_amount={reserve_amount}")

    for i, trader in enumerate(traders):
        try:
            if trader_index is not None and i != trader_index:
                continue
            
            log.info(f"交易器{i}开始逆回购, 保留资金{reserve_amount}元")
            result = trader.nhg(reserve_amount=reserve_amount)
            results.append({
                'trader_index': i, 
                'result': result,
                'status': 'success' if result.get('success') else 'failed'
            })
            log.info(f"交易器{i}逆回购完成: {result.get('message')}")
        except Exception as e:
            error_msg = f"交易器{i}逆回购失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({
                'trader_index': i, 
                'error': str(e), 
                'status': 'failed'
            })

    log.info(f"所有交易器逆回购执行完成，结果: {results}")
    return jsonify({
        'message': '逆回购执行完成', 
        'reserve_amount': reserve_amount,
        'results': results
    })


@trade_bp.route('/cancel_orders/sale', methods=['POST'])
@api_signature_required
@handle_exceptions
def cancel_all_orders_sale():
    """取消所有卖单接口"""
    results = []
    data = request.get_json()
    trader_index = data.get('trader_index')
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    ##accounts = [traders[trader_index]] if trader_index is not None else traders
    for i, trader in enumerate(traders):
        try:
            if trader_index is not None and i != trader_index:
                continue
                
            trader.cancel_all_orders_sale()
            results.append({'trader_index': i, 'status': 'success'})
        except Exception as e:
            results.append({'trader_index': i, 'error': str(e), 'status': 'failed'})

    return jsonify({'message': '取消所有卖单完成', 'results': results})


@trade_bp.route('/cancel_orders/buy', methods=['POST'])
@api_signature_required
@handle_exceptions
def cancel_all_orders_buy():
    """取消所有买单接口"""
    results = []
    data = request.get_json()
    trader_index = data.get('trader_index')
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    ##accounts = [traders[trader_index]] if trader_index is not None else traders
    for i, trader in enumerate(traders):
        try:
            if trader_index is not None and i != trader_index:
                continue
                
            trader.cancel_all_orders_buy()
            results.append({'trader_index': i, 'status': 'success'})
        except Exception as e:
            results.append({'trader_index': i, 'error': str(e), 'status': 'failed'})

    return jsonify({'message': '取消所有买单完成', 'results': results})


@trade_bp.route('/cancel_order', methods=['POST'])
@api_signature_required
@handle_exceptions
def cancel_order():
    """撤单接口"""
    data = request.get_json()
    order_id = data.get('order_id')
    trader_index = data.get('trader_index')
    if trader_index is None or trader_index >= len(traders) or trader_index < 0:
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    trader = traders[trader_index]
    return jsonify(trader.cancel_order(order_id))


@trade_bp.route('/order', methods=['POST'])
@api_signature_required
@handle_exceptions
def order():
    """订单查询"""
    data = request.get_json()
    order_id = data.get('order_id')
    trader_index = data.get('trader_index')
    if trader_index is None or trader_index >= len(traders) or trader_index < 0:
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    trader = traders[trader_index]
    return jsonify(trader.query_order(order_id))


@trade_bp.route('/orders', methods=['POST'])
@api_signature_required
@handle_exceptions
def orders():
    """所有订单查询"""

    data = request.get_json()
    trader_index = data.get('trader_index')
    cancelable_only = data.get('cancelable_only', False)
    if trader_index is None or trader_index >= len(traders) or trader_index < 0:
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    trader = traders[trader_index]
    return jsonify(trader.query_orders(cancelable_only))
