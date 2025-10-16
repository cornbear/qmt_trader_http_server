#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT交易系统 - Python客户端SDK

这是一个功能完整、使用简洁的QMT交易客户端，封装了所有交易接口。

使用示例：
    # 方式1: 使用登录会话
    client = QMTTradeClient("http://localhost:9091")
    client.login("admin", "password")
    
    # 方式2: 使用API签名（推荐用于程序化交易）
    client = QMTTradeClient(
        "http://localhost:9091",
        client_id="your_client_id",
        secret_key="your_secret_key"
    )
    
    # 获取账户列表
    accounts = client.get_accounts()
    
    # 查询资产
    portfolio = client.get_portfolio(trader_index=0)
    
    # 查询持仓
    positions = client.get_positions(trader_index=0)
    
    # 买入股票（按仓位比例）
    result = client.buy("000001", price=10.50, position_pct=0.1)
    
    # 买入股票（按固定股数）
    result = client.buy("000001", price=10.50, shares=500)
    
    # 卖出股票
    result = client.sell("000001", price=10.60, shares=500)
    
    # 全仓买入
    result = client.buy_all("000001", price=10.50)
    
    # 逆回购
    result = client.reverse_repo(reserve_amount=1000)

作者: QMT交易系统开发团队
版本: 1.0.0
"""

import hmac
import hashlib
import time
import json
import requests
from typing import Optional, Dict, List, Any, Union
from datetime import datetime


class QMTTradeClientError(Exception):
    """QMT交易客户端异常基类"""
    pass


class QMTAuthenticationError(QMTTradeClientError):
    """认证失败异常"""
    pass


class QMTAPIError(QMTTradeClientError):
    """API调用失败异常"""
    pass


class QMTTradeClient:
    """
    QMT交易系统客户端
    
    支持两种认证方式：
    1. 登录会话认证（适用于Web界面交互）
    2. HMAC签名认证（适用于程序化交易）
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:9091",
        client_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化QMT交易客户端
        
        Args:
            base_url: QMT服务器地址，默认 http://localhost:9091
            client_id: API客户端ID（使用签名认证时必需）
            secret_key: API密钥（使用签名认证时必需）
            timeout: 请求超时时间（秒），默认30秒
        """
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.secret_key = secret_key
        self.timeout = timeout
        self.session = requests.Session()
        self.use_signature = bool(client_id and secret_key)
        
        if self.use_signature:
            print(f"✓ 使用API签名认证模式 (client_id: {client_id})")
        else:
            print("✓ 使用登录会话认证模式")
    
    def _generate_signature(
        self, 
        method: str, 
        path: str, 
        query_string: str, 
        body: str, 
        timestamp: str
    ) -> str:
        """生成HMAC-SHA256签名"""
        sign_string = f"{method}\n{path}\n{query_string}\n{body}\n{timestamp}\n{self.client_id}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(
        self, 
        method: str, 
        path: str, 
        data: Optional[Dict] = None,
        use_signature: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST等)
            path: API路径
            data: 请求数据
            use_signature: 是否使用签名认证，None时使用初始化设置
            
        Returns:
            API响应数据
            
        Raises:
            QMTAuthenticationError: 认证失败
            QMTAPIError: API调用失败
        """
        url = f"{self.base_url}{path}"
        headers = {'Content-Type': 'application/json'}
        
        # 判断是否使用签名
        if use_signature is None:
            use_signature = self.use_signature
        
        # 如果使用签名认证
        if use_signature:
            if not self.client_id or not self.secret_key:
                raise QMTAuthenticationError("使用签名认证需要提供 client_id 和 secret_key")
            
            timestamp = str(int(time.time()))
            query_string = ""
            body = json.dumps(data, sort_keys=True, separators=(',', ':')) if data else ""
            
            signature = self._generate_signature(method, path, query_string, body, timestamp)
            
            headers.update({
                'X-Client-ID': self.client_id,
                'X-Timestamp': timestamp,
                'X-Signature': signature
            })
        
        # 发送请求
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(
                    url, 
                    headers=headers, 
                    data=json.dumps(data) if data else None,
                    timeout=self.timeout
                )
            else:
                raise QMTAPIError(f"不支持的HTTP方法: {method}")
            
            # 检查响应状态
            if response.status_code == 401:
                raise QMTAuthenticationError("认证失败，请检查登录状态或API密钥")
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}"
                raise QMTAPIError(f"API调用失败: {error_msg}")
            
            # 返回JSON数据
            return response.json()
            
        except requests.exceptions.Timeout:
            raise QMTAPIError(f"请求超时（{self.timeout}秒）")
        except requests.exceptions.ConnectionError:
            raise QMTAPIError(f"连接失败，请检查服务器地址: {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise QMTAPIError(f"请求异常: {str(e)}")
    
    # ==================== 认证相关 ====================
    
    def login(self, username: str, password: str) -> bool:
        """
        登录QMT系统（会话认证）
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否登录成功
            
        Raises:
            QMTAuthenticationError: 登录失败
        """
        try:
            response = self._request(
                'POST', 
                '/login',
                data={'username': username, 'password': password},
                use_signature=False
            )
            
            if response.get('success'):
                print(f"✓ 登录成功: {username}")
                return True
            else:
                raise QMTAuthenticationError(f"登录失败: {response.get('error', '未知错误')}")
                
        except QMTAPIError as e:
            raise QMTAuthenticationError(f"登录失败: {str(e)}")
    
    def logout(self) -> bool:
        """
        退出登录
        
        Returns:
            是否成功退出
        """
        try:
            self._request('GET', '/logout', use_signature=False)
            print("✓ 已退出登录")
            return True
        except:
            return False
    
    # ==================== 账户查询 ====================
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        获取账户列表
        
        Returns:
            账户列表，每个账户包含: index, account_id, nick_name
            
        Example:
            >>> accounts = client.get_accounts()
            >>> print(accounts)
            [
                {'index': 0, 'account_id': '123456', 'nick_name': '账户1'},
                {'index': 1, 'account_id': '789012', 'nick_name': '账户2'}
            ]
        """
        response = self._request('GET', '/qmt/trade/api/accounts')
        return response.get('accounts', [])
    
    def get_portfolio(self, trader_index: int = 0) -> Dict[str, float]:
        """
        获取账户资产信息
        
        Args:
            trader_index: 交易器索引，默认0
            
        Returns:
            资产信息字典，包含: total_asset, cash, frozen_cash, market_value, profit, profit_ratio
            
        Example:
            >>> portfolio = client.get_portfolio(0)
            >>> print(f"总资产: {portfolio['total_asset']}")
            >>> print(f"可用金额: {portfolio['cash']}")
        """
        response = self._request('GET', f'/qmt/trade/api/portfolio/{trader_index}')
        return response.get('portfolio', {})
    
    def get_positions(self, trader_index: int = 0) -> List[Dict[str, Any]]:
        """
        获取账户持仓信息
        
        Args:
            trader_index: 交易器索引，默认0
            
        Returns:
            持仓列表，每个持仓包含: symbol, name, volume, can_use_volume, 
                                  market_value, avg_price, current_price, profit等
            
        Example:
            >>> positions = client.get_positions(0)
            >>> for pos in positions:
            >>>     print(f"{pos['symbol']} {pos['name']}: {pos['volume']}股")
        """
        response = self._request('GET', f'/qmt/trade/api/positions/{trader_index}')
        return response.get('positions', [])
    
    # ==================== 交易操作 ====================
    
    def buy(
        self,
        symbol: str,
        price: float,
        position_pct: Optional[float] = None,
        shares: Optional[int] = None,
        price_type: int = 0,
        trader_index: Optional[int] = None,
        strategy_name: str = "客户端交易"
    ) -> Dict[str, Any]:
        """
        买入股票/可转债（支持两种模式）
        
        模式1: 按仓位比例买入 (提供 position_pct)
        模式2: 按固定股数买入 (提供 shares)
        
        Args:
            symbol: 股票代码，如 "000001" 或 "000001.SZ"
            price: 买入价格
            position_pct: 仓位比例 (0-1)，如 0.1 表示10%仓位
            shares: 买入股数/张数，股票必须是100的倍数，可转债必须是10的倍数
            price_type: 价格类型，默认0限价单
                       0: 限价
                       1: 最新价
                       2: 最优五档即时成交剩余撤销
                       3: 本方最优
                       5: 对方最优
            trader_index: 交易器索引，None表示所有交易器执行
            strategy_name: 策略名称，用于标识交易来源
            
        Returns:
            交易结果字典
            
        Raises:
            ValueError: 参数错误
            QMTAPIError: 交易失败
            
        Example:
            # 按仓位比例买入（10%仓位）
            >>> result = client.buy("000001", price=10.50, position_pct=0.1)
            
            # 按固定股数买入（500股）
            >>> result = client.buy("000001", price=10.50, shares=500)
            
            # 买入可转债（100张）
            >>> result = client.buy("128013", price=125.50, shares=100)
        """
        # 参数验证
        if position_pct is None and shares is None:
            raise ValueError("必须提供 position_pct 或 shares 其中之一")
        
        if position_pct is not None and shares is not None:
            raise ValueError("position_pct 和 shares 不能同时提供")
        
        # 使用签名认证的外部接口
        if self.use_signature:
            path = '/qmt/trade/api/outer/trade/buy'
            data = {
                'symbol': symbol,
                'trade_price': price,
                'price_type': price_type,
                'strategy_name': strategy_name
            }
            
            if trader_index is not None:
                data['trader_index'] = trader_index
            
            if position_pct is not None:
                data['position_pct'] = position_pct
            else:
                data['order_num'] = shares
            
            return self._request('POST', path, data)
        
        # 使用会话认证的内部接口
        else:
            # 按固定股数买入
            if shares is not None:
                path = '/qmt/trade/api/buy'
                data = {
                    'symbol': symbol,
                    'price': price,
                    'shares': shares,
                    'price_type': price_type,
                    'strategy_name': strategy_name
                }
            # 按仓位比例买入
            else:
                path = '/qmt/trade/api/trade'
                data = {
                    'symbol': symbol,
                    'trade_price': price,
                    'position_pct': position_pct,
                    'pricetype': price_type,
                    'strategy_name': strategy_name
                }
            
            return self._request('POST', path, data)
    
    def sell(
        self,
        symbol: str,
        price: float,
        position_pct: Optional[float] = None,
        shares: Optional[int] = None,
        price_type: int = 0,
        trader_index: Optional[int] = None,
        strategy_name: str = "客户端交易"
    ) -> Dict[str, Any]:
        """
        卖出股票/可转债（支持两种模式）
        
        模式1: 按持仓比例卖出 (提供 position_pct)
        模式2: 按固定股数卖出 (提供 shares)
        
        Args:
            symbol: 股票代码
            price: 卖出价格
            position_pct: 持仓比例 (0-1)，如 1 表示全部卖出
            shares: 卖出股数/张数
            price_type: 价格类型，默认0限价单
            trader_index: 交易器索引，None表示所有交易器执行
            strategy_name: 策略名称
            
        Returns:
            交易结果字典
            
        Example:
            # 按持仓比例卖出（卖出50%）
            >>> result = client.sell("000001", price=10.60, position_pct=0.5)
            
            # 按固定股数卖出（500股）
            >>> result = client.sell("000001", price=10.60, shares=500)
            
            # 全部卖出
            >>> result = client.sell("000001", price=10.60, position_pct=1.0)
        """
        # 参数验证
        if position_pct is None and shares is None:
            raise ValueError("必须提供 position_pct 或 shares 其中之一")
        
        if position_pct is not None and shares is not None:
            raise ValueError("position_pct 和 shares 不能同时提供")
        
        # 使用签名认证的外部接口
        if self.use_signature:
            path = '/qmt/trade/api/outer/trade/sell'
            data = {
                'symbol': symbol,
                'trade_price': price,
                'price_type': price_type,
                'strategy_name': strategy_name
            }
            
            if trader_index is not None:
                data['trader_index'] = trader_index
            
            if position_pct is not None:
                data['position_pct'] = position_pct
            else:
                data['order_num'] = shares
            
            return self._request('POST', path, data)
        
        # 使用会话认证的内部接口
        else:
            path = '/qmt/trade/api/sell'
            data = {
                'symbol': symbol,
                'price': price,
                'shares': shares,
                'price_type': price_type,
                'strategy_name': strategy_name
            }
            
            return self._request('POST', path, data)
    
    def buy_all(
        self,
        symbol: str,
        price: float,
        trader_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        全仓买入（使用所有可用资金）
        
        Args:
            symbol: 股票代码
            price: 买入价格
            trader_index: 交易器索引，None表示所有交易器执行
            
        Returns:
            交易结果字典
            
        Example:
            >>> result = client.buy_all("000001", price=10.50)
        """
        if not self.use_signature:
            raise QMTAPIError("全仓买入接口仅支持签名认证模式")
        
        data = {
            'symbol': symbol,
            'cur_price': price
        }
        
        if trader_index is not None:
            data['trader_index'] = trader_index
        
        return self._request('POST', '/qmt/trade/api/trade/allin', data)
    
    def reverse_repo(
        self,
        reserve_amount: float = 0,
        trader_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        逆回购（使用可用资金购买深圳R-001: 131810.SZ）
        
        Args:
            reserve_amount: 保留资金金额（元），默认0表示全部可用资金购买逆回购
            trader_index: 交易器索引，None表示所有交易器执行
            
        Returns:
            交易结果字典
            
        Example:
            # 全部资金购买逆回购
            >>> result = client.reverse_repo()
            
            # 保留1000元，其余资金购买逆回购
            >>> result = client.reverse_repo(reserve_amount=1000)
        """
        if not self.use_signature:
            raise QMTAPIError("逆回购接口仅支持签名认证模式")
        
        data = {
            'reserve_amount': reserve_amount
        }
        
        if trader_index is not None:
            data['trader_index'] = trader_index
        
        return self._request('POST', '/qmt/trade/api/trade/nhg', data)
    
    # ==================== 订单管理 ====================
    
    def cancel_order(self, order_id: int, trader_index: int) -> Dict[str, Any]:
        """
        撤销指定订单
        
        Args:
            order_id: 订单ID
            trader_index: 交易器索引
            
        Returns:
            撤单结果
            
        Example:
            >>> result = client.cancel_order(12345, trader_index=0)
        """
        if not self.use_signature:
            raise QMTAPIError("撤单接口仅支持签名认证模式")
        
        data = {
            'order_id': order_id,
            'trader_index': trader_index
        }
        
        return self._request('POST', '/qmt/trade/api/cancel_order', data)
    
    def cancel_all_buy_orders(self, trader_index: Optional[int] = None) -> Dict[str, Any]:
        """
        取消所有买单
        
        Args:
            trader_index: 交易器索引，None表示所有交易器执行
            
        Returns:
            撤单结果
            
        Example:
            >>> result = client.cancel_all_buy_orders()
        """
        if not self.use_signature:
            raise QMTAPIError("取消所有买单接口仅支持签名认证模式")
        
        data = {}
        if trader_index is not None:
            data['trader_index'] = trader_index
        
        return self._request('POST', '/qmt/trade/api/cancel_orders/buy', data)
    
    def cancel_all_sell_orders(self, trader_index: Optional[int] = None) -> Dict[str, Any]:
        """
        取消所有卖单
        
        Args:
            trader_index: 交易器索引，None表示所有交易器执行
            
        Returns:
            撤单结果
            
        Example:
            >>> result = client.cancel_all_sell_orders()
        """
        if not self.use_signature:
            raise QMTAPIError("取消所有卖单接口仅支持签名认证模式")
        
        data = {}
        if trader_index is not None:
            data['trader_index'] = trader_index
        
        return self._request('POST', '/qmt/trade/api/cancel_orders/sale', data)
    
    def get_order(self, order_id: int, trader_index: int) -> Dict[str, Any]:
        """
        查询指定订单
        
        Args:
            order_id: 订单ID
            trader_index: 交易器索引
            
        Returns:
            订单详情
            
        Example:
            >>> order = client.get_order(12345, trader_index=0)
        """
        if not self.use_signature:
            raise QMTAPIError("订单查询接口仅支持签名认证模式")
        
        data = {
            'order_id': order_id,
            'trader_index': trader_index
        }
        
        return self._request('POST', '/qmt/trade/api/order', data)
    
    def get_orders(
        self, 
        trader_index: int,
        cancelable_only: bool = False
    ) -> Dict[str, Any]:
        """
        查询所有订单
        
        Args:
            trader_index: 交易器索引
            cancelable_only: 是否只返回可撤销的订单，默认False
            
        Returns:
            订单列表
            
        Example:
            >>> orders = client.get_orders(trader_index=0)
            >>> cancelable_orders = client.get_orders(trader_index=0, cancelable_only=True)
        """
        if not self.use_signature:
            raise QMTAPIError("订单查询接口仅支持签名认证模式")
        
        data = {
            'trader_index': trader_index,
            'cancelable_only': cancelable_only
        }
        
        return self._request('POST', '/qmt/trade/api/orders', data)
    
    # ==================== 便捷方法 ====================
    
    def get_account_summary(self, trader_index: int = 0) -> Dict[str, Any]:
        """
        获取账户汇总信息（资产+持仓）
        
        Args:
            trader_index: 交易器索引，默认0
            
        Returns:
            包含资产和持仓的汇总信息
            
        Example:
            >>> summary = client.get_account_summary(0)
            >>> print(f"总资产: {summary['portfolio']['total_asset']}")
            >>> print(f"持仓数量: {len(summary['positions'])}")
        """
        return {
            'portfolio': self.get_portfolio(trader_index),
            'positions': self.get_positions(trader_index),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_position_by_symbol(
        self, 
        symbol: str, 
        trader_index: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        查询指定股票的持仓
        
        Args:
            symbol: 股票代码
            trader_index: 交易器索引，默认0
            
        Returns:
            持仓信息，如果没有持仓返回None
            
        Example:
            >>> pos = client.get_position_by_symbol("000001.SZ")
            >>> if pos:
            >>>     print(f"持有 {pos['volume']} 股")
        """
        positions = self.get_positions(trader_index)
        for pos in positions:
            if pos.get('symbol') == symbol:
                return pos
        return None
    
    def has_position(self, symbol: str, trader_index: int = 0) -> bool:
        """
        检查是否持有某只股票
        
        Args:
            symbol: 股票代码
            trader_index: 交易器索引，默认0
            
        Returns:
            是否持有该股票
            
        Example:
            >>> if client.has_position("000001.SZ"):
            >>>     print("持有该股票")
        """
        return self.get_position_by_symbol(symbol, trader_index) is not None
    
    def sell_all(
        self,
        symbol: str,
        price: float,
        trader_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        卖出某只股票的全部持仓
        
        Args:
            symbol: 股票代码
            price: 卖出价格
            trader_index: 交易器索引，None表示所有交易器执行
            
        Returns:
            交易结果
            
        Example:
            >>> result = client.sell_all("000001", price=10.60)
        """
        return self.sell(
            symbol=symbol,
            price=price,
            position_pct=1.0,
            trader_index=trader_index,
            strategy_name="清仓卖出"
        )
    
    # ==================== 工具方法 ====================
    
    def __repr__(self) -> str:
        """对象字符串表示"""
        auth_mode = "签名认证" if self.use_signature else "会话认证"
        return f"QMTTradeClient(base_url='{self.base_url}', auth_mode='{auth_mode}')"
    
    def __enter__(self):
        """支持with语句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出with语句时自动关闭会话"""
        self.session.close()
        return False


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    
    print("=" * 60)
    print("QMT交易客户端使用示例")
    print("=" * 60)
    
    # ========== 方式1: 使用登录会话 ==========
    print("\n【方式1: 使用登录会话】")
    print("-" * 60)
    
    client = QMTTradeClient("http://localhost:9091")
    
    # 登录
    try:
        client.login("admin", "password")
    except QMTAuthenticationError as e:
        print(f"✗ 登录失败: {e}")
        return
    
    # 查询账户列表
    print("\n1. 查询账户列表")
    accounts = client.get_accounts()
    for acc in accounts:
        print(f"  - 账户{acc['index']}: {acc['nick_name']} ({acc['account_id']})")
    
    # 查询资产
    print("\n2. 查询账户资产")
    portfolio = client.get_portfolio(0)
    print(f"  总资产: ¥{portfolio['total_asset']:,.2f}")
    print(f"  可用金额: ¥{portfolio['cash']:,.2f}")
    print(f"  持仓市值: ¥{portfolio['market_value']:,.2f}")
    
    # 查询持仓
    print("\n3. 查询持仓信息")
    positions = client.get_positions(0)
    for pos in positions:
        print(f"  - {pos['symbol']} {pos['name']}: {pos['volume']}股, "
              f"成本¥{pos['avg_price']:.2f}, "
              f"现价¥{pos['current_price']:.2f}, "
              f"盈亏¥{pos['profit']:.2f}")
    
    # 退出登录
    client.logout()
    
    # ========== 方式2: 使用API签名 ==========
    print("\n\n【方式2: 使用API签名（推荐用于程序化交易）】")
    print("-" * 60)
    
    client = QMTTradeClient(
        "http://localhost:9091",
        client_id="your_client_id",
        secret_key="your_secret_key"
    )
    
    # 按仓位比例买入
    print("\n4. 按仓位比例买入（10%仓位）")
    try:
        result = client.buy("000001", price=10.50, position_pct=0.1)
        print(f"  ✓ 买入成功: {result}")
    except (ValueError, QMTAPIError) as e:
        print(f"  ✗ 买入失败: {e}")
    
    # 按固定股数买入
    print("\n5. 按固定股数买入（500股）")
    try:
        result = client.buy("000001", price=10.50, shares=500)
        print(f"  ✓ 买入成功: {result}")
    except (ValueError, QMTAPIError) as e:
        print(f"  ✗ 买入失败: {e}")
    
    # 买入可转债
    print("\n6. 买入可转债（100张）")
    try:
        result = client.buy("128013", price=125.50, shares=100)
        print(f"  ✓ 买入成功: {result}")
    except (ValueError, QMTAPIError) as e:
        print(f"  ✗ 买入失败: {e}")
    
    # 卖出股票
    print("\n7. 卖出股票（500股）")
    try:
        result = client.sell("000001", price=10.60, shares=500)
        print(f"  ✓ 卖出成功: {result}")
    except (ValueError, QMTAPIError) as e:
        print(f"  ✗ 卖出失败: {e}")
    
    # 全仓买入
    print("\n8. 全仓买入")
    try:
        result = client.buy_all("000001", price=10.50)
        print(f"  ✓ 全仓买入成功: {result}")
    except QMTAPIError as e:
        print(f"  ✗ 全仓买入失败: {e}")
    
    # 逆回购
    print("\n9. 逆回购（保留1000元）")
    try:
        result = client.reverse_repo(reserve_amount=1000)
        print(f"  ✓ 逆回购成功: {result}")
    except QMTAPIError as e:
        print(f"  ✗ 逆回购失败: {e}")
    
    # 查询账户汇总
    print("\n10. 查询账户汇总信息")
    try:
        summary = client.get_account_summary(0)
        print(f"  总资产: ¥{summary['portfolio']['total_asset']:,.2f}")
        print(f"  持仓数量: {len(summary['positions'])}只")
        print(f"  查询时间: {summary['timestamp']}")
    except QMTAPIError as e:
        print(f"  ✗ 查询失败: {e}")
    
    # 使用with语句
    print("\n11. 使用with语句（自动管理会话）")
    with QMTTradeClient("http://localhost:9091") as client:
        accounts = client.get_accounts()
        print(f"  账户数量: {len(accounts)}")
    
    print("\n" + "=" * 60)
    print("示例结束")
    print("=" * 60)


if __name__ == "__main__":
    # 运行示例
    example_usage()

