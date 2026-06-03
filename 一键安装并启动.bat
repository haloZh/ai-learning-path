@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   AI 个性化学习路径系统 - 一键安装并启动
echo   (北科大 MBA 人工智能课程作业 L-2)
echo ============================================================
echo.

REM ---------- 0. 检测 Python ----------
echo [1/6] 检测 Python ...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [X] 未检测到 Python。
    echo   请先安装 Python 3.11~3.13: https://www.python.org/downloads/
    echo   安装时务必勾选 "Add Python to PATH"，装完重新运行本脚本。
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "delims=" %%v in ('python --version') do echo   [OK] %%v

REM ---------- 0. 检测 Node ----------
echo [2/6] 检测 Node.js ...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [X] 未检测到 Node.js。
    echo   请先安装 Node.js 18+ (LTS): https://nodejs.org/
    echo   装完重新运行本脚本。
    start https://nodejs.org/
    pause
    exit /b 1
)
for /f "delims=" %%v in ('node --version') do echo   [OK] Node %%v

REM ---------- 1. 创建虚拟环境 ----------
echo [3/6] 准备 Python 虚拟环境 ...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo   [X] 创建虚拟环境失败。
        pause
        exit /b 1
    )
    echo   [OK] 已创建 .venv
) else (
    echo   [OK] .venv 已存在，跳过
)

REM ---------- 2. 安装后端依赖 ----------
echo [4/6] 安装后端依赖（首次约 5-10 分钟，请耐心等待）...
.venv\Scripts\python.exe -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo   [X] 后端依赖安装失败。请检查网络后重试。
    pause
    exit /b 1
)
echo   [OK] 后端依赖安装完成

REM ---------- 3. 安装并构建前端 ----------
echo [5/6] 安装并构建前端 ...
if exist "ymy\dist\index.html" (
    echo   [OK] ymy\dist 已存在，跳过前端构建
) else (
    pushd ymy
    if not exist "node_modules" (
        echo   - npm install ...
        call npm install
        if errorlevel 1 (
            echo   [X] 前端依赖安装失败。
            popd
            pause
            exit /b 1
        )
    )
    echo   - npm run build ...
    call npm run build
    if errorlevel 1 (
        echo   [X] 前端构建失败。
        popd
        pause
        exit /b 1
    )
    popd
    echo   [OK] 前端构建完成
)

REM ---------- 4. 启动 ----------
echo [6/6] 启动服务 ...
echo.
echo ============================================================
echo   安装完成！正在启动后端服务（端口 8000）
echo.
echo   ★ 首次启动需等待约 1-2 分钟加载 AI 向量模型
echo     当看到日志 "RAG 预热完成" 后即可使用
echo.
echo   ★ 浏览器打开:  http://localhost:8000
echo.
echo   ★ 关闭服务: 在本窗口按 Ctrl+C
echo ============================================================
echo.

REM 延迟 3 秒后自动打开浏览器（后端还在预热，但页面会先出来）
start "" cmd /c "timeout /t 8 >nul && start http://localhost:8000"

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info

pause
