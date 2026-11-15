# Demo del taller como servidor en la notebook

> **Aviso (2026-11-15):** esta guía supone una notebook Windows y no se usó. La notebook real es Linux y
> la demo ya corre allí con systemd, cron y Tailscale: ver
> [servidor notebook Linux](servidor-notebook-linux.md). NSSM, los scripts `.ps1` y las rutas `C:\…` de
> esta guía no aplican a esa máquina. Siguen siendo válidos `scripts/backup.py`, las variables de `.env`
> y las explicaciones de HTTPS.

Guía para dejar la demo estable en la notebook usada como servidor: web y bot arrancan solos y se reinician si fallan. Es una etapa **local de demo**; el despliegue en VPS para clientes sigue siendo una etapa futura separada.

> Los scripts de `scripts/` **no se ejecutan solos**. Cada paso con efectos en el sistema (servicios, tareas programadas, energía, túneles) lo ejecutas tú, cuando decidas.

## Arquitectura

| Pieza | Cómo corre | Dónde escribe |
| --- | --- | --- |
| Web | Servicio `TallerWeb`: `waitress` en `127.0.0.1:8000` con `DJANGO_DEBUG=false`; estáticos con whitenoise | `C:\ProgramData\TallerAgenteIA\logs\web.log` |
| Bot | Servicio `TallerBot`: `manage.py runbot` (long polling, sin túnel) | `...\logs\bot.log` |
| Salud | Tarea `TallerSalud`, cada 5 min | `%LOCALAPPDATA%\TallerAgenteIA\salud.log` |
| Backup | Tarea `TallerBackup`, diaria 03:30 | `%LOCALAPPDATA%\TallerAgenteIA\backup.log` y `TALLER_BACKUP_DIR` |

`runserver` queda solo para desarrollo. `db.sqlite3` y `media/` siguen dentro del repositorio y no se modifican por esta configuración.

## Cambios de código y dependencias

- `requirements.txt`: se agregan `waitress` (servidor WSGI apto para Windows), `whitenoise` (estáticos) y `cryptography` (cifrado de backups).
- `taller/settings.py`: `STATIC_ROOT=staticfiles/`, `WhiteNoiseMiddleware` tras `SecurityMiddleware`, almacenamiento con manifiesto, y variables de entorno `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_HTTPS` y `DJANGO_HSTS_SECONDS`. Con los valores por defecto el comportamiento es el de antes (solo `127.0.0.1` y `localhost`, cookies sin `Secure`). Durante `manage.py test` se usa el almacenamiento de estáticos simple, porque el manifiesto exige `collectstatic`.
- `staticfiles/` ya está en `.gitignore`.

Tras actualizar el código: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, luego `manage.py collectstatic --noinput` y `Restart-Service TallerWeb, TallerBot`.

## 1. Probar waitress a mano

```powershell
.\scripts\run_web.ps1            # primer plano; Ctrl+C para detener
```

Detén antes cualquier `runserver` en el puerto 8000.

## 2. Servicios de Windows (NSSM)

1. Instala NSSM con winget, que valida el hash del instalador contra el manifiesto: `winget install NSSM.NSSM` (o descarga desde <https://nssm.cc> y compara el SHA256 que obtengas por una segunda vía).
2. En PowerShell **como administrador**:

```powershell
.\scripts\install_services.ps1 -Start
```

El script muestra el SHA256 de `nssm.exe` (acepta `-ExpectedSha256` para exigirlo), ejecuta `collectstatic`, pide **tu contraseña de Windows** (no se guarda ni se muestra; el servicio necesita una cuenta con contraseña) y configura:

- Cuenta: la tuya, con permisos de escritura solo sobre la carpeta de logs; el repo lo lees con tus propios permisos.
- Inicio automático retrasado; reinicio ante fallo con espera de 5 s (`AppExit Default Restart`).
- Logs en `C:\ProgramData\TallerAgenteIA\logs`, rotados a 10 MB o 1 día. `salud.ps1` borra los rotados de más de 30 días.
- `DJANGO_SECRET_KEY`, el token del bot y las demás claves **no** se pasan a NSSM: `settings.py` las lee de `.env`, así que no aparecen en la configuración del servicio ni en logs.

Si cambias tu contraseña de Windows, vuelve a ejecutar `install_services.ps1`. Para quitar los servicios: `.\scripts\uninstall_services.ps1`.

Comandos habituales: `Get-Service TallerWeb, TallerBot`, `Restart-Service TallerBot`, `Get-Content C:\ProgramData\TallerAgenteIA\logs\bot.log -Tail 50`.

## 3. Acceso remoto

Ahora **no hay túnel** y no se abre ningún puerto del router: la web solo escucha en `127.0.0.1`. El bot no necesita túnel.

Si luego hace falta mostrar la demo, la opción recomendada es **Tailscale** (acceso solo desde tus dispositivos o invitados de la tailnet, con HTTPS). No se instala sin tu autorización. Esquema:

1. Instalar Tailscale en la notebook y habilitar HTTPS en el panel de administración de la tailnet.
2. Publicar el puerto local: `tailscale serve --bg 8000` (entrega HTTPS en `https://<equipo>.<tailnet>.ts.net`). No usar `funnel`, que lo expone a Internet.
3. En `.env`:

```
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,<equipo>.<tailnet>.ts.net
DJANGO_CSRF_TRUSTED_ORIGINS=https://<equipo>.<tailnet>.ts.net
DJANGO_HTTPS=true
```

4. `Restart-Service TallerWeb`.

`DJANGO_HTTPS=true` activa cookies de sesión y CSRF `Secure`, confía en `X-Forwarded-Proto` del proxy local y `Referrer-Policy`. HSTS queda desactivado (`DJANGO_HSTS_SECONDS=0`) por ser difícil de revertir; actívalo con un valor corto solo si lo necesitas. No se fuerza `SECURE_SSL_REDIRECT` porque el acceso local `http://127.0.0.1:8000` debe seguir funcionando. Por eso `manage.py check --deploy` informa `W004` (HSTS) y `W008` (redirect SSL): son intencionales en este esquema.

Cloudflare Tunnel sería otra opción (requiere dominio); tampoco se instala sin autorización.

## 4. Energía y autologon

Este repositorio no duplica la guía de energía de KietoAgenteIA. En `..\KietoAgenteIA\docs\instalacion-pc.md` solo se indica que el PC debe permanecer encendido con la suspensión desactivada por su propietario; **no define comandos de energía ni autologon**, por lo que no se ha podido enlazar a ellos.

Para esta notebook se incluye `scripts/configurar_energia.ps1`, idempotente: lee los valores actuales con `powercfg /query` y se omite si ya están aplicados. Ajusta: sin suspensión ni hibernación con cable, y sin acción al cerrar la tapa (cable y batería).

```powershell
.\scripts\configurar_energia.ps1 -WhatIf   # muestra qué cambiaría
.\scripts\configurar_energia.ps1
```

Con la tapa cerrada cuida la ventilación y el cargador. El autologon no se configura aquí; sin él, tras un reinicio los servicios arrancan, pero las tareas de salud y backup (que usan tu sesión) esperan a que inicies sesión.

## 5. Backups

`scripts/backup.py` copia `db.sqlite3` con la **API de backup de SQLite** (conexión de solo lectura, verificada con `PRAGMA integrity_check`) y añade `media/` en un zip. Nunca modifica el origen.

- Destino: `TALLER_BACKUP_DIR` en `.env`, en la subcarpeta propia `TallerAgenteIA-backups`. Debe estar fuera del repo y de la notebook (disco USB, NAS o carpeta de una nube).
- Cifrado (Fernet) activo por defecto, con `TALLER_BACKUP_KEY_FILE`. La clave **no puede estar dentro del destino** (el script lo rechaza); guárdala por separado, p. ej. en un gestor de contraseñas y una copia impresa. Sin la clave los backups cifrados no se recuperan. Los archivos quedan como `taller-AAAAMMDD-HHMMSS.zip.enc`.
- Sin cifrar (`--no-encrypt`) solo para discos locales; el script lo rechaza si la ruta parece una nube (OneDrive, Google Drive, Dropbox, iCloud, MEGA, Box).
- Retención: 14 copias; solo se borran archivos propios del formato `taller-*.zip[.enc]`.
- El cifrado y la lectura son en memoria: pensado para el tamaño de la demo.

Preparación (una vez):

```powershell
.\.venv\Scripts\python.exe scripts\backup.py --generate-key D:\claves\taller.key   # no imprime la clave
# En .env:  TALLER_BACKUP_DIR=<ruta externa>   TALLER_BACKUP_KEY_FILE=D:\claves\taller.key
.\.venv\Scripts\python.exe scripts\backup.py                                        # backup manual de prueba
```

Programar (diario 03:30 y salud cada 5 min, como tareas de tu usuario con la sesión iniciada):

```powershell
.\scripts\instalar_tareas.ps1          # -Quitar para eliminarlas
```

Probar una restauración, siempre en una carpeta nueva (se rechaza el repo y `media/`):

```powershell
.\.venv\Scripts\python.exe scripts\backup.py --restore <archivo.zip.enc> --to C:\temp\restore-prueba
```

Para restaurar de verdad: detén los servicios, haz una copia de seguridad de lo actual, copia `db.sqlite3` y `media/` desde la carpeta restaurada y reinicia.

## 6. Salud

`scripts/salud.ps1` comprueba que `TallerWeb` y `TallerBot` estén en ejecución y hace un GET a `/accounts/login/`. Escribe un log rotativo (1 MB × 5) en `%LOCALAPPDATA%\TallerAgenteIA\salud.log` y muestra un toast local solo cuando el estado cambia (problema o recuperación). El **ping externo está desactivado**: solo se usa si pasas `-PingUrl`, p. ej. `.\scripts\instalar_tareas.ps1 -PingUrl <url>`.

## Verificación recomendada

```powershell
$env:DJANGO_SECRET_KEY = 'clave-temporal-solo-para-pruebas'
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
```

Y `check --deploy` con `DJANGO_DEBUG=false` y `DJANGO_HTTPS=true`: solo deben aparecer `W004` y `W008`.

## Solución de problemas

- El servicio no arranca: revisa `web.log` / `bot.log` y que `.env` tenga `DJANGO_SECRET_KEY`.
- Error 400 al acceder por otro nombre: falta ese host en `DJANGO_ALLOWED_HOSTS`.
- Error CSRF tras activar HTTPS: falta el origen en `DJANGO_CSRF_TRUSTED_ORIGINS` (incluye `https://`).
- Puerto 8000 ocupado: hay un `runserver` o waitress manual; deténlo.
- `ValueError: Missing staticfiles manifest entry`: ejecuta `collectstatic --noinput`.

`OPENAI_ENABLED` permanece en `False`.
