# 03: Enviar solo el mensaje actual a OpenAI

**What to build:** construir solicitudes que incluyan únicamente el mensaje entrante y sigan funcionando en interacciones sucesivas con importes estructurados.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Corrección de error P1; requiere cerrar el tratamiento operativo antes de habilitar la integración real.

**Problema y requisito afectado:** El ticket IA 02, comentario de definición operativa, y README acordaron enviar solo el mensaje actual, nunca el borrador previo. La revisión capturó el teléfono del borrador previo en el JSON enviado. También reprodujo un fallo al serializar un `Decimal` guardado en ese borrador en la siguiente interacción. Incumple la spec IA, alcance 13–15, cuestión operativa 55 y criterio 2.

**Pasos para reproducir:** iniciar borrador con teléfono y precio, capturar la petición de OpenAI y luego responder con otra corrección cuando los precios ya estén normalizados como `Decimal`.

**Comportamiento actual:** la solicitud incorpora `previous`; con determinados importes la serialización falla antes de realizar la segunda llamada.

**Comportamiento esperado:** no transmitir estado previo ni otros datos personales; las sucesivas interacciones no fallan por el tipo de datos persistidos.

- [ ] El cuerpo enviado al cliente de OpenAI contiene únicamente el texto del mensaje entrante y las instrucciones/schema sin datos del borrador.
- [ ] Un borrador con campos decimales persiste y la siguiente solicitud se construye sin error.
- [ ] Pruebas con cliente HTTP simulado inspeccionan la petición y comprueban ausencia de patente, nombre, teléfono, precios e historial previo.
- [ ] Prueba de dos turnos con precios confirma que ambas llamadas se pueden construir y que la respuesta se combina localmente.
- [ ] Antes de habilitar solicitudes reales quedan documentados los campos transmitidos, retención y límites de uso/costo, según la spec IA:55.
- [ ] No usar secretos ni datos reales en las pruebas.

**Dependencias:** Ninguna; la verificación real del ticket 15 queda bloqueada hasta cerrar los asuntos operativos.
