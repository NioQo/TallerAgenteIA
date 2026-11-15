# 05: Aplicar correcciones parciales sin perder datos

**What to build:** corregir únicamente los datos que el Operador menciona, conservar el resto del borrador y retirar las aclaraciones que ya se resolvieron.

**Blocked by:** 01 — Validar el borrador completo antes de confirmar; 03 — Enviar solo el mensaje actual a OpenAI.

**Status:** ready-for-agent — Requisito incumplido P1.

**Problema y requisito afectado:** Una corrección del repuesto A reemplazó la lista que también contenía B; una respuesta sin incertidumbres no limpió una duda previa. Incumple spec IA, criterios 2 y 6, y ticket IA 03, criterio 1.

**Pasos para reproducir:** preparar dos repuestos y una pregunta pendiente, luego enviar una corrección de precio para uno de ellos que resuelva la aclaración.

**Comportamiento actual:** la lista completa puede reemplazarse y la duda antigua permanece; algunos campos booleanos también pueden reemplazarse aunque no se mencionen.

**Comportamiento esperado:** aplicar una modificación puntual por campo/ítem; conservar otros valores, repuestos y pendientes aún sin resolver.

- [ ] Corregir un campo escalar conserva todos los demás campos.
- [ ] Corregir un ítem identifica y actualiza ese ítem sin eliminar los restantes.
- [ ] Una aclaración resuelta retira solo la incertidumbre relacionada; las otras siguen visibles.
- [ ] Una respuesta que no menciona `labor_only` no cambia esa decisión.
- [ ] Cada cambio actualiza el resumen y revoca botones de confirmación previos.
- [ ] Añadir pruebas de corrección de descripción, mano de obra, un ítem entre varios, duda resuelta y duda no relacionada.

**Dependencias:** 01, 03.
