<#
Registra dos tareas programadas del usuario actual (NO se ejecuta automaticamente):
  - TallerBackup: diario a las 03:30 (scripts\backup.py, 14 copias, TALLER_BACKUP_DIR).
  - TallerSalud:  cada 5 minutos (scripts\salud.ps1).
Se ejecutan con la sesion iniciada (necesario para el toast y para unidades de red/USB del usuario);
StartWhenAvailable repite el backup si el equipo estaba apagado a las 03:30.
Uso: .\scripts\instalar_tareas.ps1 [-Quitar]
#>
param([switch]$Quitar, [string]$PingUrl = '')
$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Repo '.venv\Scripts\python.exe'

if ($Quitar) {
    foreach ($n in 'TallerBackup', 'TallerSalud') {
        Unregister-ScheduledTask -TaskName $n -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Tarea $n quitada (si existia)."
    }
    return
}

$user = "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

$backup = New-ScheduledTaskAction -Execute $Python -Argument "`"$Repo\scripts\backup.py`" --keep 14" -WorkingDirectory $Repo
Register-ScheduledTask -TaskName 'TallerBackup' -Action $backup -Trigger (New-ScheduledTaskTrigger -Daily -At '03:30') `
    -Principal $principal -Settings $settings -Force | Out-Null

$saludArgs = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Repo\scripts\salud.ps1`""
if ($PingUrl) { $saludArgs += " -PingUrl `"$PingUrl`"" }
$salud = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $saludArgs -WorkingDirectory $Repo
Register-ScheduledTask -TaskName 'TallerSalud' -Action $salud `
    -Trigger (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)) `
    -Principal $principal -Settings $settings -Force | Out-Null
Write-Host 'Tareas TallerBackup (03:30) y TallerSalud (cada 5 min) registradas.'
