## Instalación activa: notebook servidor (desde 2026-11-14)

- La demo activa (web y bot) ya NO corre en el PC. Corre en la notebook Linux `nio-HP-15-Notebook-PC`
  (Linux Mint 22.3), en `/home/nio/TallerAgenteIA`, con systemd (`taller-web`, `taller-bot`), backup por
  cron y acceso por Tailscale. Detalle, comandos y pendientes: `docs/servidor-notebook-linux.md`.
- Los datos vigentes (`db.sqlite3`, `media/`) están en la notebook. Los del PC quedaron desactualizados:
  no copiarlos a la notebook ni tratarlos como actuales.
- No arrancar el bot ni `runserver` en el PC: con el mismo token, Telegram da `Conflict`.
- El repo del PC sigue siendo la fuente del código. Los cambios se llevan a la notebook con `scp` y se
  aplican allí (`pip install`, `migrate`, `collectstatic`, `systemctl restart`); cada actualización en la
  notebook requiere autorización explícita del usuario.
- `docs/servidor-notebook.md` y los scripts `.ps1` de `scripts/` son de Windows y no aplican a la notebook.
- En la notebook conviven servicios ajenos al taller: KietoAgenteIA, n8n, Uptime Kuma y otras rutas de
  `tailscale serve`. No modificarlos.

## Agent skills

### Issue tracker

Specifications and implementation tickets are stored as local Markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Domain docs

This is a single-context project: read the root `GLOSSARY.md` and relevant decisions in `docs/adr/`. See `docs/agents/domain.md`.
