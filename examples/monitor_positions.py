#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓监控脚本

实时监控持仓，自动止盈止损
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmt_trade_client import QMTTradeClient, QMTAPIError


class PositionMonitor:
    """持仓监控器"""
    
    def __init__(
        self,
        client: QMTTradeClient,
        trader_index: int = 0,
        stop_profit_ratio: float = 10.0,  # 止盈比例（%）
        stop_loss_ratio: float = -5.0,    # 止损比例（%）
        stop_profit_sell_ratio: float = 0.5,  # 止盈时卖出比例
        check_interval: int = 60  # 检查间隔（秒）
    ):
        self.client = client
        self.trader_index = trader_index
        self.stop_profit_ratio = stop_profit_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.stop_profit_sell_ratio = stop_profit_sell_ratio
        self.check_interval = check_interval
        self.triggered_symbols = set()  # 记录已触发的股票，避免重复操作
    
    def check_positions(self):
        """检查持仓并执行止盈止损"""
        
        try:
            positions = self.client.get_positions(self.trader_index)
            
            if not positions:
                print("当前无持仓")
                return
            
            print(f"\n当前持仓数量: {len(positions)}只\n")
            
            for pos in positions:
                self._check_single_position(pos)
                
        except QMTAPIError as e:
            print(f"✗ 查询持仓失败: {e}")
    
    def _check_single_position(self, pos: dict):
        """检查单个持仓"""
        
        symbol = pos['symbol']
        name = pos['name']
        volume = pos['volume']
        can_use_volume = pos['can_use_volume']
        cost_price = pos['avg_price']
        current_price = pos['current_price']
        profit = pos['profit']
        profit_ratio = pos['profit_ratio']
        
        # 显示持仓信息
        profit_sign = "+" if profit >= 0 else ""
        status_color = "🔴" if profit < 0 else "🟢" if profit > 0 else "⚪"
        
        print(f"{status_color} {symbol} {name}")
        print(f"   持仓: {volume}股 (可用: {can_use_volume}股)")
        print(f"   成本价: ¥{cost_price:.2f} | 现价: ¥{current_price:.2f}")
        print(f"   盈亏: {profit_sign}¥{profit:,.2f} ({profit_sign}{profit_ratio:.2f}%)")
        
        # 检查是否已经触发过（避免重复操作）
        if symbol in self.triggered_symbols:
            print(f"   ⚠️  已触发过操作，跳过")
            return
        
        # 止盈检查
        if profit_ratio >= self.stop_profit_ratio:
            print(f"   🎯 触发止盈条件 (>= {self.stop_profit_ratio}%)")
            self._execute_stop_profit(pos)
        
        # 止损检查
        elif profit_ratio <= self.stop_loss_ratio:
            print(f"   🛑 触发止损条件 (<= {self.stop_loss_ratio}%)")
            self._execute_stop_loss(pos)
        
        else:
            print(f"   ✓ 正常持仓")
    
    def _execute_stop_profit(self, pos: dict):
        """执行止盈"""
        
        symbol = pos['symbol']
        current_price = pos['current_price']
        can_use_volume = pos['can_use_volume']
        
        # 计算卖出股数（按比例，且必须是100的倍数）
        sell_volume = int(can_use_volume * self.stop_profit_sell_ratio)
        sell_volume = (sell_volume // 100) * 100
        
        if sell_volume < 100:
            print(f"   ⚠️  可卖出股数不足100股，跳过")
            return
        
        # 使用略低于现价的价格委托，提高成交概率
        sell_price = current_price * 0.99
        
        print(f"   → 准备卖出 {sell_volume}股 @ ¥{sell_price:.2f}")
        
        try:
            result = self.client.sell(
                symbol=symbol.split('.')[0],  # 去掉市场后缀
                price=sell_price,
                shares=sell_volume,
                strategy_name="自动止盈"
            )
            print(f"   ✓ 止盈委托已提交")
            self.triggered_symbols.add(symbol)
        except Exception as e:
            print(f"   ✗ 止盈委托失败: {e}")
    
    def _execute_stop_loss(self, pos: dict):
        """执行止损"""
        
        symbol = pos['symbol']
        current_price = pos['current_price']
        
        # 使用略低于现价的价格委托，快速止损
        sell_price = current_price * 0.98
        
        print(f"   → 准备清仓 @ ¥{sell_price:.2f}")
        
        try:
            result = self.client.sell_all(
                symbol=symbol.split('.')[0],  # 去掉市场后缀
                price=sell_price
            )
            print(f"   ✓ 止损委托已提交")
            self.triggered_symbols.add(symbol)
        except Exception as e:
            print(f"   ✗ 止损委托失败: {e}")
    
    def run(self):
        """运行监控"""
        
        print("=" * 60)
        print("持仓监控脚本已启动")
        print("=" * 60)
        print(f"止盈条件: 盈利 >= {self.stop_profit_ratio}% (卖出{int(self.stop_profit_sell_ratio * 100)}%)")
        print(f"止损条件: 亏损 <= {self.stop_loss_ratio}% (全部卖出)")
        print(f"检查间隔: {self.check_interval}秒")
        print("按 Ctrl+C 停止监控")
        print("=" * 60)
        
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                self.check_positions()
                
                print(f"\n等待 {self.check_interval} 秒后进行下次检查...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n\n监控已停止")
                break
            except Exception as e:
                print(f"\n✗ 监控异常: {e}")
                print(f"等待 {self.check_interval} 秒后重试...")
                time.sleep(self.check_interval)


def main():
    """主函数"""
    
    # 创建客户端
    client = QMTTradeClient(
        base_url="http://localhost:9091",
        client_id="position_monitor",
        secret_key="your_secret_key"
    )
    
    # 创建监控器
    monitor = PositionMonitor(
        client=client,
        trader_index=0,
        stop_profit_ratio=10.0,   # 盈利10%时止盈
        stop_loss_ratio=-5.0,     # 亏损5%时止损
        stop_profit_sell_ratio=0.5,  # 止盈时卖出50%
        check_interval=60  # 每60秒检查一次
    )
    
    # 运行监控
    monitor.run()


if __name__ == "__main__":
    main()

