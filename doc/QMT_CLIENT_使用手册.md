# QMT交易客户端使用手册

> 一个功能完整、使用简洁的Python SDK，封装所有QMT交易功能

**版本**: 1.0.0  
**作者**: QMT交易系统开发团队

---

## 📋 目录

1. [快速开始](#快速开始)
2. [安装依赖](#安装依赖)
3. [认证方式](#认证方式)
4. [核心功能](#核心功能)
5. [完整API参考](#完整api参考)
6. [实战示例](#实战示例)
7. [错误处理](#错误处理)
8. [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 最简单的示例

```python
from qmt_trade_client import QMTTradeClient

# 创建客户端（使用API签名认证）
client = QMTTradeClient(
    base_url="http://localhost:9091",
    client_id="your_client_id",
    secret_key="your_secret_key"
)

# 查询账户资产
portfolio = client.get_portfolio(0)
print(f"总资产: {portfolio['total_asset']}")

# 买入股票（10%仓位）
result = client.buy("000001", price=10.50, position_pct=0.1)
print(result)

# 卖出股票（500股）
result = client.sell("000001", price=10.60, shares=500)
print(result)
```

---

## 📦 安装依赖

客户端依赖以下Python库：

```bash
pip install requests
```

或使用 `requirements.txt`:

```bash
pip install -r requirements.txt
```

**系统要求**:
- Python 3.7+
- QMT交易服务器运行中

---

## 🔐 认证方式

客户端支持两种认证方式：

### 方式1: 登录会话认证

适用于Web界面交互、短期脚本。

```python
client = QMTTradeClient("http://localhost:9091")

# 登录
client.login("admin", "password")

# 执行交易
portfolio = client.get_portfolio(0)

# 退出登录
client.logout()
```

**优点**:
- ✅ 简单直接
- ✅ 适合交互式使用

**缺点**:
- ❌ 需要手动管理登录状态
- ❌ 会话可能过期

### 方式2: API签名认证（推荐）

适用于程序化交易、自动化策略。

```python
client = QMTTradeClient(
    base_url="http://localhost:9091",
    client_id="your_client_id",
    secret_key="your_secret_key"
)

# 直接执行交易，无需登录
result = client.buy("000001", price=10.50, position_pct=0.1)
```

**优点**:
- ✅ 无需登录，自动认证
- ✅ 更安全（HMAC-SHA256签名）
- ✅ 适合长期运行的策略
- ✅ 支持多客户端并发

**缺点**:
- ❌ 需要预先配置client_id和secret_key

**如何获取API密钥？**

在QMT服务器的配置文件中添加：

```yaml
# config.yaml
outer_api_clients:
  - client_id: "your_client_id"
    secret_key: "your_secret_key"
    name: "我的策略客户端"
```

---

## 🎯 核心功能

### 1. 账户查询

#### 获取账户列表

```python
accounts = client.get_accounts()

for acc in accounts:
    print(f"账户{acc['index']}: {acc['nick_name']}")
```

**返回格式**:
```python
[
    {
        'index': 0,
        'account_id': '123456',
        'nick_name': '账户1'
    },
    {
        'index': 1,
        'account_id': '789012',
        'nick_name': '账户2'
    }
]
```

#### 获取账户资产

```python
portfolio = client.get_portfolio(trader_index=0)

print(f"总资产: {portfolio['total_asset']}")
print(f"可用金额: {portfolio['cash']}")
print(f"冻结金额: {portfolio['frozen_cash']}")
print(f"持仓市值: {portfolio['market_value']}")
print(f"盈亏: {portfolio['profit']}")
print(f"盈亏比例: {portfolio['profit_ratio']}%")
```

#### 获取持仓信息

```python
positions = client.get_positions(trader_index=0)

for pos in positions:
    print(f"{pos['symbol']} {pos['name']}")
    print(f"  持仓: {pos['volume']}股")
    print(f"  可用: {pos['can_use_volume']}股")
    print(f"  成本价: {pos['avg_price']}")
    print(f"  现价: {pos['current_price']}")
    print(f"  市值: {pos['market_value']}")
    print(f"  盈亏: {pos['profit']} ({pos['profit_ratio']:.2f}%)")
```

### 2. 买入操作

#### 按仓位比例买入

```python
# 买入10%仓位
result = client.buy(
    symbol="000001",
    price=10.50,
    position_pct=0.1,
    strategy_name="我的策略"
)
```

#### 按固定股数买入

```python
# 买入500股
result = client.buy(
    symbol="000001",
    price=10.50,
    shares=500
)
```

#### 买入可转债

```python
# 买入100张可转债
result = client.buy(
    symbol="128013",  # 可转债代码
    price=125.50,
    shares=100  # 可转债最小10张
)
```

#### 使用不同价格类型

```python
# 限价单（默认）
client.buy("000001", price=10.50, shares=500, price_type=0)

# 最新价
client.buy("000001", price=10.50, shares=500, price_type=1)

# 最优五档即时成交剩余撤销
client.buy("000001", price=10.50, shares=500, price_type=2)

# 本方最优
client.buy("000001", price=10.50, shares=500, price_type=3)

# 对方最优
client.buy("000001", price=10.50, shares=500, price_type=5)
```

**价格类型说明**:

| 代码 | 名称 | 说明 |
|-----|------|------|
| 0 | 限价 | 按指定价格委托 |
| 1 | 最新价 | 按当前最新成交价委托 |
| 2 | 最优五档即时成交剩余撤销 | 对手方最优五档价格委托 |
| 3 | 本方最优 | 本方最优价格委托 |
| 5 | 对方最优 | 对手方最优价格委托 |

#### 全仓买入

```python
# 使用所有可用资金买入
result = client.buy_all(
    symbol="000001",
    price=10.50
)
```

### 3. 卖出操作

#### 按持仓比例卖出

```python
# 卖出50%持仓
result = client.sell(
    symbol="000001",
    price=10.60,
    position_pct=0.5
)

# 全部卖出
result = client.sell(
    symbol="000001",
    price=10.60,
    position_pct=1.0
)
```

#### 按固定股数卖出

```python
# 卖出500股
result = client.sell(
    symbol="000001",
    price=10.60,
    shares=500
)
```

#### 便捷方法：清仓卖出

```python
# 卖出某只股票的全部持仓
result = client.sell_all(
    symbol="000001",
    price=10.60
)
```

### 4. 订单管理

#### 查询订单

```python
# 查询所有订单
orders = client.get_orders(trader_index=0)

# 只查询可撤销的订单
cancelable_orders = client.get_orders(
    trader_index=0,
    cancelable_only=True
)

# 查询指定订单
order = client.get_order(
    order_id=12345,
    trader_index=0
)
```

#### 撤销订单

```python
# 撤销指定订单
result = client.cancel_order(
    order_id=12345,
    trader_index=0
)

# 取消所有买单
result = client.cancel_all_buy_orders()

# 取消所有卖单
result = client.cancel_all_sell_orders()
```

### 5. 其他功能

#### 逆回购

```python
# 全部资金购买逆回购
result = client.reverse_repo()

# 保留1000元，其余资金购买逆回购
result = client.reverse_repo(reserve_amount=1000)
```

#### 账户汇总信息

```python
# 一次获取资产+持仓
summary = client.get_account_summary(trader_index=0)

print(f"总资产: {summary['portfolio']['total_asset']}")
print(f"持仓数量: {len(summary['positions'])}只")
print(f"查询时间: {summary['timestamp']}")
```

#### 检查持仓

```python
# 检查是否持有某只股票
if client.has_position("000001.SZ"):
    print("持有该股票")
else:
    print("未持有该股票")

# 获取指定股票的持仓
pos = client.get_position_by_symbol("000001.SZ")
if pos:
    print(f"持有 {pos['volume']} 股")
```

---

## 📚 完整API参考

### 类: QMTTradeClient

#### 初始化

```python
QMTTradeClient(
    base_url: str = "http://localhost:9091",
    client_id: Optional[str] = None,
    secret_key: Optional[str] = None,
    timeout: int = 30
)
```

**参数**:
- `base_url`: QMT服务器地址
- `client_id`: API客户端ID（签名认证）
- `secret_key`: API密钥（签名认证）
- `timeout`: 请求超时时间（秒）

---

### 认证方法

#### login()

```python
client.login(username: str, password: str) -> bool
```

登录QMT系统（会话认证）

#### logout()

```python
client.logout() -> bool
```

退出登录

---

### 查询方法

#### get_accounts()

```python
client.get_accounts() -> List[Dict[str, Any]]
```

获取账户列表

#### get_portfolio()

```python
client.get_portfolio(trader_index: int = 0) -> Dict[str, float]
```

获取账户资产信息

#### get_positions()

```python
client.get_positions(trader_index: int = 0) -> List[Dict[str, Any]]
```

获取账户持仓信息

#### get_account_summary()

```python
client.get_account_summary(trader_index: int = 0) -> Dict[str, Any]
```

获取账户汇总信息（资产+持仓）

#### get_position_by_symbol()

```python
client.get_position_by_symbol(
    symbol: str,
    trader_index: int = 0
) -> Optional[Dict[str, Any]]
```

查询指定股票的持仓

#### has_position()

```python
client.has_position(symbol: str, trader_index: int = 0) -> bool
```

检查是否持有某只股票

---

### 交易方法

#### buy()

```python
client.buy(
    symbol: str,
    price: float,
    position_pct: Optional[float] = None,
    shares: Optional[int] = None,
    price_type: int = 0,
    trader_index: Optional[int] = None,
    strategy_name: str = "客户端交易"
) -> Dict[str, Any]
```

买入股票/可转债

**参数**:
- `symbol`: 股票代码
- `price`: 买入价格
- `position_pct`: 仓位比例 (0-1)
- `shares`: 买入股数/张数
- `price_type`: 价格类型 (0-5)
- `trader_index`: 交易器索引
- `strategy_name`: 策略名称

**注意**: `position_pct` 和 `shares` 二选一

#### sell()

```python
client.sell(
    symbol: str,
    price: float,
    position_pct: Optional[float] = None,
    shares: Optional[int] = None,
    price_type: int = 0,
    trader_index: Optional[int] = None,
    strategy_name: str = "客户端交易"
) -> Dict[str, Any]
```

卖出股票/可转债

#### buy_all()

```python
client.buy_all(
    symbol: str,
    price: float,
    trader_index: Optional[int] = None
) -> Dict[str, Any]
```

全仓买入

#### sell_all()

```python
client.sell_all(
    symbol: str,
    price: float,
    trader_index: Optional[int] = None
) -> Dict[str, Any]
```

清仓卖出

#### reverse_repo()

```python
client.reverse_repo(
    reserve_amount: float = 0,
    trader_index: Optional[int] = None
) -> Dict[str, Any]
```

逆回购

---

### 订单方法

#### get_order()

```python
client.get_order(order_id: int, trader_index: int) -> Dict[str, Any]
```

查询指定订单

#### get_orders()

```python
client.get_orders(
    trader_index: int,
    cancelable_only: bool = False
) -> Dict[str, Any]
```

查询所有订单

#### cancel_order()

```python
client.cancel_order(order_id: int, trader_index: int) -> Dict[str, Any]
```

撤销指定订单

#### cancel_all_buy_orders()

```python
client.cancel_all_buy_orders(
    trader_index: Optional[int] = None
) -> Dict[str, Any]
```

取消所有买单

#### cancel_all_sell_orders()

```python
client.cancel_all_sell_orders(
    trader_index: Optional[int] = None
) -> Dict[str, Any]
```

取消所有卖单

---

## 💡 实战示例

### 示例1: 简单的交易脚本

```python
from qmt_trade_client import QMTTradeClient

# 创建客户端
client = QMTTradeClient(
    "http://localhost:9091",
    client_id="my_strategy",
    secret_key="my_secret_key"
)

# 查询账户资产
portfolio = client.get_portfolio(0)
print(f"可用资金: ¥{portfolio['cash']:,.2f}")

# 如果有足够资金，买入股票
if portfolio['cash'] >= 10000:
    result = client.buy("000001", price=10.50, shares=500)
    print(f"买入结果: {result}")
else:
    print("资金不足，无法买入")
```

### 示例2: 网格交易策略

```python
from qmt_trade_client import QMTTradeClient
import time

client = QMTTradeClient(
    "http://localhost:9091",
    client_id="grid_strategy",
    secret_key="secret"
)

# 网格参数
symbol = "000001"
base_price = 10.00
grid_size = 0.10  # 网格间距
grid_levels = 5   # 网格层数
shares_per_grid = 100  # 每格买入股数

# 生成买入价格网格
buy_prices = [base_price - i * grid_size for i in range(1, grid_levels + 1)]

# 在每个价格网格挂单
for price in buy_prices:
    try:
        result = client.buy(symbol, price=price, shares=shares_per_grid)
        print(f"✓ 在 ¥{price:.2f} 挂买单 {shares_per_grid}股")
    except Exception as e:
        print(f"✗ 挂单失败: {e}")
    
    time.sleep(0.5)  # 避免请求过快
```

### 示例3: 持仓监控脚本

```python
from qmt_trade_client import QMTTradeClient
import time
from datetime import datetime

client = QMTTradeClient(
    "http://localhost:9091",
    client_id="monitor",
    secret_key="secret"
)

def monitor_positions():
    """监控持仓并自动止盈止损"""
    
    positions = client.get_positions(0)
    
    for pos in positions:
        symbol = pos['symbol']
        cost_price = pos['avg_price']
        current_price = pos['current_price']
        profit_ratio = pos['profit_ratio']
        
        print(f"\n{symbol} {pos['name']}")
        print(f"  成本价: ¥{cost_price:.2f}")
        print(f"  现价: ¥{current_price:.2f}")
        print(f"  盈亏比例: {profit_ratio:.2f}%")
        
        # 止盈：盈利超过10%，卖出50%
        if profit_ratio >= 10:
            print(f"  → 触发止盈，卖出50%持仓")
            sell_shares = pos['can_use_volume'] // 2
            if sell_shares >= 100:
                client.sell(symbol, price=current_price * 0.99, shares=sell_shares)
        
        # 止损：亏损超过5%，全部卖出
        elif profit_ratio <= -5:
            print(f"  → 触发止损，全部卖出")
            client.sell_all(symbol, price=current_price * 0.99)

# 每分钟检查一次
while True:
    try:
        print(f"\n{'='*60}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        monitor_positions()
        
        time.sleep(60)  # 等待60秒
        
    except KeyboardInterrupt:
        print("\n监控已停止")
        break
    except Exception as e:
        print(f"✗ 监控异常: {e}")
        time.sleep(60)
```

### 示例4: 批量下单脚本

```python
from qmt_trade_client import QMTTradeClient
import time

client = QMTTradeClient(
    "http://localhost:9091",
    client_id="batch_trader",
    secret_key="secret"
)

# 批量买入列表
buy_list = [
    {"symbol": "000001", "price": 10.50, "shares": 500},
    {"symbol": "000002", "price": 20.30, "shares": 300},
    {"symbol": "600000", "price": 15.20, "shares": 400},
]

print(f"准备批量买入 {len(buy_list)} 只股票\n")

for item in buy_list:
    try:
        result = client.buy(**item)
        print(f"✓ {item['symbol']}: 买入 {item['shares']}股 @ ¥{item['price']}")
        time.sleep(0.5)  # 避免请求过快
    except Exception as e:
        print(f"✗ {item['symbol']}: 买入失败 - {e}")

print("\n批量下单完成")
```

### 示例5: 使用with语句

```python
from qmt_trade_client import QMTTradeClient

# 使用with语句，自动管理会话
with QMTTradeClient("http://localhost:9091") as client:
    # 登录
    client.login("admin", "password")
    
    # 执行交易
    accounts = client.get_accounts()
    print(f"账户数量: {len(accounts)}")
    
    # 退出with语句时自动清理资源
```

---

## ⚠️ 错误处理

### 异常类型

客户端定义了以下异常类型：

```python
QMTTradeClientError     # 基础异常
├── QMTAuthenticationError  # 认证失败
└── QMTAPIError            # API调用失败
```

### 错误处理示例

```python
from qmt_trade_client import (
    QMTTradeClient,
    QMTAuthenticationError,
    QMTAPIError
)

client = QMTTradeClient("http://localhost:9091")

# 处理登录错误
try:
    client.login("admin", "wrong_password")
except QMTAuthenticationError as e:
    print(f"登录失败: {e}")

# 处理API调用错误
try:
    result = client.buy("000001", price=10.50, shares=500)
except QMTAPIError as e:
    print(f"买入失败: {e}")

# 处理参数错误
try:
    # 错误：同时提供 position_pct 和 shares
    result = client.buy(
        "000001",
        price=10.50,
        position_pct=0.1,
        shares=500
    )
except ValueError as e:
    print(f"参数错误: {e}")

# 处理所有异常
try:
    result = client.buy("000001", price=10.50, shares=500)
except Exception as e:
    print(f"交易失败: {e}")
```

### 常见错误及解决方案

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| "认证失败，请检查登录状态或API密钥" | 未登录或密钥错误 | 检查登录状态或API密钥配置 |
| "连接失败，请检查服务器地址" | 服务器未运行或地址错误 | 检查服务器是否启动，确认地址正确 |
| "必须提供 position_pct 或 shares 其中之一" | 交易参数缺失 | 提供 position_pct 或 shares 参数 |
| "position_pct 和 shares 不能同时提供" | 参数冲突 | 只提供一个交易参数 |
| "order_num 必须是 100 的倍数（股）" | 股数不符合要求 | 股票买入必须是100的倍数 |
| "order_num 必须是 10 的倍数（张）" | 张数不符合要求 | 可转债买入必须是10的倍数 |

---

## 🎓 最佳实践

### 1. 使用签名认证

```python
# ✅ 推荐：使用API签名认证
client = QMTTradeClient(
    "http://localhost:9091",
    client_id="my_strategy",
    secret_key="my_secret"
)

# ❌ 不推荐：频繁使用登录认证（会话可能过期）
client = QMTTradeClient("http://localhost:9091")
client.login("admin", "password")
```

### 2. 设置合理的超时时间

```python
# 对于网络较慢或交易量大的情况，增加超时时间
client = QMTTradeClient(
    "http://localhost:9091",
    timeout=60  # 60秒超时
)
```

### 3. 使用异常处理

```python
# ✅ 推荐：完善的异常处理
try:
    result = client.buy("000001", price=10.50, shares=500)
    print(f"买入成功: {result}")
except QMTAPIError as e:
    print(f"买入失败: {e}")
    # 记录日志、发送通知等

# ❌ 不推荐：不处理异常
result = client.buy("000001", price=10.50, shares=500)  # 可能崩溃
```

### 4. 合理使用请求频率

```python
import time

# ✅ 推荐：批量操作时添加延迟
for symbol in symbols:
    client.buy(symbol, price=10.50, shares=100)
    time.sleep(0.5)  # 避免请求过快

# ❌ 不推荐：短时间大量请求
for symbol in symbols:
    client.buy(symbol, price=10.50, shares=100)  # 可能被限流
```

### 5. 使用with语句管理资源

```python
# ✅ 推荐：使用with语句
with QMTTradeClient("http://localhost:9091") as client:
    client.login("admin", "password")
    result = client.buy("000001", price=10.50, shares=500)
    # 自动清理资源

# ❌ 不推荐：不清理资源
client = QMTTradeClient("http://localhost:9091")
client.login("admin", "password")
result = client.buy("000001", price=10.50, shares=500)
# 没有关闭会话
```

### 6. 参数验证

```python
# ✅ 推荐：使用参数验证
def safe_buy(client, symbol, price, shares):
    if shares % 100 != 0:
        print(f"错误：股数 {shares} 不是100的倍数")
        return None
    
    if price <= 0:
        print(f"错误：价格 {price} 无效")
        return None
    
    return client.buy(symbol, price=price, shares=shares)

# ❌ 不推荐：不验证参数
client.buy("000001", price=-10, shares=150)  # 参数错误
```

### 7. 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# ✅ 推荐：记录关键操作
try:
    logger.info(f"准备买入: 000001, 价格: 10.50, 股数: 500")
    result = client.buy("000001", price=10.50, shares=500)
    logger.info(f"买入成功: {result}")
except Exception as e:
    logger.error(f"买入失败: {e}", exc_info=True)
```

### 8. 配置文件管理

```python
import json

# ✅ 推荐：使用配置文件
with open('config.json', 'r') as f:
    config = json.load(f)

client = QMTTradeClient(
    base_url=config['base_url'],
    client_id=config['client_id'],
    secret_key=config['secret_key']
)

# ❌ 不推荐：硬编码敏感信息
client = QMTTradeClient(
    "http://localhost:9091",
    client_id="hardcoded_id",  # 不安全
    secret_key="hardcoded_key"  # 不安全
)
```

---

## 📞 技术支持

如有问题或建议，请联系：

- 📧 邮箱: support@qmt-trader.com
- 📱 技术支持热线: xxx-xxxx-xxxx
- 💬 内部工单系统

---

## 📄 更新日志

### v1.0.0 (2024-10)

**新功能**:
- ✅ 完整封装所有交易接口
- ✅ 支持双认证模式（会话/签名）
- ✅ 支持双交易模式（仓位比例/固定股数）
- ✅ 完善的异常处理机制
- ✅ 类型提示和文档字符串
- ✅ 便捷方法和工具函数

---

**文档版本**: v1.0.0  
**最后更新**: 2024年10月  
**版权所有**: QMT交易系统开发团队

