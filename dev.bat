@echo off
REM 货盘系统开发模式 - 前后端分离
cd /d "%~dp0"

echo === 启动后端 (FastAPI :8767) ===
start "huopan-backend" cmd /k "cd backend && set PYTHONPATH=. && python -m uvicorn app.main:app --host 0.0.0.0 --port 8767 --reload"

timeout /t 2 /nobreak >nul

echo === 启动前端 (Vite :5173, 热更新) ===
start "huopan-frontend" cmd /k "cd frontend && npx vite --host 0.0.0.0 --port 5173"

echo.
echo 后端: http://localhost:8767/docs
echo 前端: http://localhost:5173
echo.
pause
