@echo off
REM 货盘系统启动脚本
cd /d "%~dp0"

echo === 检查前端是否已构建 ===
if not exist "frontend\dist\index.html" (
    echo 前端未构建, 正在构建...
    cd frontend
    call npm run build
    cd ..
    echo 前端构建完成
)

echo === 启动后端 (FastAPI :8767, 含前端SPA) ===
start "huopan-server" cmd /k "cd backend && set PYTHONPATH=. && python -m uvicorn app.main:app --host 0.0.0.0 --port 8767"

timeout /t 3 /nobreak >nul

echo.
echo 货盘系统已启动: http://localhost:8767
echo API文档: http://localhost:8767/docs
echo.
echo 如需开发模式(前后端分离), 运行 dev.bat
echo.
pause
