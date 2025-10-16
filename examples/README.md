# QMT交易客户端示例

本目录包含各种使用场景的示例脚本，帮助您快速上手QMT交易客户端。

## 📋 示例列表

### 1. simple_trade.py - 简单交易示例

最基础的示例，演示如何进行基本的买卖操作。

**功能**:
- 查询账户资产
- 查询持仓信息
- 买入股票
- 卖出股票

**运行方式**:
```bash
python simple_trade.py
```

**适合场景**:
- 初次使用QMT客户端
- 学习基本的API调用
- 手动交易操作

---

### 2. monitor_positions.py - 持仓监控脚本

实时监控持仓，自动执行止盈止损策略。

**功能**:
- 实时监控所有持仓
- 自动止盈（盈利达到设定比例时卖出部分）
- 自动止损（亏损达到设定比例时全部卖出）
- 可自定义止盈止损参数

**运行方式**:
```bash
python monitor_positions.py
```

**可配置参数**:
```python
monitor = PositionMonitor(
    client=client,
    trader_index=0,
    stop_profit_ratio=10.0,   # 盈利10%时止盈
    stop_loss_ratio=-5.0,     # 亏损5%时止损
    stop_profit_sell_ratio=0.5,  # 止盈时卖出50%
    check_interval=60  # 每60秒检查一次
)
```

**适合场景**:
- 自动化止盈止损
- 风险控制
- 24小时监控（需保持运行）

---

### 3. batch_trading.py - 批量交易脚本

支持从列表或CSV文件批量下单，以及批量清仓。

**功能**:
- 从Python列表批量买入
- 从CSV文件批量买入
- 批量卖出所有持仓
- 创建示例CSV文件

**运行方式**:
```bash
python batch_trading.py
```

**CSV文件格式**:
```csv
symbol,price,shares
000001,10.50,500
000002,20.30,300
600000,15.20,400
```

**适合场景**:
- 批量建仓
- 批量清仓
- 策略调仓
- 定时买入

---

## 🚀 快速开始

### 1. 配置API密钥

在运行示例前，需要先配置您的API密钥。

编辑示例文件，修改以下部分：

```python
client = QMTTradeClient(
    base_url="http://localhost:9091",
    client_id="your_client_id",      # 修改为您的client_id
    secret_key="your_secret_key"     # 修改为您的secret_key
)
```

### 2. 安装依赖

```bash
pip install requests
```

### 3. 运行示例

```bash
cd examples
python simple_trade.py
```

---

## 📝 使用建议

### 开发测试

在开发和测试阶段，建议：

1. **使用模拟账户**：避免实际资金损失
2. **小额测试**：先用小金额测试功能
3. **添加日志**：记录所有交易操作
4. **异常处理**：完善的错误处理机制

### 生产环境

在生产环境中运行时，建议：

1. **配置文件管理**：不要硬编码API密钥
2. **日志记录**：记录所有操作和异常
3. **监控告警**：设置异常告警机制
4. **定时检查**：定期检查程序运行状态
5. **资金管理**：设置合理的仓位和风险控制

---

## 🔧 自定义开发

### 创建自己的交易策略

基于这些示例，您可以开发自己的交易策略：

```python
from qmt_trade_client import QMTTradeClient

class MyStrategy:
    def __init__(self, client):
        self.client = client
    
    def run(self):
        # 1. 获取行情数据
        # 2. 分析信号
        # 3. 执行交易
        pass

# 使用策略
client = QMTTradeClient("http://localhost:9091", ...)
strategy = MyStrategy(client)
strategy.run()
```

### 添加更多功能

您可以在这些示例基础上添加：

- 技术指标计算
- 多账户管理
- 风险控制模块
- 回测功能
- 实时行情接入
- 消息通知（邮件、钉钉、微信等）

---

## ⚠️ 注意事项

### 风险提示

1. **投资有风险**：使用本客户端进行的所有交易操作需自行承担风险
2. **策略验证**：在实盘使用前，请充分验证策略的有效性
3. **资金管理**：合理控制仓位，不要满仓操作
4. **异常处理**：程序异常可能导致交易失败，需有备用方案

### 技术注意

1. **网络稳定性**：确保网络连接稳定
2. **服务器状态**：确认QMT服务器正常运行
3. **请求频率**：避免短时间内大量请求
4. **数据准确性**：定期核对持仓和资金数据

---

## 📚 更多资源

- [QMT_CLIENT_使用手册.md](../QMT_CLIENT_使用手册.md) - 完整的API文档
- [qmt_trade_client.py](../qmt_trade_client.py) - 客户端源码
- [改进说明文档.md](../改进说明文档.md) - 系统功能说明

---

## 💬 获取帮助

如有问题或建议：

1. 查看使用手册
2. 检查示例代码
3. 联系技术支持

---

**祝您交易顺利！** 📈

