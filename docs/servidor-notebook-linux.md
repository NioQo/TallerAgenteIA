# Demo del taller en la notebook servidor (Linux)

Estado (2026-11-14): **instalada y verificada en la notebook**. Es la instalación activa de la demo.
La guía [servidor-notebook.md](servidor-notebook.md) describe una instalación Windows (NSSM, scripts
`.ps1`, tareas programadas) que **no se usó**: la notebook es Linux y se configuró a mano con systemd y
cron.

## Máquina
| Dato | Valor |
|---|---|
| Equipo | `nio-HP-15-Notebook-PC`, Linux Mint 22.3 (base Ubuntu 24.04), usuario `nio` |
| Acceso | SSH `nio@192.168.0.235` (LAN) o Tailscale `nio-hp-15-notebook-pc` |
| Energía | Tapa cerrada sin suspender: `HandleLidSwitch=ignore` y `HandleLidSwitchExternalPower=ignore` en `/etc/systemd/logind.conf` |
| Otros servicios | KietoAgenteIA (Docker, 127.0.0.1:3008, ngrok), n8n (Docker, 127.0.0.1:5678), Uptime Kuma (Docker, 127.0.0.1:3001) |

## Qué corre
| Pieza | Cómo | Notas |
|---|---|---|
| Web | systemd `taller-web.service`: `.venv/bin/python -m waitress --listen=127.0.0.1:8000 taller.wsgi:application` | `User=nio`, `DJANGO_DEBUG=false`, `Restart=always` |
| Bot | systemd `taller-bot.service`: `.venv/bin/python manage.py runbot` | Long polling: no necesita túnel ni puerto abierto |
| Acceso web | `tailscale serve --bg 8000` → `https://nio-hp-15-notebook-pc.tail4d1b4b.ts.net/` | Solo dentro de la tailnet; no es público |
| Backup | cron diario 03:30: `scripts/backup.py` | Log en `/home/nio/backup.log` |

Ambos servicios tienen `WorkingDirectory=/home/nio/TallerAgenteIA` y `WantedBy=multi-user.target`.
Arrancan solos al reiniciar (verificado con `sudo reboot` el 2026-11-14).

## Archivos en la notebook
- Código y datos: `/home/nio/TallerAgenteIA`, copiado del PC con `scp`. `.venv` recreado en Linux
  (el de Windows no sirve). `db.sqlite3` y `media/` de la notebook son los datos vigentes.
- `.env` (permisos 600). Además de las variables de `.env.example`, contiene:
  - `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,nio-hp-15-notebook-pc.tail4d1b4b.ts.net`
  - `DJANGO_CSRF_TRUSTED_ORIGINS=https://nio-hp-15-notebook-pc.tail4d1b4b.ts.net`
  - `DJANGO_HTTPS=true`
  - `TALLER_BACKUP_DIR=/home/nio/backups` y `TALLER_BACKUP_KEY_FILE=/home/nio/claves/taller.key`
  - Cada variable en su propia línea: dos líneas pegadas en una rompieron el backup y `ALLOWED_HOSTS`.
- Backups: `/home/nio/backups/TallerAgenteIA-backups/taller-AAAAMMDD-HHMMSS.zip.enc` (retención 14).
- Clave de backup: `/home/nio/claves/taller.key` (Fernet, 44 bytes, permisos 600). Fuera del destino de
  backups, como exige el script.

## Comandos habituales (en la notebook)
```bash
systemctl status taller-web taller-bot --no-pager
sudo systemctl restart taller-web taller-bot
journalctl -u taller-web -n 30 --no-pager
journalctl -u taller-bot -n 30 --no-pager | grep -i conflict   # vacío = sin bot duplicado
curl -I http://127.0.0.1:8000/accounts/login/                  # 200 esperado
tailscale serve status
crontab -l
tail -n 20 ~/backup.log && ls -la ~/backups/TallerAgenteIA-backups
```
Restauración de prueba, siempre en carpeta nueva:
`.venv/bin/python scripts/backup.py --restore <archivo>.zip.enc --to ~/restore-prueba`.

## Actualizar el código
1. Copiar los cambios desde el PC con `scp` (desde PowerShell del PC, no desde la sesión SSH). **No copiar
   `db.sqlite3` ni `media/` del PC**: pisarían los datos vigentes de la notebook. Tampoco `.venv`.
2. En la notebook, en `~/TallerAgenteIA`:
   ```bash
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python manage.py migrate
   .venv/bin/python manage.py collectstatic --noinput
   sudo systemctl restart taller-web taller-bot
   ```
   Antes de una migración, hacer un backup manual: `.venv/bin/python scripts/backup.py`.
3. Comprobar `curl -I` del login, la URL de Tailscale y `/start` en el bot.

## Reglas
- No arrancar el bot ni `runserver` en el PC: Telegram da `Conflict` si dos procesos usan el mismo token,
  y los datos del PC ya no se actualizan.
- Usar la web siempre por la URL de Tailscale. El dispositivo que la abre necesita Tailscale conectado con
  la misma cuenta; el PC no tiene que estar encendido.
- Para mostrarla a terceros: invitarlos a la tailnet (compartir solo esta máquina) en vez de hacerla
  pública. Tailscale Funnel la expondría a Internet.
- En terminales SSH, pegar los comandos de a uno: el pegado con corchetes (`[200~`) rompió comandos.

## Incidencias
- `tailscale serve --bg 8000` quitó un Funnel público que había en el puerto 443. La ruta `/webhook` de n8n
  (→ 127.0.0.1:5678) quedó solo para la tailnet. Si un flujo de n8n con disparador webhook o un servicio
  externo deja de recibir llamadas, esta es la causa: hay que publicarlo en otro puerto de Funnel sin
  exponer la web del taller.

## Pendiente
- Backup fuera de la notebook: hoy los backups están en el mismo disco. Conectar un USB o copiarlos al PC.
- Confirmar que la clave `taller.key` está guardada fuera de la notebook (gestor de contraseñas o USB).
  Sin ella los backups no se recuperan.
- Revisar `~/backup.log` para confirmar que el cron de las 03:30 corre.
