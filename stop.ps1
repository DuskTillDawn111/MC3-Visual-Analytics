$ErrorActionPreference = 'Stop'
$mc3Manifest = Join-Path $PSScriptRoot 'work\server.json'
if (-not (Test-Path -LiteralPath $mc3Manifest)) { Write-Output '没有由 start.ps1 创建的服务记录。'; return }
$mc3State = Get-Content -LiteralPath $mc3Manifest -Raw | ConvertFrom-Json
if ($mc3State.root -ne $PSScriptRoot) { throw '服务记录的工作区不匹配，停止操作。' }
$mc3Owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($mc3State.listener_pid)" -ErrorAction SilentlyContinue
if ($mc3Owner) {
    $mc3CreatedTicks = if ($mc3State.listener_created_ticks) { [long]$mc3State.listener_created_ticks } else { ([datetime]$mc3State.listener_created).ToUniversalTime().Ticks }
    if ($mc3Owner.CommandLine -notlike '*uvicorn backend.app.main:app*' -or $mc3Owner.CreationDate.ToUniversalTime().Ticks -ne $mc3CreatedTicks) { throw '进程身份发生变化，停止操作。' }
    Stop-Process -Id $mc3Owner.ProcessId
}
if ($mc3State.launcher_pid -ne $mc3State.listener_pid) {
    $mc3Launcher = Get-CimInstance Win32_Process -Filter "ProcessId = $($mc3State.launcher_pid)" -ErrorAction SilentlyContinue
    if ($mc3Launcher -and $mc3Launcher.CommandLine -like '*uvicorn backend.app.main:app*') { Stop-Process -Id $mc3Launcher.ProcessId }
}
Remove-Item -LiteralPath $mc3Manifest
Write-Output 'MC3 本地服务已停止。'
