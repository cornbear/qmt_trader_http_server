#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT交易系统服务器启动脚本

支持多种启动方式：
1. Waitress 生产服务器（推荐）
2. Flask 开发服务器（开发调试）
3. 自定义配置启动

使用方式：
    python start_server.py                    # 使用默认配置
    python start_server.py --debug            # 开发模式
    python start_server.py --port 8080        # 指定端口
    python start_server.py --host 0.0.0.0     # 指定主机
    python start_server.py --threads 8        # 指定线程数
"""

import sys
import argparse
from app import app, log, config


def start_with_waitress(host, port, threads=4):
    """使用Waitress生产服务器启动"""
    try:
        from waitress import serve
        log.info("=" * 60)
        log.info("使用 Waitress 生产服务器")
        log.info("=" * 60)
        log.info(f"服务器地址: http://{host}:{port}")
        log.info(f"工作线程数: {threads}")
        log.info(f"访问地址: http://{host}:{port}")
        if host == '0.0.0.0':
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            log.info(f"内网访问: http://{local_ip}:{port}")
        log.info("=" * 60)
        log.info("服务器启动成功，按 Ctrl+C 停止")
        log.info("=" * 60)
        
        # 启动Waitress服务器
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            connection_limit=1000,  # 最大连接数
            channel_timeout=120,     # 通道超时
            cleanup_interval=30,     # 清理间隔
            url_scheme='http'
        )
    except ImportError:
        log.error("未安装 waitress！")
        log.error("请运行: pip install waitress")
        sys.exit(1)
    except Exception as e:
        log.error(f"启动失败: {str(e)}")
        sys.exit(1)


def start_with_flask(host, port, debug=True):
    """使用Flask开发服务器启动"""
    log.info("=" * 60)
    log.info("使用 Flask 开发服务器")
    log.info("=" * 60)
    log.info(f"服务器地址: http://{host}:{port}")
    log.info(f"调试模式: {'开启' if debug else '关闭'}")
    log.info(f"热重载: {'开启' if debug else '关闭'}")
    log.info("=" * 60)
    log.info("⚠️  Flask开发服务器仅用于开发调试")
    log.info("⚠️  生产环境请使用 Waitress 服务器")
    log.info("=" * 60)
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,
        use_reloader=debug
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='QMT交易系统服务器启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_server.py                      # 生产模式，使用配置文件设置
  python start_server.py --debug              # 开发模式，启用热重载
  python start_server.py --port 8080          # 使用8080端口
  python start_server.py --host 0.0.0.0       # 监听所有网卡
  python start_server.py --threads 8          # 使用8个工作线程
  python start_server.py --server flask       # 强制使用Flask服务器
        """
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help=f'监听主机地址 (默认: {config.flask.host})'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help=f'监听端口 (默认: {config.flask.port})'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='开启调试模式（使用Flask开发服务器）'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=4,
        help='Waitress服务器工作线程数 (默认: 4)'
    )
    
    parser.add_argument(
        '--server',
        type=str,
        choices=['waitress', 'flask'],
        default='waitress',
        help='指定服务器类型 (默认: waitress)'
    )
    
    args = parser.parse_args()
    
    # 确定主机和端口
    host = args.host or config.flask.host
    port = args.port or config.flask.port
    
    # 打印启动信息
    log.info("")
    log.info("*" * 60)
    log.info("*" + " " * 18 + "QMT交易系统" + " " * 18 + "*")
    log.info("*" * 60)
    log.info("")
    
    try:
        if args.debug:
            # 开发模式，使用Flask
            start_with_flask(host, port, debug=True)
        elif args.server == 'flask':
            # 强制使用Flask
            start_with_flask(host, port, debug=False)
        else:
            # 生产模式，使用Waitress
            start_with_waitress(host, port, threads=args.threads)
    except KeyboardInterrupt:
        log.info("")
        log.info("=" * 60)
        log.info("收到停止信号，正在关闭服务器...")
        log.info("=" * 60)
    except Exception as e:
        log.error(f"服务器异常: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        log.info("服务器已停止")


if __name__ == '__main__':
    main()


