#!/bin/bash
# QMT交易系统 - Linux/Mac启动脚本
#
# 使用说明:
#   ./start.sh              使用默认配置启动（生产模式）
#   ./start.sh --debug      开发模式（支持热重载）
#   ./start.sh --port 8080  指定端口
#   ./start.sh --host 0.0.0.0  监听所有网卡
#
# 首次使用需要添加执行权限:
#   chmod +x start.sh

echo ""
echo "========================================================"
echo "          QMT交易系统服务器启动脚本"
echo "========================================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 显示Python版本
echo "[信息] Python版本: $(python3 --version)"

# 检查依赖
echo "[信息] 检查依赖..."
if ! python3 -c "import waitress" &> /dev/null; then
    echo "[警告] 未安装waitress，正在安装..."
    pip3 install waitress
    if [ $? -ne 0 ]; then
        echo "[错误] 安装waitress失败"
        exit 1
    fi
fi

# 启动服务器
echo "[信息] 正在启动服务器..."
echo ""

if [ $# -eq 0 ]; then
    # 默认启动（生产模式）
    python3 start_server.py
else
    # 传递所有参数
    python3 start_server.py "$@"
fi

echo ""
echo "========================================================"
echo "               服务器已停止"
echo "========================================================"


