<#
Chequeo de salud: servicios TallerWeb y TallerBot + GET a la web.
Log rotativo en %LOCALAPPDATA%\TallerAgenteIA\salud.log y toast local solo cuando el estado cambia.
Ping externo DESACTIVADO por defecto: solo se usa si se pasa -PingUrl.
Codigo de salida: 0 = todo bien, 1 = hay problemas.
#>
param(
    [string]$Url = 'http://127.0.0.1:8000/accounts/login/',
    [string]$PingUrl = '',
    [string]$ServiceLogDir = 'C:\ProgramData\TallerAgenteIA\logs'
)
$ErrorActionPreference = 'Continue'
$Base = Join-Path $env:LOCALAPPDATA 'TallerAgenteIA'
New-Item -ItemType Directory -Force -Path $Base | Out-Null
$LogFile = Join-Path $Base 'salud.log'
$StateFile = Join-Path $Base 'salud.estado'

function Write-Log([string]$msg) {
    if ((Test-Path $LogFile) -and ((Get-Item $LogFile).Length -gt 1MB)) {
        for ($i = 4; $i -ge 1; $i--) {
            if (Test-Path "$LogFile.$i") { Move-Item "$LogFile.$i" "$LogFile.$($i + 1)" -Force }
        }
        Move-Item $LogFile "$LogFile.1" -Force
        Remove-Item "$LogFile.5" -ErrorAction SilentlyContinue
    }
    Add-Content -Path $LogFile -Value ("{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg)
}

function Show-Toast([string]$title, [string]$text) {
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml("<toast><visual><binding template='ToastGeneric'><text>$title</text><text>$text</text></binding></visual></toast>")
        $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show([Windows.UI.Notifications.ToastNotification]::new($xml))
    } catch {
        Write-Log "No se pudo mostrar el toast: $($_.Exception.Message)"
    }
}

$problems = @()
foreach ($name in 'TallerWeb', 'TallerBot') {
    $svc = Get-Service $name -ErrorAction SilentlyContinue
    if (-not $svc) { $problems += "$name no esta instalado" }
    elseif ($svc.Status -ne 'Running') { $problems += "$name esta $($svc.Status)" }
}
try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10 -MaximumRedirection 0 -ErrorAction Stop
    if ($resp.StatusCode -ne 200) { $problems += "La web respondio HTTP $($resp.StatusCode)" }
} catch {
    $problems += "La web no responde ($($_.Exception.Message))"
}

# Limpieza de logs rotados de los servicios con mas de 30 dias (NSSM no los elimina).
if (Test-Path $ServiceLogDir) {
    Get-ChildItem $ServiceLogDir -File | Where-Object { $_.Name -match '-\d{8}T\d{6}' -and $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

$ok = ($problems.Count -eq 0)
$previous = if (Test-Path $StateFile) { (Get-Content $StateFile -Raw).Trim() } else { 'unknown' }
$state = if ($ok) { 'ok' } else { 'fail' }
if ($ok) { Write-Log 'OK servicios y web' } else { Write-Log ('PROBLEMA: ' + ($problems -join '; ')) }

if ($state -ne $previous) {
    if (-not $ok) { Show-Toast 'Taller: problema detectado' ($problems -join '; ') }
    elseif ($previous -eq 'fail') { Show-Toast 'Taller: recuperado' 'Web y bot funcionan de nuevo.' }
    Set-Content -Path $StateFile -Value $state
}

if ($ok -and $PingUrl) {
    try { Invoke-WebRequest -Uri $PingUrl -UseBasicParsing -TimeoutSec 10 | Out-Null } catch { Write-Log 'Ping externo fallo.' }
}
exit $(if ($ok) { 0 } else { 1 })
