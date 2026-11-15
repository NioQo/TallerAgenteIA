# 02: Persistir ediciones y revocar confirmaciones descartadas

**What to build:** recuperar el último estado del borrador y hacer que descartarlo invalide cualquier ruta de confirmación previamente preparada.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Corrección de error P1.

**Problema y requisito afectado:** La revisión cambió la mano de obra guiada en memoria, pero el borrador persistido conservó el importe anterior. También reprodujo que, tras descartar, un botón antiguo aún crea un presupuesto. Incumple la spec IA, criterios 7 y 9; ticket IA 02, criterios 1–3; ticket IA 04, criterios 2–3.

**Pasos para reproducir:** continuar un borrador persistido, cambiar un campo desde el flujo guiado, reiniciar y recuperar; luego preparar un resumen, descartar el borrador y pulsar la confirmación anterior.

**Comportamiento actual:** se recuperan datos anteriores a la edición; el descarte borra el registro IA, pero deja una clave de confirmación guiada válida en el contexto.

**Comportamiento esperado:** cada edición aceptada queda persistida y el descarte invalida todas las confirmaciones ligadas a ese borrador; un callback tardío no tiene efectos.

- [ ] Editar descripción, repuestos o mano de obra actualiza el borrador durable y sus preguntas pendientes.
- [ ] Recuperar tras recrear el proceso devuelve el último cambio confirmado por el operador.
- [ ] Descartar elimina el borrador y revoca el estado/clave de confirmación asociado.
- [ ] Un botón guardado antes del descarte no crea presupuesto, versión, PDF, vehículo ni cambio de catálogo.
- [ ] Una confirmación vigente repetida sigue siendo idempotente.
- [ ] Añadir pruebas de recuperación, edición por cada campo, descarte seguido de callback obsoleto y repetición de confirmación.

**Dependencias:** Ninguna.
