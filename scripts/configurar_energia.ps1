<#
Plan de energia para servidor: sin suspension ni hibernacion con cable, tapa cerrada sin accion.
Idempotente: lee los valores actuales (powercfg /query) y se omite si ya estan aplicados.
Uso: .\scripts\configurar_energia.ps1 [-WhatIf]   (NO se ejecuta automaticamente)
Autologon no se configura aqui.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param()
$ErrorActionPreference = 'Stop'

# Cada ajuste: subgrupo, configuracion, y valores deseados para CA y CC ($null = no tocar).
$settings = @(
    @{ Sub = 'SUB_SLEEP';   Name = 'STANDBYIDLE';   Label = 'Suspender tras inactividad'; AC = 0; DC = $null },
    @{ Sub = 'SUB_SLEEP';   Name = 'HIBERNATEIDLE'; Label = 'Hibernar tras inactividad';  AC = 0; DC = $null },
    @{ Sub = 'SUB_BUTTONS'; Name = 'LIDACTION';     Label = 'Accion al cerrar la tapa';   AC = 0; DC = 0 }
)

# Salida independiente del idioma: los dos ultimos valores hexadecimales son CA y CC.
function Get-PowerIndex($sub, $name) {
    $out = (powercfg /query SCHEME_CURRENT $sub $name) -join "`n"
    $hex = [regex]::Matches($out, '0x[0-9a-fA-F]{8}') | ForEach-Object { [Convert]::ToInt32($_.Value.Substring(2), 16) }
    if ($hex.Count -lt 2) { throw "No se pudo leer $sub/$name con powercfg." }
    return @{ AC = $hex[$hex.Count - 2]; DC = $hex[$hex.Count - 1] }
}

$pending = @()
foreach ($s in $settings) {
    $current = Get-PowerIndex $s.Sub $s.Name
    foreach ($kind in 'AC', 'DC') {
        if ($null -ne $s[$kind] -and $current[$kind] -ne $s[$kind]) {
            $pending += @{ Setting = $s; Kind = $kind; From = $current[$kind] }
        }
    }
}

if ($pending.Count -eq 0) {
    Write-Host 'Configuracion de energia ya aplicada; se omite.'
    return
}

foreach ($p in $pending) {
    $s = $p.Setting
    $verb = if ($p.Kind -eq 'AC') { '/setacvalueindex' } else { '/setdcvalueindex' }
    if ($PSCmdlet.ShouldProcess("$($s.Label) ($($p.Kind))", "cambiar de $($p.From) a $($s[$p.Kind])")) {
        powercfg $verb SCHEME_CURRENT $s.Sub $s.Name $s[$p.Kind]
        if ($LASTEXITCODE -ne 0) { throw "powercfg fallo en $($s.Name)." }
    }
}
if ($PSCmdlet.ShouldProcess('esquema activo', 'reaplicar')) {
    powercfg /setactive SCHEME_CURRENT
}
Write-Host "Aplicados $($pending.Count) cambio(s) de energia."
