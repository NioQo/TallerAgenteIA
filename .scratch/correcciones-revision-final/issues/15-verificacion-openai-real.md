# 15: Verificar extracción con OpenAI real

**What to build:** comprobar la calidad y tolerancia a fallos de la extracción contra OpenAI real, solo después de cerrar el contrato de datos y proteger los flujos locales.

**Blocked by:** 01 — Validar el borrador completo antes de confirmar; 03 — Enviar solo el mensaje actual a OpenAI; 05 — Aplicar correcciones parciales sin perder datos; 06 — Continuar el borrador por el flujo guiado; 07 — Completar el flujo de presupuesto por lenguaje natural; 08 — Corregir presupuestos pendientes mediante lenguaje natural.

**Status:** pending-verification — Sin clave/servicio real en la revisión; no se asume defecto del modelo.

**Problema y requisito afectado:** spec IA, criterios 1–11 y cuestión operativa 55; tickets IA 01, 03 y 04. Los tests existentes simulan la extracción y no verifican comprensión, latencia ni formato del proveedor real.

**Pasos para verificar:** una vez autorizada la política y configurada localmente una clave, usar datos ficticios: presupuesto completo, “50 mil”, precio unitario/total ambiguo, faltantes parciales, corrección de un repuesto entre varios, contradicción de vehículo, timeout y respuesta inválida.

**Comportamiento actual:** integración real no ejecutada; no hay evidencia para afirmar que el modelo falla o cumple esos escenarios.

**Comportamiento esperado:** candidatos explícitos y validados, aclaraciones sin inventar importes, conservación del borrador y fallback manual; nunca escribir registros directamente desde la salida del modelo.

- [ ] Confirmar antes de prueba la lista de datos transmitidos, política de retención, presupuesto/límites de uso y tratamiento de datos personales.
- [ ] Usar solo identidad y datos ficticios; no registrar clave ni payload con datos sensibles.
- [ ] Registrar solicitud/respuesta observada de forma redactada, resultado y coste/latencia si el proveedor lo expone.
- [ ] Comprobar los escenarios indicados, incluidos errores y reintento; separar resultados del servicio real de mocks.
- [ ] No marcar como aceptado ningún criterio sin evidencia reproducible; si falta acceso, conservar estado pendiente.

**Dependencias:** 01, 03, 05, 06, 07, 08.
