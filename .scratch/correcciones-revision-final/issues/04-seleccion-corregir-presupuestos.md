# 04: Seleccionar correctamente presupuestos para corregir

**What to build:** permitir al Operador elegir una versión vigente pendiente con `/corregir` y abrir el resumen correcto para crear una revisión.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Corrección de error P1.

**Problema y requisito afectado:** La lista transmite el PK del presupuesto, pero la consulta interpreta el valor como número público. La revisión reprodujo el rechazo de un presupuesto pendiente válido. Incumple la spec base, criterio complementario 3; ticket base 06, criterio 1; spec IA, criterio 10 y ticket IA 03, criterios 2–3.

**Pasos para reproducir:** crear un presupuesto pendiente, ejecutar `/corregir` y elegirlo.

**Comportamiento actual:** el callback busca el número público usando el PK y responde que el presupuesto no está pendiente o ya tiene una versión posterior.

**Comportamiento esperado:** el identificador transmitido se resuelve con el mismo tipo de identificador y se abre el resumen de la versión vigente elegida.

- [ ] Seleccionar un presupuesto pendiente sin revisión abre su resumen y permite editarlo.
- [ ] Seleccionar una versión histórica, un presupuesto decidido o uno que ya tenga revisión no permite crear otra.
- [ ] La confirmación crea una versión vinculada y conserva valores, ítems y PDF anteriores.
- [ ] Añadir prueba del flujo callback completo con un PK distinto del número público y pruebas para estados/versiones no elegibles.

**Dependencias:** Ninguna.
