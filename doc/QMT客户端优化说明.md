# QMT交易客户端优化说明

**版本**: v1.1.0  
**日期**: 2024年10月16日  
**优化**: trader_index 参数优化

---

## 🎯 优化内容

### 问题

在之前的版本中，每次调用方法时都需要传递 `trader_index` 参数，导致代码冗余：

```python
# ❌ 之前的方式 - 每次都要传 trader_index
client = QMTTradeClient("http://localhost:9091", ...)

portfolio = client.get_portfolio(trader_index=0)
positions = client.get_positions(trader_index=0)
summary = client.get_account_summary(trader_index=0)
```

### 解决方案

现在可以在初始化时设置一次 `trader_index`，后续调用自动使用默认值：

```python
# ✅ 优化后的方式 - 只设置一次
client = QMTTradeClient(
    "http://localhost:9091",
    client_id="your_client_id",
    secret_key="your_secret_key",
    trader_index=0  # ✨ 只需设置一次
)

# 后续调用无需传递 trader_index
portfolio = client.get_portfolio()
positions = client.get_positions()
summary = client.get_account_summary()
```

---

## 📋 修改的方法

以下方法现在支持使用默认 `trader_index`：

| 方法 | 修改前 | 修改后 |
|-----|-------|-------|
| `__init__()` | 无 trader_index 参数 | ✅ 新增 trader_index 参数 |
| `get_portfolio()` | trader_index: int = 0 | ✅ trader_index: Optional[int] = None |
| `get_positions()` | trader_index: int = 0 | ✅ trader_index: Optional[int] = None |
| `get_account_summary()` | trader_index: int = 0 | ✅ trader_index: Optional[int] = None |
| `get_position_by_symbol()` | trader_index: int = 0 | ✅ trader_index: Optional[int] = None |
| `has_position()` | trader_index: int = 0 | ✅ trader_index: Optional[int] = None |
| `sell_all()` | trader_index: Optional[int] = None | ✅ 文档更新 |

---

## 🔧 向后兼容性

本次优化**完全向后兼容**，原有代码无需修改：

```python
# ✅ 旧代码仍然可以正常工作
client = QMTTradeClient("http://localhost:9091", ...)
portfolio = client.get_portfolio(trader_index=0)  # 仍然有效

# ✅ 也可以使用新方式
client = QMTTradeClient("http://localhost:9091", ..., trader_index=0)
portfolio = client.get_portfolio()  # 使用默认值
```

---

## 💡 使用示例

### 示例1: 基础使用

```python
from qmt_trade_client import QMTTradeClient

# 创建客户端时设置默认 trader_index
client = QMTTradeClient(
    base_url="http://localhost:9091",
    client_id="my_strategy",
    secret_key="my_secret",
    trader_index=0  # 设置默认为账户0
)

# 所有查询和交易都使用默认 trader_index
portfolio = client.get_portfolio()
positions = client.get_positions()
client.buy("000001", price=10.50, shares=500)
client.sell("000001", price=10.60, shares=500)
```

### 示例2: 覆盖默认值

```python
# 如果需要临时使用其他账户，仍然可以传递参数
client = QMTTradeClient(
    base_url="http://localhost:9091",
    trader_index=0  # 默认账户0
)

# 使用默认账户0
portfolio_0 = client.get_portfolio()

# 临时查询账户1
portfolio_1 = client.get_portfolio(trader_index=1)

# 回到默认账户0
positions_0 = client.get_positions()
```

### 示例3: 多账户管理

```python
# 为不同账户创建不同的客户端实例
client_0 = QMTTradeClient(
    base_url="http://localhost:9091",
    client_id="account_0",
    secret_key="secret_0",
    trader_index=0
)

client_1 = QMTTradeClient(
    base_url="http://localhost:9091",
    client_id="account_1",
    secret_key="secret_1",
    trader_index=1
)

# 每个客户端使用各自的默认账户
portfolio_0 = client_0.get_portfolio()
portfolio_1 = client_1.get_portfolio()
```

---

## 📊 代码对比

### 之前的代码

```python
client = QMTTradeClient(
    "http://localhost:9091",
    client_id="outer",
    secret_key="cornbear"
)

# 每次都要传 trader_index - 重复且冗余
portfolio = client.get_portfolio(trader_index=0)
positions = client.get_positions(trader_index=0)

if client.has_position("000001.SZ", trader_index=0):
    pos = client.get_position_by_symbol("000001.SZ", trader_index=0)
    
summary = client.get_account_summary(trader_index=0)
```

### 优化后的代码

```python
client = QMTTradeClient(
    "http://localhost:9091",
    client_id="outer",
    secret_key="cornbear",
    trader_index=0  # 只设置一次
)

# 简洁清晰 - 无需重复传递参数
portfolio = client.get_portfolio()
positions = client.get_positions()

if client.has_position("000001.SZ"):
    pos = client.get_position_by_symbol("000001.SZ")
    
summary = client.get_account_summary()
```

**代码减少**: 约 30% 的参数传递

---

## ✨ 优势

1. **代码更简洁**
   - 减少重复参数传递
   - 提高代码可读性

2. **使用更便捷**
   - 一次设置，处处生效
   - 降低出错概率

3. **完全兼容**
   - 不影响现有代码
   - 可以随时覆盖默认值

4. **设计合理**
   - 符合"Don't Repeat Yourself"原则
   - 保持API的灵活性

---

## 📝 更新的文件

- ✅ `qmt_trade_client.py` - 核心客户端
- ✅ `examples/simple_trade.py` - 简单交易示例
- ✅ `examples/monitor_positions.py` - 持仓监控示例
- ✅ `examples/batch_trading.py` - 批量交易示例

---

## 🔄 迁移指南

### 无需迁移

如果您满意当前的代码，无需做任何修改。

### 推荐迁移

如果想使用新特性，只需两步：

1. **初始化时添加 trader_index 参数**

```python
# 添加这一行
client = QMTTradeClient(..., trader_index=0)
```

2. **移除方法调用中的 trader_index 参数**

```python
# 之前
portfolio = client.get_portfolio(trader_index=0)

# 之后
portfolio = client.get_portfolio()
```

---

## 📞 技术支持

如有问题，请联系技术支持团队。

---

**优化时间**: 2024年10月16日  
**优化人**: AI Assistant  
**版本**: v1.1.0  
**状态**: ✅ 已完成

