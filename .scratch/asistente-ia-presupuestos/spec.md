# Asistente de Telegram con IA para presupuestos

## Objetivo

Permitir que el Operador de Telegram describa en lenguaje natural un presupuesto o una corrección, y que el bot convierta esa información en un borrador, consulte solo lo que falta o requiere aclaración y conserve el flujo de revisión y confirmación explícita.

Esta es una ampliación posterior e independiente de la demo base descrita en [Demo de presupuestos para taller](../demo-taller/spec.md). No afirma que la IA ni la persistencia de borradores estén implementadas.

## Alcance

- Una única cuenta numérica autorizada de Telegram, que en la demo puede utilizar el mecánico o su ayudante.
- Mensajes de texto directos al bot; se mantienen disponibles los comandos y botones existentes. Audio, transcripción y operación multiusuario no forman parte de esta ampliación.
- API de OpenAI; el modelo será configurable. La clave se configura localmente y nunca se registra en el repositorio.
- Entender mensajes que describen un presupuesto y extraer los datos explícitos, sin delegar a la IA cálculos definitivos ni persistencia de registros.
- Reutilizar el vehículo y datos del cliente ya registrados. Si hay contradicciones, pedir confirmación o corrección antes de seguir.
- Permitir completar el alta de un vehículo nuevo en la misma conversación, reutilizando lo aportado y preguntando por los campos obligatorios faltantes.
- Preguntar los faltantes en un solo mensaje cuando sea posible y conservar respuestas parciales. Una omisión de repuestos requiere aclarar si el trabajo es solo mano de obra.
- Interpretar formatos comunes de importes (por ejemplo, “50 mil”) y preguntar si no se entiende si el precio es unitario o total. Nunca inventar importes.
- Sugerir precios existentes del catálogo como referencias históricas, con aceptación explícita; si no hay precio confirmado, preguntar.
- Permitir presupuestos de solo mano de obra cuando el Operador lo indique.
- Permitir correcciones puntuales del borrador y de presupuestos pendientes existentes. Una corrección confirmada crea una nueva versión inmutable, preservando las anteriores.
- Mantener un único borrador persistente por cuenta autorizada, recuperable tras reiniciar el proceso, con opción de continuar o descartar.
- Ante un fallo de la API, informar el problema y permitir reintentar o continuar el mismo borrador mediante el flujo guiado actual.
- Guardar el vehículo nuevo y actualizar el catálogo solo al confirmar el presupuesto; descartar no produce esos efectos.
- Mantener la ejecución local actual de la demo. Instalación y operación en VPS para clientes quedan fuera de alcance.

## Reglas y compatibilidad

- El total sigue siendo la suma de cantidad por precio unitario más mano de obra, en ARS; no hay impuestos, márgenes ni descuentos automáticos.
- Los precios consultados a proveedores se siguen cargando manualmente. Una sugerencia del catálogo no representa una cotización actual.
- La IA prepara datos candidatos; validaciones de dominio y cálculos deterministas preceden a toda escritura.
- Un resumen debe mostrar identidad del vehículo (patente, marca/modelo) y cliente para revisar la selección correcta.
- Solo el botón de confirmación del resumen vigente puede crear presupuesto/versión y PDF. Toda modificación invalida confirmaciones anteriores. La operación repetida no duplica registros.
- Se conservan autorización de Telegram, números, estados, PDF, historial, datos y presupuestos existentes.
- Las versiones históricas son inmutables. La versión vigente pendiente puede corregirse, aprobarse o rechazarse; un presupuesto no pendiente no admite nuevas correcciones.
- La indisponibilidad de IA no debe impedir completar un presupuesto con el flujo guiado tradicional.

## Criterios de aceptación

1. Un mensaje directo que incluya los datos necesarios produce el resumen sin exigir `/presupuesto` ni preguntas redundantes.
2. Si faltan varios datos obligatorios, se solicitan juntos; responder solo algunos conserva lo demás y la siguiente pregunta se limita a faltantes.
3. Una patente existente rellena los datos asociados; una contradicción se confirma y no reemplaza datos en silencio. Una patente nueva permite completar el vehículo sin perder el borrador.
4. El bot entiende expresiones inequívocas como “50 mil”; si “dos discos por 100 mil” puede ser precio unitario o total, no calcula hasta aclararlo.
5. Un precio del catálogo se presenta como sugerencia y requiere aceptación; nunca se inventan precios. Repuestos omitidos se aclaran; “sin repuestos” permite presupuesto de mano de obra únicamente.
6. Una instrucción de corrección puntual modifica únicamente el dato indicado y refresca el resumen.
7. Reiniciar y volver a iniciar el bot permite continuar o descartar el borrador persistido. Descartar no crea vehículo ni cambia catálogo.
8. Un fallo o respuesta inválida de API conserva el borrador y permite reintento o completar manualmente.
9. Confirmar el resumen vigente una sola vez emite un presupuesto con totales calculados por reglas deterministas y PDF; una repetición o botón obsoleto no crea otro presupuesto ni confirma contenido distinto.
10. Corregir un presupuesto pendiente emite una nueva versión, conservando datos y PDF anteriores. La versión vigente corregida puede aprobarse y cerrarse; las históricas no se gestionan como presupuestos independientes.
11. Los comandos y botones actuales siguen disponibles como alternativa, y los datos guardados antes de la ampliación siguen consultables.

## Fuera de alcance y cuestiones operativas

- Audio, reconocimiento de voz, fotos, acceso del cliente, más de una cuenta autorizada, consulta automática a proveedores, facturación e instalación VPS.
- La información exacta que se enviará al proveedor, retención de conversaciones, límites de gasto/uso y tratamiento de datos personales requieren definición operativa antes de habilitar el envío a la API. No se deben enviar secretos.
- El flujo existente de precios del catálogo se actualizará únicamente al confirmar, aunque el usuario acepte una sugerencia o ingrese un precio durante el borrador.

## Plan de tickets

- [01 — Interpretar mensajes y construir borradores](issues/01-interpretar-mensajes-y-borradores.md)
- [02 — Persistir y recuperar borradores](issues/02-persistir-borradores.md)
- [03 — Corregir versiones y preservar compatibilidad](issues/03-correcciones-y-versiones.md)
- [04 — Proteger confirmación y manejo de fallos](issues/04-confirmacion-y-fallos.md)
