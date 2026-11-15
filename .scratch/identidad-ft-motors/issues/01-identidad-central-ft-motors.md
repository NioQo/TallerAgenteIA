# 01: Identidad central de FT MOTORS

**Objetivo / Qué construir:** definir la identidad real de FT MOTORS en un único lugar y aplicarla a la web y a los PDF nuevos, incluyendo un logotipo de texto reemplazable.

**Status:** done — implementado en el repo (commit `7aef6a2`) y verificado en el PC (ver [ticket 04](04-verificacion-y-regresiones.md)). Despliegue en la notebook: ver comentarios.

**Blocked by:** None (can start immediately).

**Referencia:** [Especificación](../spec.md), secciones "Identidad del taller" y "Compatibilidad funcional".

## Alcance

- Nombre, lema ("Tu vehículo en manos expertas"), teléfono (+54 9 11 5429 6017), dirección (Av. Dardo Rocha 1891, Ruta 25, Pilar, Buenos Aires) y logotipo de texto definidos en un solo lugar.
- Web: título, encabezado, pantalla de acceso y pie usan esa fuente en lugar de "Taller Norte / Servicio automotor".
- PDF nuevos: el encabezado usa nombre, dirección y teléfono reales en lugar de "TALLER DEMO", "Av. del Taller 123" y "(011) 4000-0000".
- El logotipo puede sustituirse por un archivo real cambiándolo en un solo lugar.

## Criterios de aceptación

- [x] Cambiar un dato de identidad se hace en un solo lugar y se refleja en web y PDF. (`tallerweb/identity.py`, expuesto como `workshop` a las plantillas y usado por `pdf.py`.)
- [x] Ninguna pantalla ni PDF nuevo muestra "Taller Norte" ni "TALLER DEMO".
- [x] Las pruebas que buscaban "Taller Norte" verifican "FT MOTORS" y los datos de contacto.
- [x] Prueba nueva: el PDF nuevo contiene nombre, dirección y teléfono reales.
- [x] Los PDF ya emitidos en `media/presupuestos/` no se modifican. (Solo pruebas automatizadas.)
- [x] No se agregan datos fiscales, email, horarios ni redes.

## Comments

- **2026-11-15:** criterios cumplidos en el repo del PC. La instalación activa (notebook Linux) seguía mostrando "Taller Norte" hasta aplicar la actualización; el despliegue requiere `scp` y comandos en la notebook según `docs/servidor-notebook-linux.md`.
- **2026-11-15, despliegue en la notebook:** código de `HEAD` copiado con `scp` (sin `db.sqlite3`, `media/`, `.env` ni `.venv`). Antes: backup `taller-20261115-031821.zip.enc` y copia del código previo en `~/taller-codigo-antes-20261115-031822.tgz`. Sin migraciones pendientes; `collectstatic` y reinicio de `taller-web` y `taller-bot`. Resultado: ambos servicios activos, login HTTP 200, bot sin `Conflict`. La URL de Tailscale muestra "FT MOTORS", el lema, la dirección y el teléfono en el pie, y el botón "Modo oscuro".

## Límites

No cambia el contenido del PDF más allá del encabezado. No incluye mensajes de Telegram ni `/admin/`.
