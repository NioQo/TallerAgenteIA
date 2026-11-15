<#
Inicia la web con waitress (produccion, sin runserver) en primer plano.
Uso manual / pruebas: .\scripts\run_web.ps1 [-Port 8000]
DJANGO_SECRET_KEY se lee desde .env por settings.py; este script no lo imprime.
#>
param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
Set-Location $Repo
$env:DJANGO_DEBUG = 'false'
& $Python manage.py collectstatic --noinput | Out-Null
& $Python -m waitress --listen="127.0.0.1:$Port" taller.wsgi:application
