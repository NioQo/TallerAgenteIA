# 06: Corregir mediante nuevas versiones

**Objetivo / Qué construir:** permitir al mecánico corregir desde Telegram un presupuesto pendiente, revisar los cambios y generar una nueva versión con su PDF, manteniendo accesibles las versiones anteriores en la web.

**Blocked by:** 04 — Generar y entregar el PDF.

**Status:** implementation-complete; real Telegram verification pending user credentials

**Referencia:** [PDF del presupuesto](../spec.md#pdf-del-presupuesto), conservación de versiones; [Criterios complementarios](../spec.md#criterios-complementarios); [Supuestos y datos pendientes](../spec.md#supuestos-y-datos-pendientes). Aclaración aprobada en la conversación de descomposición: solo se permiten nuevas versiones mientras el presupuesto esté pendiente.

## Alcance de la sesión

- Recuperar un presupuesto pendiente y partir de su versión vigente para corregirlo.
- Reutilizar la revisión y confirmación del bot antes de emitir otra versión.
- Conservar la relación entre las versiones de un mismo presupuesto y permitir consultar sus documentos.

## Criterios de aceptación

- [x] El mecánico selecciona un presupuesto pendiente, corrige sus datos y obtiene un resumen antes de confirmar la nueva versión.
- [x] La confirmación crea una versión identificable como nueva, vinculada al mismo presupuesto y con fecha, detalle económico y PDF propios.
- [x] Si la versión inicial suma ARS 70.000 y la corrección suma ARS 72.000, ambas versiones conservan exactamente esos valores.
- [x] El PDF nuevo se entrega al confirmar por Telegram; desde la web se distingue la versión vigente y se descarga cada versión anterior.
- [x] Una corrección no sobrescribe el detalle ni el PDF de versiones ya confirmadas; la persistencia se almacena en SQLite y `media/`.
- [x] La operación de crear versión solo acepta presupuestos pendientes; la comprobación se realiza en la operación de guardado dentro de una transacción.
- [x] Se verifica la vinculación de versiones, la conservación de los documentos y el rechazo de una revisión para un presupuesto no pendiente mediante datos de prueba. El flujo real de cambio de estado se incorpora en el ticket 07.

## Implementación

- `Budget` conserva cada versión como registro independiente, relacionado con la versión anterior mediante `previous_version` y numerado en `version`.
- `/corregir` lista las versiones vigentes pendientes. La selección abre un resumen editable y la confirmación genera un nuevo número y PDF; la entrega y reintento usan el flujo del ticket 04.
- El historial web etiqueta versiones vigentes e históricas y ofrece la descarga individual de cada PDF.
- Migración `0005_budget_previous_version_budget_version.py` agrega la relación y el número de versión. Verificado con 24 pruebas, `manage.py check` y `makemigrations --check --dry-run`.
- La prueba real de entrega en Telegram queda pendiente de las credenciales locales del usuario.

## Decisión de dominio confirmada

Al aprobar o rechazar un presupuesto se cierra la posibilidad de crear nuevas versiones. Las diferencias de materiales o importes de un trabajo aprobado se registran al finalizarlo, sin reescribir el presupuesto. La inmutabilidad se aplica al contenido confirmado de cada versión; el estado administrativo puede avanzar según el flujo.
