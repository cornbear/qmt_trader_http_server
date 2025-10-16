#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量交易示例

从CSV文件或列表批量下单
"""

import sys
import os
import time
import csv
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmt_trade_client import QMTTradeClient, QMTAPIError


def batch_buy_from_list(
    client: QMTTradeClient,
    buy_list: List[Dict],
    delay: float = 0.5
):
    """
    从列表批量买入
    
    Args:
        client: QMT客户端
        buy_list: 买入列表，每项包含 symbol, price, shares
        delay: 每次下单间隔（秒）
    """
    
    print("=" * 60)
    print("批量买入开始")
    print("=" * 60)
    print(f"待买入数量: {len(buy_list)}只\n")
    
    success_count = 0
    failed_count = 0
    results = []
    
    for i, item in enumerate(buy_list, 1):
        symbol = item['symbol']
        price = item['price']
        shares = item['shares']
        
        print(f"[{i}/{len(buy_list)}] 买入 {symbol}")
        print(f"   价格: ¥{price:.2f} | 数量: {shares}股 | 金额: ¥{price * shares:,.2f}")
        
        try:
            result = client.buy(
                symbol=symbol,
                price=price,
                shares=shares,
                strategy_name="批量交易"
            )
            
            print(f"   ✓ 委托成功")
            success_count += 1
            results.append({
                'symbol': symbol,
                'status': 'success',
                'result': result
            })
            
        except Exception as e:
            print(f"   ✗ 委托失败: {e}")
            failed_count += 1
            results.append({
                'symbol': symbol,
                'status': 'failed',
                'error': str(e)
            })
        
        # 延迟，避免请求过快
        if i < len(buy_list):
            time.sleep(delay)
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("批量买入完成")
    print("=" * 60)
    print(f"成功: {success_count}只")
    print(f"失败: {failed_count}只")
    print(f"总计: {len(buy_list)}只")
    
    return results


def batch_buy_from_csv(
    client: QMTTradeClient,
    csv_file: str,
    delay: float = 0.5
):
    """
    从CSV文件批量买入
    
    CSV格式:
    symbol,price,shares
    000001,10.50,500
    000002,20.30,300
    
    Args:
        client: QMT客户端
        csv_file: CSV文件路径
        delay: 每次下单间隔（秒）
    """
    
    print(f"从CSV文件读取: {csv_file}\n")
    
    buy_list = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                buy_list.append({
                    'symbol': row['symbol'],
                    'price': float(row['price']),
                    'shares': int(row['shares'])
                })
    except FileNotFoundError:
        print(f"✗ 文件不存在: {csv_file}")
        return
    except Exception as e:
        print(f"✗ 读取CSV文件失败: {e}")
        return
    
    if not buy_list:
        print("✗ CSV文件为空")
        return
    
    # 执行批量买入
    results = batch_buy_from_list(client, buy_list, delay)
    
    return results


def batch_sell_positions(
    client: QMTTradeClient,
    trader_index: int = 0,
    sell_ratio: float = 1.0,
    price_discount: float = 0.01,
    delay: float = 0.5
):
    """
    批量卖出持仓
    
    Args:
        client: QMT客户端
        trader_index: 交易器索引
        sell_ratio: 卖出比例 (0-1)，1表示全部卖出
        price_discount: 价格折扣，如0.01表示按现价的99%委托
        delay: 每次下单间隔（秒）
    """
    
    print("=" * 60)
    print("批量卖出持仓")
    print("=" * 60)
    
    try:
        positions = client.get_positions(trader_index)
    except QMTAPIError as e:
        print(f"✗ 查询持仓失败: {e}")
        return
    
    if not positions:
        print("当前无持仓")
        return
    
    print(f"当前持仓: {len(positions)}只")
    print(f"卖出比例: {sell_ratio * 100:.0f}%")
    print(f"价格折扣: {price_discount * 100:.1f}%\n")
    
    confirm = input("是否确认批量卖出？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    success_count = 0
    failed_count = 0
    
    for i, pos in enumerate(positions, 1):
        symbol = pos['symbol']
        name = pos['name']
        can_use_volume = pos['can_use_volume']
        current_price = pos['current_price']
        
        # 计算卖出股数
        sell_volume = int(can_use_volume * sell_ratio)
        sell_volume = (sell_volume // 100) * 100  # 向下取整到100的倍数
        
        if sell_volume < 100:
            print(f"[{i}/{len(positions)}] {symbol} {name}")
            print(f"   ⚠️  可卖出股数不足100股，跳过")
            continue
        
        # 计算卖出价格
        sell_price = current_price * (1 - price_discount)
        
        print(f"[{i}/{len(positions)}] 卖出 {symbol} {name}")
        print(f"   现价: ¥{current_price:.2f} | 委托价: ¥{sell_price:.2f}")
        print(f"   卖出: {sell_volume}股 | 金额: ¥{sell_price * sell_volume:,.2f}")
        
        try:
            result = client.sell(
                symbol=symbol.split('.')[0],  # 去掉市场后缀
                price=sell_price,
                shares=sell_volume,
                strategy_name="批量清仓"
            )
            
            print(f"   ✓ 委托成功")
            success_count += 1
            
        except Exception as e:
            print(f"   ✗ 委托失败: {e}")
            failed_count += 1
        
        # 延迟
        if i < len(positions):
            time.sleep(delay)
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("批量卖出完成")
    print("=" * 60)
    print(f"成功: {success_count}只")
    print(f"失败: {failed_count}只")
    print(f"总计: {len(positions)}只")


def create_sample_csv(filename: str = "buy_list.csv"):
    """创建示例CSV文件"""
    
    sample_data = [
        {'symbol': '000001', 'price': 10.50, 'shares': 500},
        {'symbol': '000002', 'price': 20.30, 'shares': 300},
        {'symbol': '600000', 'price': 15.20, 'shares': 400},
    ]
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'price', 'shares'])
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"✓ 已创建示例CSV文件: {filename}")


def main():
    """主函数"""
    
    print("=" * 60)
    print("批量交易示例")
    print("=" * 60)
    
    # 创建客户端（设置默认 trader_index）
    client = QMTTradeClient(
        base_url="http://localhost:9091",
        client_id="batch_trader",
        secret_key="your_secret_key",
        trader_index=0  # ✨ 设置默认交易器索引
    )
    
    while True:
        print("\n请选择操作：")
        print("1. 从列表批量买入")
        print("2. 从CSV文件批量买入")
        print("3. 批量卖出持仓")
        print("4. 创建示例CSV文件")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == '1':
            # 从列表批量买入
            buy_list = [
                {'symbol': '000001', 'price': 10.50, 'shares': 500},
                {'symbol': '000002', 'price': 20.30, 'shares': 300},
                {'symbol': '600000', 'price': 15.20, 'shares': 400},
            ]
            
            batch_buy_from_list(client, buy_list)
        
        elif choice == '2':
            # 从CSV文件批量买入
            csv_file = input("请输入CSV文件路径 (默认: buy_list.csv): ").strip()
            if not csv_file:
                csv_file = "buy_list.csv"
            
            batch_buy_from_csv(client, csv_file)
        
        elif choice == '3':
            # 批量卖出持仓
            sell_ratio = input("请输入卖出比例 (0-1, 默认1全部卖出): ").strip()
            sell_ratio = float(sell_ratio) if sell_ratio else 1.0
            
            batch_sell_positions(
                client,
                trader_index=0,
                sell_ratio=sell_ratio,
                price_discount=0.01  # 按现价的99%委托
            )
        
        elif choice == '4':
            # 创建示例CSV文件
            filename = input("请输入文件名 (默认: buy_list.csv): ").strip()
            if not filename:
                filename = "buy_list.csv"
            
            create_sample_csv(filename)
        
        elif choice == '0':
            print("\n再见！")
            break
        
        else:
            print("\n✗ 无效的选项，请重新输入")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n✗ 程序异常: {e}")

