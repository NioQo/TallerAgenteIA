# 07: Completar el flujo de presupuesto por lenguaje natural

**What to build:** llevar un mensaje directo completo al resumen vigente y permitir resolver explícitamente las sugerencias del catálogo sin exigir un comando de presupuesto.

**Blocked by:** 01 — Validar el borrador completo antes de confirmar; 02 — Persistir ediciones y revocar confirmaciones descartadas; 03 — Enviar solo el mensaje actual a OpenAI; 05 — Aplicar correcciones parciales sin perder datos; 06 — Continuar el borrador por el flujo guiado.

**Status:** ready-for-agent — Requisito incumplido P2.

**Problema y requisito afectado:** la ruta IA muestra un borrador informativo y obliga a iniciar `/presupuesto` para confirmar; no presenta la sugerencia histórica del catálogo con aceptación explícita en esa ruta. Incumple spec IA, criterios 1, 4, 5, 9 y ticket IA 01, criterios 1, 5–7.

**Pasos para reproducir:** enviar un mensaje directo con vehículo existente, descripción, repuestos, precios y mano de obra; repetir con un repuesto presente en catálogo.

**Comportamiento actual:** no aparece el resumen confirmable prometido por mensaje directo, y no hay aceptación de catálogo en el borrador IA.

**Comportamiento esperado:** preguntas agrupadas para faltantes; con datos completos, resumen de identidad y valores, sugerencia histórica explícita cuando aplique, y confirmación vigente sin repetir captura.

- [ ] Un mensaje completo produce un resumen confirmable sin exigir `/presupuesto`.
- [ ] Si hay faltantes, se preguntan juntos cuando sea posible y se conservan respuestas parciales.
- [ ] Una sugerencia de catálogo se presenta como referencia histórica y exige aceptación o reemplazo.
- [ ] No se inventan precios; ambigüedades y ausencia de repuestos se aclaran.
- [ ] Rechazo, modificación o aceptación de sugerencia no modifica el catálogo antes de confirmar.
- [ ] Añadir pruebas del mensaje completo, faltantes parciales, catálogo y confirmación repetida/obsoleta.

**Dependencias:** 01, 02, 03, 05, 06.
