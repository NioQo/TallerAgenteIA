# 08: Corregir presupuestos pendientes mediante lenguaje natural

**What to build:** permitir localizar por número el presupuesto pendiente vigente, aplicar una corrección puntual y completar la nueva versión sin alterar el historial.

**Blocked by:** 03 — Enviar solo el mensaje actual a OpenAI; 04 — Seleccionar correctamente presupuestos para corregir; 05 — Aplicar correcciones parciales sin perder datos; 06 — Continuar el borrador por el flujo guiado; 07 — Completar el flujo de presupuesto por lenguaje natural.

**Status:** ready-for-agent — Requisito incumplido P2.

**Problema y requisito afectado:** el asistente no ofrece una ruta natural por número de presupuesto pendiente; la ruta existente `/corregir` está bloqueada por la selección incorrecta. Incumple spec IA, criterio 10; ticket IA 03, criterios 2–6.

**Pasos para reproducir:** mencionar una corrección para un presupuesto pendiente identificado por número; intentar corregir otro que esté aprobado o histórico.

**Comportamiento actual:** la interacción IA trata el mensaje como datos de un borrador nuevo y no selecciona una versión existente por número.

**Comportamiento esperado:** validar número y vigencia, cambiar solo lo indicado, revisar resumen y crear nueva versión solo tras confirmación explícita.

- [ ] El presupuesto se encuentra por número público y se selecciona su versión vigente.
- [ ] Solo una versión vigente pendiente admite revisión.
- [ ] La corrección conserva ítems/campos no mencionados y requiere resumen vigente.
- [ ] La nueva versión conserva anterior y PDF; la vigente puede decidirse/cerrarse y la histórica solo consultarse.
- [ ] Añadir pruebas para número válido, inexistente, histórico, decidido, callback obsoleto, aprobación y cierre de la nueva vigente.

**Dependencias:** 03, 04, 05, 06, 07.
