<#
Detiene y elimina los servicios TallerWeb y TallerBot (administrador). No borra logs ni datos.
#>
#Requires -RunAsAdministrator
param([string]$NssmPath)
$ErrorActionPreference = 'Stop'
if (-not $NssmPath) {
    $cmd = Get-Command nssm.exe -ErrorAction SilentlyContinue
    if (-not $cmd) { throw 'No se encontro nssm.exe; usa -NssmPath.' }
    $NssmPath = $cmd.Source
}
foreach ($n in 'TallerBot', 'TallerWeb') {
    if (Get-Service $n -ErrorAction SilentlyContinue) {
        & $NssmPath stop $n | Out-Null
        & $NssmPath remove $n confirm | Out-Null
        Write-Host "Servicio $n eliminado."
    } else {
        Write-Host "Servicio $n no existe; se omite."
    }
}
