# 07: Aprobar o rechazar presupuestos

**Objetivo / Qué construir:** permitir al administrador registrar desde la web la aprobación o el rechazo de un presupuesto pendiente y hacer efectiva esa decisión en las operaciones disponibles desde Telegram.

**Blocked by:** 06 — Corregir mediante nuevas versiones.

**Status:** implementation-complete

**Referencia:** [Gestión web e historial](../spec.md#gestión-web-e-historial), estados; [Recorrido principal](../spec.md#recorrido-principal), paso 4. Aclaración aprobada en la conversación de descomposición: aprobar o rechazar cierra las correcciones; los cambios de un trabajo aprobado se registran al terminarlo.

## Alcance de la sesión

- Mostrar el estado en el historial y el detalle del presupuesto.
- Permitir aprobar o rechazar la versión vigente de un presupuesto pendiente.
- Aplicar la restricción de nuevas versiones en todo el flujo.

## Criterios de aceptación

- [x] Un presupuesto confirmado aparece como pendiente en la web.
- [x] El administrador puede marcarlo como aprobado o rechazado y el estado persiste al reiniciar.
- [x] La acción corresponde a la versión vigente del presupuesto: las versiones históricas se conservan para consulta y no se aprueban como trabajos independientes.
- [x] Tras aprobar o rechazar, Telegram impide generar otra versión y explica que el presupuesto ya no está pendiente.
- [x] Una corrección iniciada antes del cambio de estado tampoco puede confirmarse después de la aprobación o el rechazo.
- [x] El cambio de estado no altera los importes ni los PDFs emitidos.
- [x] No hay una acción de reapertura a pendiente en esta demo; el trabajo aprobado podrá terminarse mediante el ticket 08.
- [x] Se verifican aprobación, rechazo y rechazo de una corrección iniciada antes del cambio de estado.

## Límites

El administrador registra una decisión del cliente; no se implementa un portal de aprobación para el cliente ni envío automático de notificaciones. El cierre con materiales e importe final corresponde al ticket 08.

## Implementación

- El administrador puede cambiar de pendiente a aprobado o rechazado desde el historial web. La operación requiere autenticación, POST y CSRF; solo modifica la versión vigente y no permite reabrir el presupuesto.
- Se amplió el estado de presupuesto y se añadió la migración `0006_alter_budget_status.py`.
- La operación de guardar una nueva versión ya valida dentro de una transacción que el presupuesto continúa pendiente; el callback de Telegram comunica el rechazo si otra acción cerró el presupuesto mientras la corrección estaba en curso.
- Pruebas cubren aprobación y rechazo, bloqueo de versiones históricas, rechazo de una corrección en curso y preservación del total y PDF.
- Verificación: 27 pruebas pasan; `manage.py check` y `makemigrations --check --dry-run` sin errores.
