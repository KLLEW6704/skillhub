param(
  [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'

Set-Location $root

if (-not (Test-Path $python)) {
  Write-Host '正在创建后端运行环境…' -ForegroundColor Cyan
  py -3.11 -m venv (Join-Path $backend '.venv')
}

if (-not $SkipInstall) {
  Write-Host '正在检查后端依赖…' -ForegroundColor Cyan
  Set-Location $backend
  & $python -m pip install -e '.[dev]'
  if (-not (Test-Path (Join-Path $backend '.env'))) {
    Copy-Item (Join-Path $backend '.env.example') (Join-Path $backend '.env')
  }
  Write-Host '正在生成演示账号和模拟数据…' -ForegroundColor Cyan
  & $python -m app.seed
  Set-Location $root

  if (-not (Test-Path (Join-Path $frontend 'node_modules'))) {
    Write-Host '正在安装前端依赖…' -ForegroundColor Cyan
    Set-Location $frontend
    npm install
    Set-Location $root
  }
}

Write-Host '正在启动 SkillHub…' -ForegroundColor Green
Start-Process powershell.exe -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', "Set-Location '$backend'; & '$python' -m uvicorn app.main:app --reload --port 8000")
Start-Process powershell.exe -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', "Set-Location '$frontend'; npm run dev")

Write-Host ''
Write-Host '前端地址：http://127.0.0.1:5173' -ForegroundColor Yellow
Write-Host '后端地址：http://127.0.0.1:8000' -ForegroundColor Yellow
Write-Host '首页会显示所有演示账号，统一密码：Student123!' -ForegroundColor Yellow
