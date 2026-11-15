# 01: Validar el borrador completo antes de confirmar

**What to build:** impedir que datos de IA incompletos, contradictorios o económicamente inválidos se conviertan en presupuesto, vehículo, PDF o cambio de catálogo.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Corrección de error P1.

**Problema y requisito afectado:** En la revisión se reprodujo la confirmación de un presupuesto con mano de obra `-100`; además, desapareció un repuesto con precio total ambiguo y se aceptaron en silencio datos de cliente contradictorios con el vehículo existente. Incumple la spec IA, reglas 15, 18 y 31; criterios 3–5 y 9; ticket IA 01, criterios 3–7; ticket IA 04, criterio 5.

**Pasos para reproducir:** preparar un borrador IA de un vehículo registrado, especificar datos de cliente distintos, mano de obra negativa y un repuesto que solo tenga precio total; continuar a la confirmación.

**Comportamiento actual:** se omite el repuesto sin resolución, se conserva el cliente registrado sin confirmación, y el total negativo se puede guardar.

**Comportamiento esperado:** no se presenta un resumen confirmable mientras falte resolver datos obligatorios, ambigüedades o contradicciones. Todos los importes y cantidades cumplen las reglas de dominio antes de cualquier escritura.

- [ ] Mano de obra no admite negativos, NaN, infinitos, exceso de precisión ni valores fuera de rango.
- [ ] Cada repuesto candidato debe quedar completo con cantidad positiva y precio unitario válido; no se descarta ningún repuesto silenciosamente.
- [ ] Precio total sin desglose unitario produce una aclaración y no un cálculo inventado.
- [ ] Contradicciones con vehículo/cliente registrado requieren confirmación o corrección explícita.
- [ ] Solo datos validados habilitan confirmación; la escritura valida nuevamente y es atómica.
- [ ] Reproducir casos válidos e inválidos y demostrar que los inválidos no crean vehículo, presupuesto, versión, PDF ni cambios de catálogo.
- [ ] Añadir regresiones automatizadas para importes negativos/no finitos, campos incompletos, precio total ambiguo y contradicciones.

**Dependencias:** Ninguna.
