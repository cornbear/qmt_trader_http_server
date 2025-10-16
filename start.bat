@echo off
REM QMT交易系统 - Windows启动脚本
REM 
REM 使用说明:
REM   双击运行: 使用默认配置启动（生产模式）
REM   命令行: start.bat [选项]
REM 
REM 选项:
REM   --debug    开发模式（支持热重载）
REM   --port     指定端口
REM   --host     指定主机地址

echo.
echo ========================================================
echo            QMT交易系统服务器启动脚本
echo ========================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖
echo [信息] 检查依赖...
python -c "import waitress" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未安装waitress，正在安装...
    pip install waitress
)

REM 启动服务器
echo [信息] 正在启动服务器...
echo.

if "%1"=="" (
    REM 默认启动（生产模式）
    python start_server.py
) else (
    REM 传递所有参数
    python start_server.py %*
)

echo.
echo ========================================================
echo                 服务器已停止
echo ========================================================
pause


