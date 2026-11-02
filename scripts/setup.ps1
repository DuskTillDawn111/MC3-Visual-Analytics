$ErrorActionPreference = 'Stop'
$mc3Root = Split-Path -Parent $PSScriptRoot
Push-Location $mc3Root
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { py -3.11 -m venv .venv; if ($LASTEXITCODE -ne 0) { throw '需要安装 Python 3.11。' } }
    $mc3Requirements = if (Test-Path -LiteralPath 'backend\requirements.lock.txt') { 'backend\requirements.lock.txt' } else { 'backend\requirements.txt' }
    & '.\.venv\Scripts\python.exe' -m pip install -r $mc3Requirements
    if ($LASTEXITCODE -ne 0) { throw 'Python 依赖安装失败。' }
    & '.\.venv\Scripts\python.exe' scripts/prepare_data.py
    if ($LASTEXITCODE -ne 0) { throw '原始数据核验失败。' }
    Push-Location frontend
    try {
        npm ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw '前端依赖安装失败。' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw '前端构建失败。' }
    } finally { Pop-Location }
    & '.\.venv\Scripts\python.exe' -m pytest backend/tests -q
    if ($LASTEXITCODE -ne 0) { throw '后端测试失败。' }
    Write-Output '准备完成。运行 .\start.ps1 -OpenBrowser 打开工作台。'
} finally { Pop-Location }
