# 01: Interpretar mensajes y construir borradores

**Objetivo / Qué construir:** permitir que el Operador describa un presupuesto en un mensaje libre y el bot extraiga datos estructurados, identifique los faltantes y guíe aclaraciones sin emitir decisiones económicas por cuenta propia.

**Status:** spec-ready

**Referencia:** [Especificación del asistente IA](../spec.md), alcance, reglas y criterios 1–6.

## Alcance

- Integrar API de OpenAI con modelo configurable y configuración secreta local.
- Entender mensajes directos, seleccionar vehículo por patente, resolver datos existentes/nuevos y preparar un borrador.
- Preguntar faltantes juntos, conservar respuestas parciales y resolver contradicciones/ambigüedades.
- Proponer el catálogo sin tratar sus valores como cotización y permitir explícitamente trabajo sin repuestos.
- Mantener comandos y botones como alternativa de entrada.

## Criterios de aceptación

- [ ] Un mensaje completo llega al resumen sin iniciar comando y sin repetir preguntas.
- [ ] Faltantes múltiples se presentan juntos; respuestas parciales se agregan al mismo borrador.
- [ ] No se confunden datos de vehículos existentes, y los datos contradictorios requieren confirmación.
- [ ] Un vehículo nuevo puede completarse en la misma conversación, solicitando los campos obligatorios que falten.
- [ ] Importes inequívocos se interpretan; ambigüedades unitario/total se aclaran antes del cálculo.
- [ ] No se inventan precios, cantidad ni mano de obra. Catálogo es sugerencia explícita; ausencia de repuestos se confirma.
- [ ] El cálculo final continúa usando reglas deterministas en ARS y datos sujetos a validación.

## Límites

No incluye voz, fotos, proveedores automatizados, VPS ni operación multiusuario. No autoriza persistencia de vehículo, presupuesto o catálogo antes de la confirmación.

## Riesgos/pendientes de implementación

- Definir qué campos personales se envían a OpenAI, límites de uso/costo y retención de datos antes de activar solicitudes reales.
- Probar salidas incompletas, inválidas, ambiguas y respuestas no confiables sin aceptar acciones arbitrarias de la IA.
