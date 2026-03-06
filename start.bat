@echo off
chcp 65001 >nul
echo ========================================
echo   AI客服系统 - 一键启动
echo ========================================
echo.

echo [1/2] 启动后端服务...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'e:\Project\AICustomerService\AICustomService\Scripts\python.exe' -ArgumentList 'e:\Project\AICustomerService\backend\main.py' -WorkingDirectory 'e:\Project\AICustomerService\backend'"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm run dev' -WorkingDirectory 'e:\Project\AICustomerService\frontend'"

echo.
echo ========================================
echo   启动完成！
echo   后端: http://localhost:8000
echo   前端: http://localhost:5173
echo   API文档: http://localhost:8000/api/docs
echo ========================================
