@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   AI 个性化学习路径系统 - 启动
echo ============================================================
echo.

REM 检查是否已安装
if not exist ".venv\Scripts\python.exe" (
    echo   [X] 尚未安装环境，请先运行 "一键安装并启动.bat"
    pause
    exit /b 1
)
if not exist "ymy\dist\index.html" (
    echo   [!] 前端未构建，请先运行 "一键安装并启动.bat"
    pause
    exit /b 1
)

echo   ★ 首次启动需等待约 1-2 分钟加载 AI 向量模型
echo     看到日志 "RAG 预热完成" 后即可使用
echo   ★ 浏览器打开:  http://localhost:8000
echo   ★ 关闭服务: 按 Ctrl+C
echo.

start "" cmd /c "timeout /t 8 >nul && start http://localhost:8000"

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info

pause
