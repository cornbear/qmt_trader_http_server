#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单交易示例

演示如何使用QMT交易客户端进行基本的买卖操作
"""

import sys
import os

# 添加父目录到路径，以便导入qmt_trade_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmt_trade_client import QMTTradeClient, QMTAuthenticationError, QMTAPIError


def main():
    """简单交易示例"""
    
    print("=" * 60)
    print("QMT交易客户端 - 简单交易示例")
    print("=" * 60)
    
    # 创建客户端（请替换为您的配置）
    client = QMTTradeClient(
        base_url="http://localhost:9091",
        client_id="your_client_id",
        secret_key="your_secret_key"
    )
    
    # 1. 查询账户资产
    print("\n【1. 查询账户资产】")
    print("-" * 60)
    try:
        portfolio = client.get_portfolio(0)
        print(f"总资产:     ¥{portfolio['total_asset']:>15,.2f}")
        print(f"可用金额:   ¥{portfolio['cash']:>15,.2f}")
        print(f"冻结金额:   ¥{portfolio['frozen_cash']:>15,.2f}")
        print(f"持仓市值:   ¥{portfolio['market_value']:>15,.2f}")
    except QMTAPIError as e:
        print(f"✗ 查询失败: {e}")
        return
    
    # 2. 查询持仓
    print("\n【2. 查询持仓信息】")
    print("-" * 60)
    try:
        positions = client.get_positions(0)
        if positions:
            for pos in positions:
                print(f"\n{pos['symbol']} {pos['name']}")
                print(f"  持仓数量: {pos['volume']}股")
                print(f"  成本价:   ¥{pos['avg_price']:.2f}")
                print(f"  现价:     ¥{pos['current_price']:.2f}")
                print(f"  市值:     ¥{pos['market_value']:,.2f}")
                profit_sign = "+" if pos['profit'] >= 0 else ""
                print(f"  盈亏:     {profit_sign}¥{pos['profit']:,.2f} ({profit_sign}{pos['profit_ratio']:.2f}%)")
        else:
            print("暂无持仓")
    except QMTAPIError as e:
        print(f"✗ 查询失败: {e}")
    
    # 3. 买入示例
    print("\n【3. 买入示例】")
    print("-" * 60)
    
    # 示例：买入平安银行500股
    symbol = "000001"
    buy_price = 10.50
    buy_shares = 500
    
    print(f"准备买入: {symbol}")
    print(f"  价格: ¥{buy_price}")
    print(f"  数量: {buy_shares}股")
    print(f"  预计金额: ¥{buy_price * buy_shares:,.2f}")
    
    confirm = input("\n是否确认买入？(y/n): ")
    if confirm.lower() == 'y':
        try:
            result = client.buy(
                symbol=symbol,
                price=buy_price,
                shares=buy_shares,
                strategy_name="简单交易示例"
            )
            print(f"✓ 买入成功!")
            print(f"  结果: {result}")
        except (ValueError, QMTAPIError) as e:
            print(f"✗ 买入失败: {e}")
    else:
        print("已取消买入")
    
    # 4. 卖出示例
    print("\n【4. 卖出示例】")
    print("-" * 60)
    
    # 检查是否持有该股票
    if client.has_position(f"{symbol}.SZ", trader_index=0):
        pos = client.get_position_by_symbol(f"{symbol}.SZ", trader_index=0)
        
        sell_price = 10.60
        sell_shares = 500
        
        # 确保不超过可用股数
        if sell_shares > pos['can_use_volume']:
            sell_shares = pos['can_use_volume']
        
        print(f"准备卖出: {symbol}")
        print(f"  可用股数: {pos['can_use_volume']}股")
        print(f"  卖出价格: ¥{sell_price}")
        print(f"  卖出数量: {sell_shares}股")
        print(f"  预计金额: ¥{sell_price * sell_shares:,.2f}")
        
        confirm = input("\n是否确认卖出？(y/n): ")
        if confirm.lower() == 'y':
            try:
                result = client.sell(
                    symbol=symbol,
                    price=sell_price,
                    shares=sell_shares,
                    strategy_name="简单交易示例"
                )
                print(f"✓ 卖出成功!")
                print(f"  结果: {result}")
            except (ValueError, QMTAPIError) as e:
                print(f"✗ 卖出失败: {e}")
        else:
            print("已取消卖出")
    else:
        print(f"未持有 {symbol}，无法卖出")
    
    print("\n" + "=" * 60)
    print("示例结束")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n✗ 程序异常: {e}")

