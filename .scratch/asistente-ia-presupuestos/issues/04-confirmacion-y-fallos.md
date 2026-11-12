# 04: Confirmación y manejo de fallos

**Objetivo / Qué construir:** asegurar que solo el resumen actual pueda confirmar y que la indisponibilidad de IA no descarte el trabajo ya ingresado.

**Status:** spec-ready

**Referencia:** [Especificación del asistente IA](../spec.md), reglas y criterios 8–11.

## Alcance

- Separar interpretación de validación, cálculo y persistencia.
- Exigir confirmación explícita del resumen vigente para generar el presupuesto/PDF.
- Invalidar botones/respuestas de confirmación anteriores a cualquier modificación del borrador.
- Mantener idempotencia y permitir reintento de entrega del PDF ya existente.
- Gestionar timeout, error de API y respuesta no estructurada mediante aviso, reintento o flujo manual existente.
- Incorporar efectos secundarios (alta de vehículo y actualización del catálogo) en la operación de confirmación, evitando guardarlos al descartar.

## Criterios de aceptación

- [ ] No se persiste presupuesto ni se genera PDF antes de la confirmación explícita.
- [ ] Un botón obsoleto no confirma la versión nueva del borrador.
- [ ] Repetir confirmación no duplica presupuesto/versión, PDF ni escrituras de catálogo.
- [ ] El error/timeout de IA conserva el borrador y ofrece reintentar o seguir con el flujo guiado.
- [ ] El total se recalcula mediante reglas de dominio; datos inválidos se rechazan con pregunta corregible.
- [ ] Alta de vehículo y cambios de catálogo ocurren solo al confirmar, de forma coherente con el presupuesto confirmado.
