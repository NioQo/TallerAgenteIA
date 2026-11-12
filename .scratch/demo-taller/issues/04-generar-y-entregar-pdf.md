# 04: Generar y entregar el PDF

**Objetivo / Qué construir:** entregar al mecánico el PDF del presupuesto confirmado mediante Telegram y permitir al administrador descargar el mismo documento desde el historial web.

**Blocked by:** 03 — Preparar y confirmar presupuestos.

**Status:** implementation-complete; real Telegram PDF delivery verified

**Referencia:** [PDF del presupuesto](../spec.md#pdf-del-presupuesto); [Flujo para crear un presupuesto](../spec.md#flujo-para-crear-un-presupuesto), pasos 6–7; [Recorrido principal](../spec.md#recorrido-principal), paso 3.

## Alcance de la sesión

- Generar un PDF legible con identidad ficticia del taller cuando falten datos reales.
- Entregar el documento como archivo en Telegram tras la confirmación.
- Habilitar su descarga desde el presupuesto en la web protegida.

## Criterios de aceptación

- [x] El PDF incluye marca/datos ficticios del taller, número, fecha, cliente y tipo, patente, marca, modelo, descripción, cantidades, precios unitarios, importes, mano de obra y total en ARS.
- [x] El documento se identifica como presupuesto y no como factura.
- [x] El presupuesto de prueba de ARS 70.000 persiste sus importes y genera un archivo PDF.
- [x] El mecánico recibe y puede abrir el PDF enviado por el bot real. Verificado manualmente; el envío al cliente es externo al sistema.
- [x] El administrador puede descargar el mismo documento desde el historial; la descarga requiere sesión.
- [x] La tabla PDF repite encabezados y se pagina para conservar legibilidad de listas largas.
- [x] El documento queda guardado en `media/presupuestos/` junto al presupuesto, independiente de datos posteriores.
- [x] Si falla el envío a Telegram, el presupuesto confirmado se conserva y `/reenviar <número>` permite reintentar.
- [x] Verificación real de entrega y apertura en Telegram completada. La descarga desde la web sigue pendiente de prueba manual.

## Implementación

- ReportLab genera el PDF al confirmar y lo guarda asociado al presupuesto en `media/presupuestos/`.
- Telegram recibe el documento al confirmar; `/reenviar P-000001` reintenta sin crear otro presupuesto.
- La URL de descarga requiere sesión y se muestra en el historial del vehículo.
- Prueba real de entrega completada con las credenciales locales del usuario; ver Comments. La descarga desde la web no se comprobó en esta sesión.

## Límites

No enviar automáticamente el documento al cliente ni integrar WhatsApp. La identidad ficticia es material de demo, no una identidad confirmada de la empresa.

## Comments

- Verificación manual real: tras confirmar P-000001, el mecánico recibió y pudo leer el PDF en Telegram. El usuario confirmó que presupuesto e historial se visualizan correctamente en la web. La descarga del PDF desde la web no se probó expresamente en esta sesión.
