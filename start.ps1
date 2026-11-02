param([switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
$mc3Root = $PSScriptRoot
$mc3Python = Join-Path $mc3Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $mc3Python)) { throw '请先运行 scripts\setup.ps1 创建 Python 环境。' }
if (-not (Test-Path -LiteralPath (Join-Path $mc3Root 'frontend\dist\index.html'))) { throw '请先在 frontend 运行 npm ci 和 npm run build。' }
$mc3Url = 'http://127.0.0.1:8000'
$mc3ExpectedHash = (Get-FileHash -LiteralPath (Join-Path $mc3Root 'data\raw\MC3_release.zip') -Algorithm SHA256).Hash.ToLowerInvariant()
try { $mc3Existing = Invoke-RestMethod -Uri "$mc3Url/api/health" -TimeoutSec 2 } catch { $mc3Existing = $null }
if ($mc3Existing) {
    if ($mc3Existing.source_sha256 -ne $mc3ExpectedHash) { throw '8000 端口运行其他数据版本，请先检查该服务。' }
    Write-Output "系统已运行：$mc3Url"
    if ($OpenBrowser) { Start-Process $mc3Url }
    return
}
if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { throw '8000 端口被其他程序占用。' }
$mc3Work = Join-Path $mc3Root 'work'
New-Item -ItemType Directory -Path $mc3Work -Force | Out-Null
$mc3Process = Start-Process -FilePath $mc3Python -ArgumentList @('-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $mc3Root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $mc3Work 'server.log') -RedirectStandardError (Join-Path $mc3Work 'server-error.log') -PassThru
$mc3Ready = $false
for ($mc3Attempt = 0; $mc3Attempt -lt 40; $mc3Attempt++) {
    Start-Sleep -Milliseconds 500
    try { $mc3Health = Invoke-RestMethod -Uri "$mc3Url/api/health" -TimeoutSec 2; if ($mc3Health.source_sha256 -eq $mc3ExpectedHash) { $mc3Ready = $true; break } } catch { }
    if ($mc3Process.HasExited) { break }
}
if (-not $mc3Ready) { throw "服务启动失败，请检查 $mc3Work\server-error.log。" }
$mc3Listener = Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object -First 1
$mc3Owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($mc3Listener.OwningProcess)"
@{ root=$mc3Root; launcher_pid=$mc3Process.Id; listener_pid=$mc3Owner.ProcessId; listener_created_ticks=$mc3Owner.CreationDate.ToUniversalTime().Ticks; source_sha256=$mc3ExpectedHash } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $mc3Work 'server.json') -Encoding utf8
Write-Output "系统已启动：$mc3Url（$($mc3Health.messages) 条官方通信已加载）"
if ($OpenBrowser) { Start-Process $mc3Url }
