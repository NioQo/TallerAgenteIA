# 06: Continuar el borrador por el flujo guiado

**What to build:** permitir que el Operador complete por el flujo guiado actual un borrador preservado cuando la IA falla o no puede completar una aclaración.

**Blocked by:** 01 — Validar el borrador completo antes de confirmar; 02 — Persistir ediciones y revocar confirmaciones descartadas; 03 — Enviar solo el mensaje actual a OpenAI; 05 — Aplicar correcciones parciales sin perder datos.

**Status:** ready-for-agent — Requisito incumplido P1.

**Problema y requisito afectado:** el fallback vuelve a pedir datos desde cero, el alta de vehículo nuevo debe salir de la conversación y `/listo` bloquea trabajos sin repuestos. Incumple spec IA, criterios 2, 3, 5 y 8; ticket IA 02, criterio 1; ticket IA 04, criterios 4–5.

**Pasos para reproducir:** crear borrador con vehículo nuevo incompleto o marcar trabajo solo de mano de obra; continuar con `/presupuesto` o simular timeout de IA.

**Comportamiento actual:** se pierde el progreso al pedir la patente/registro guiado por separado; el flujo guiado exige al menos un repuesto aunque se indicó trabajo sin repuestos.

**Comportamiento esperado:** continuar el mismo borrador, reutilizar datos ya aportados y preguntar solo lo faltante, sin depender de que OpenAI vuelva a estar disponible.

- [ ] Timeout, error o respuesta inválida conserva borrador y ofrece reintentar o continuar manualmente ese borrador.
- [ ] Alta de vehículo nuevo guiada pide solo los campos que falten y no pierde lo ya ingresado.
- [ ] La patente existente se reutiliza; las contradicciones siguen requiriendo resolución explícita.
- [ ] “Solo mano de obra” permite omitir repuestos tanto en IA como en el flujo manual alternativo.
- [ ] Añadir pruebas de timeout, vehículo nuevo parcial, vehículo existente y mano de obra sin repuestos.

**Dependencias:** 01, 02, 03, 05.
