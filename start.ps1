# 毕业设计市场平台 - 一键启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  毕业设计市场平台 - 启动中..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境
if (-not (Test-Path ".\AICustomService\Scripts\python.exe")) {
    Write-Host "错误: 找不到虚拟环境 AICustomService" -ForegroundColor Red
    Write-Host "请先运行 'python -m venv AICustomService' 创建虚拟环境" -ForegroundColor Yellow
    exit 1
}

# 启动后端
Write-Host "正在启动后端服务..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; ..\AICustomService\Scripts\python.exe main.py"

# 等待后端启动
Write-Host "等待后端服务启动 (5秒)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 启动前端
Write-Host "正在启动前端服务..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后端地址: http://localhost:8000" -ForegroundColor Yellow
Write-Host "API 文档: http://localhost:8000/api/docs" -ForegroundColor Yellow
Write-Host "前端地址: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "测试账户:" -ForegroundColor Cyan
Write-Host "  管理员: admin / admin123" -ForegroundColor White
Write-Host "  买家:   buyer1 / buyer123" -ForegroundColor White
Write-Host "  卖家:   seller1 / seller123" -ForegroundColor White
Write-Host ""
