# Demo de presupuestos para taller mecánico

## Objetivo

Demostrar un flujo que permita al mecánico preparar presupuestos desde Telegram, generar un PDF para enviar al cliente y mantener en una web el historial de vehículos, presupuestos y trabajos realizados.

El problema actual es que preparar cada presupuesto toma aproximadamente entre una y dos horas. El mecánico verifica el problema del vehículo y consulta a dos proveedores por WhatsApp; luego otra persona arma el presupuesto con costos, mano de obra y marca del taller. La mayoría de los trabajos actuales (aproximadamente 90%) son para patrulleros de la Municipalidad y el resto para clientes particulares. Estas proporciones describen el contexto informado, no una regla del sistema.

## Alcance de la demo

- Un único taller.
- Bot real de Telegram, conectado al sistema y utilizable mientras el programa esté ejecutándose en la computadora del usuario.
- Aplicación web para consulta y gestión administrativa.
- Persistencia de datos entre sesiones.
- Un mecánico autorizado mediante su cuenta de Telegram.
- Un administrador con usuario y contraseña para la web. Una persona puede cumplir ambos roles.
- Interacción del bot mediante botones y mensajes de texto. No se incluyen audios ni fotos.
- Consulta de precios a proveedores continúa siendo manual por WhatsApp; el mecánico carga los precios obtenidos en el bot.

## Estado y ampliaciones posteriores

Esta especificación describe la demo base ya construida; no incluye la futura interpretación de mensajes mediante IA ni el rediseño visual integral. Esas ampliaciones están especificadas por separado: [Asistente IA para presupuestos](../asistente-ia-presupuestos/spec.md) y [Rediseño profesional de la web](../rediseno-web/spec.md). La demo conserva su ejecución local actual. El despliegue para clientes en VPS es una etapa posterior y queda fuera de esas ampliaciones.

## Flujo para crear un presupuesto

1. El mecánico inicia un presupuesto en Telegram e identifica el vehículo por patente.
2. Registra o confirma marca, modelo y cliente asociado. El cliente se clasifica como Municipalidad o particular y cuenta con nombre y teléfono.
3. Carga la descripción del trabajo, los repuestos, cantidades, precios y el importe total de mano de obra.
4. Para cada repuesto, el sistema puede sugerir un precio del catálogo. El mecánico puede confirmarlo o cambiarlo. Los precios consultados a proveedores se ingresan manualmente.
5. El bot muestra un resumen antes de confirmar. El mecánico puede corregir los datos o confirmar.
6. Al confirmar, el sistema registra el presupuesto, calcula el total y genera un PDF que entrega al mecánico por Telegram.
7. El mecánico revisa el PDF y lo envía al cliente fuera del sistema.

## Cálculo y precios

- Total del presupuesto = suma de (cantidad × precio unitario de cada repuesto) + importe total de mano de obra.
- No se aplican márgenes automáticos, impuestos ni descuentos en la demo.
- La mano de obra se ingresa como un importe total manual para cada reparación, tanto municipal como particular. Es un supuesto de demo; la regla real de la empresa aún no está confirmada.
- Los precios de repuestos ingresados se guardan en un catálogo para sugerirlos en presupuestos futuros. El usuario puede aceptar o reemplazar una sugerencia.
- Cada presupuesto conserva los precios usados al crearse, aunque luego cambie el catálogo.
- Importes en pesos argentinos (ARS).

## PDF del presupuesto

El PDF incluirá:

- Logo y datos del taller.
- Número y fecha del presupuesto.
- Cliente y tipo de cliente.
- Vehículo (patente, marca y modelo).
- Descripción del trabajo.
- Repuestos, cantidades, precios unitarios e importes.
- Mano de obra y total.

Los datos del taller que todavía no se conozcan serán ficticios para la demo. Una corrección posterior crea una nueva versión vinculada a la anterior; las versiones previas no se modifican.

## Gestión web e historial

- Listar y consultar vehículos, cada uno identificado por patente y con marca, modelo y cliente asociado.
- Consultar el historial de presupuestos del vehículo y descargar sus PDFs.
- Cambiar el estado del presupuesto a pendiente, aprobado, rechazado o trabajo terminado.
- Al finalizar un trabajo, registrar los repuestos realmente utilizados y el importe final cobrado, manteniendo intacto el presupuesto original.
- Mostrar un resumen mensual de trabajos terminados e importes cobrados.
- Permitir filtros por fecha, patente y tipo de cliente.
- En el resumen de cobros, contar el importe final cobrado del trabajo, no sumar también el importe estimado del presupuesto.

## Criterios de aceptación

### Recorrido principal

1. El mecánico registra un vehículo desde Telegram.
2. Carga dos unidades de repuesto a ARS 15.000 cada una y ARS 40.000 de mano de obra.
3. El sistema presenta el resumen para revisión y, al confirmarlo, produce un PDF por ARS 70.000 y lo entrega al mecánico por Telegram.
4. El administrador encuentra el vehículo y el presupuesto en la web y lo marca como aprobado.
5. Al terminar el trabajo, el administrador registra los materiales realmente utilizados y ARS 75.000 como importe final cobrado.
6. El historial conserva el presupuesto de ARS 70.000 y el cierre de ARS 75.000.
7. El resumen mensual muestra ARS 75.000 cobrados para ese trabajo, sin sumar también los ARS 70.000 presupuestados.
8. Tras cerrar y volver a abrir la aplicación o iniciar una nueva sesión, los datos siguen disponibles.

### Criterios complementarios

- Un precio guardado en el catálogo se sugiere para un presupuesto posterior, pero puede modificarse.
- Cambiar un precio del catálogo no altera presupuestos ya creados.
- Una corrección de presupuesto genera una versión nueva y conserva la anterior.
- El bot permite revisar y corregir el resumen antes de confirmar la generación del PDF.
- El PDF incluye los campos indicados en la sección correspondiente, con importes en ARS.
- El administrador puede filtrar registros por fecha, patente y tipo de cliente.

## Supuestos y datos pendientes

- La mano de obra se ingresa como importe manual por reparación para ambos tipos de cliente: supuesto para simplificar la demo, no regla validada del taller.
- Los datos de identidad del taller y el logo serán ficticios hasta recibir los reales.
- No se ha definido aún el formato de factura o comprobante fiscal; el PDF descrito es un presupuesto, no una factura.
- La automatización de consultas a proveedores queda fuera de alcance; las consultas continúan por WhatsApp y la carga de precios es manual.
- Las correcciones posteriores al presupuesto se representan con versiones vinculadas; no se sobrescribe el documento confirmado.

## Registro de verificación manual

- **2026-11-12:** recorrido real confirmado hasta la emisión del presupuesto: inicio de sesión en la web, conexión y autorización del bot de Telegram, alta de AB123CD (Toyota Corolla, cliente particular), creación y confirmación de P-000001, recepción del PDF por Telegram con total ARS 70.000 y consulta satisfactoria del vehículo y presupuesto en la web.
- **Pendiente para declarar completo el recorrido principal:** aprobar el presupuesto desde la web, registrar el trabajo con importe final cobrado de ARS 75.000, verificar que el resumen mensual muestre ARS 75.000 sin sumar el presupuesto y comprobar persistencia tras reiniciar. No se probó el acceso con una cuenta Telegram no autorizada ni la descarga del PDF desde la web.
- Los filtros del historial ya están implementados y cubiertos por pruebas automatizadas (ticket 09); esto no equivale a una verificación manual del recorrido completo.
- **Pruebas automatizadas, 2026-11-12:** suite Django completa (48 pruebas) y `manage.py check` pasaron durante el rediseño web. Cubren los flujos funcionales, incluyendo filtros, decisión, cierre, descarga y resumen; no reemplazan el recorrido financiero manual pendiente.
