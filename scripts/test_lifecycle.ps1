$ErrorActionPreference = 'Stop'
$mc3Root = Split-Path -Parent $PSScriptRoot
& (Join-Path $mc3Root 'start.ps1')
$mc3First = Get-Content -LiteralPath (Join-Path $mc3Root 'work\server.json') -Raw | ConvertFrom-Json
& (Join-Path $mc3Root 'start.ps1')
$mc3Second = Get-Content -LiteralPath (Join-Path $mc3Root 'work\server.json') -Raw | ConvertFrom-Json
if ($mc3First.listener_pid -ne $mc3Second.listener_pid) { throw '重复启动创建了新的服务。' }
$mc3Process = Get-Process -Id $mc3Second.listener_pid
if ($mc3Process.MainWindowHandle -ne 0) { throw '后台服务出现了可见窗口。' }
& (Join-Path $mc3Root 'stop.ps1')
if (Test-Path -LiteralPath (Join-Path $mc3Root 'work\server.json')) { throw '停止后服务记录仍存在。' }
for ($mc3Attempt=0; $mc3Attempt -lt 20; $mc3Attempt++) {
    if (-not (Get-Process -Id $mc3Second.listener_pid -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Milliseconds 100
}
if (Get-Process -Id $mc3Second.listener_pid -ErrorAction SilentlyContinue) { throw '停止后原服务进程仍运行。' }
& (Join-Path $mc3Root 'start.ps1')
$mc3Health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health'
if (-not $mc3Health.data_loaded -or $mc3Health.messages -ne 584) { throw '重启后真实数据不可用。' }
if ((Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing).StatusCode -ne 200) { throw '生产页面不可访问。' }
Write-Output 'PASS: 后台不可见、重复启动幂等、停止及重启、生产页面与真实数据。'
