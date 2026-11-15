<#
Instala (o actualiza) los servicios TallerWeb y TallerBot con NSSM.
Ejecutar en PowerShell como administrador. NO se ejecuta automaticamente.

  .\scripts\install_services.ps1 [-NssmPath C:\ruta\nssm.exe] [-ExpectedSha256 <hash>] [-Start]

- Cuenta del servicio: la del usuario actual (se pide la contrasena; no se guarda ni se muestra).
- Logs fuera del repositorio, con rotacion de NSSM.
- DJANGO_SECRET_KEY y demas secretos NO se pasan a NSSM: settings.py los lee de .env.
#>
#Requires -RunAsAdministrator
param(
    [string]$NssmPath,
    [string]$ExpectedSha256,
    [string]$LogDir = 'C:\ProgramData\TallerAgenteIA\logs',
    [string]$ServiceUser = "$env:USERDOMAIN\$env:USERNAME",
    [int]$Port = 8000,
    [switch]$Start
)
$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Repo '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) { throw "No existe $Python. Crea el entorno virtual primero (ver README)." }
if (-not (Test-Path (Join-Path $Repo '.env'))) { throw 'Falta .env en el repositorio.' }

if (-not $NssmPath) {
    $cmd = Get-Command nssm.exe -ErrorAction SilentlyContinue
    if (-not $cmd) { throw 'No se encontro nssm.exe. Instalalo con winget (ver docs/servidor-notebook.md) o usa -NssmPath.' }
    $NssmPath = $cmd.Source
}
$hash = (Get-FileHash $NssmPath -Algorithm SHA256).Hash
Write-Host "NSSM: $NssmPath"
Write-Host "SHA256: $hash"
if ($ExpectedSha256 -and ($hash -ne $ExpectedSha256.Trim().ToUpper())) { throw 'El hash de nssm.exe no coincide con el esperado. Abortando.' }

# Archivos estaticos: el manifiesto de whitenoise debe existir antes de servir con DEBUG=false.
Push-Location $Repo
try {
    $env:DJANGO_DEBUG = 'false'
    & $Python manage.py collectstatic --noinput | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'collectstatic fallo.' }
} finally { Pop-Location }

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
& icacls $LogDir /grant "${ServiceUser}:(OI)(CI)M" | Out-Null

$secure = Read-Host "Contrasena de $ServiceUser (para el servicio)" -AsSecureString
$plain = [System.Net.NetworkCredential]::new('', $secure).Password

$services = @(
    @{ Name = 'TallerWeb'; Display = 'Taller - Web (waitress)'; Params = "-m waitress --listen=127.0.0.1:$Port taller.wsgi:application"; Log = 'web' },
    @{ Name = 'TallerBot'; Display = 'Taller - Bot de Telegram'; Params = 'manage.py runbot'; Log = 'bot' }
)

function Invoke-Nssm { & $NssmPath @args | Out-Null; if ($LASTEXITCODE -ne 0) { throw "nssm $($args -join ' ') fallo." } }

foreach ($s in $services) {
    $n = $s.Name
    if (-not (Get-Service $n -ErrorAction SilentlyContinue)) {
        Invoke-Nssm install $n $Python $s.Params
    } else {
        Invoke-Nssm set $n Application $Python
        Invoke-Nssm set $n AppParameters $s.Params
    }
    Invoke-Nssm set $n DisplayName $s.Display
    Invoke-Nssm set $n AppDirectory $Repo
    Invoke-Nssm set $n AppEnvironmentExtra 'DJANGO_DEBUG=false' 'PYTHONUNBUFFERED=1' 'PYTHONUTF8=1'
    Invoke-Nssm set $n Start SERVICE_DELAYED_AUTO_START
    Invoke-Nssm set $n ObjectName $ServiceUser $plain
    # Reinicio automatico ante fallo.
    Invoke-Nssm set $n AppExit Default Restart
    Invoke-Nssm set $n AppRestartDelay 5000
    Invoke-Nssm set $n AppThrottle 15000
    # Logs rotados (10 MB o 1 dia); salud.ps1 elimina los rotados con mas de 30 dias.
    $log = Join-Path $LogDir "$($s.Log).log"
    Invoke-Nssm set $n AppStdout $log
    Invoke-Nssm set $n AppStderr $log
    Invoke-Nssm set $n AppRotateFiles 1
    Invoke-Nssm set $n AppRotateOnline 1
    Invoke-Nssm set $n AppRotateBytes 10485760
    Invoke-Nssm set $n AppRotateSeconds 86400
    Write-Host "Servicio $n configurado."
}
$plain = $null

if ($Start) {
    foreach ($s in $services) { Start-Service $s.Name; Write-Host "Iniciado $($s.Name)." }
} else {
    Write-Host 'Servicios instalados sin iniciar. Detene antes cualquier runserver/runbot manual y luego: Start-Service TallerWeb, TallerBot'
}
