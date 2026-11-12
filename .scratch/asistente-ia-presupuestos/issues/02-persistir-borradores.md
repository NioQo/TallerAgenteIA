# 02: Persistir y recuperar borradores

**Objetivo / Qué construir:** permitir que la cuenta autorizada retome un presupuesto en preparación después de un reinicio, sin convertir el borrador en presupuesto emitido.

**Status:** implemented

**Referencia:** [Especificación del asistente IA](../spec.md), alcance y criterios 7, 8 y 11; [Glosario: Borrador de presupuesto](../../../GLOSSARY.md#borrador-de-presupuesto).

## Alcance

- Mantener como máximo un borrador activo para la única cuenta autorizada de la demo.
- Ofrecer continuar o descartar al reanudar la interacción.
- Conservar respuestas parciales, datos detectados y estado de preguntas pendientes.
- Manejar limpieza/expiración y datos transmitidos a la API de acuerdo con la definición operativa que se cierre antes de implementar.

## Criterios de aceptación

- [x] Tras reiniciar el proceso, la cuenta puede retomar el borrador y sus preguntas pendientes.
- [x] Descartar elimina el borrador sin crear vehículo, presupuesto, versión, PDF ni cambios de catálogo.
- [x] Iniciar una operación nueva no borra silenciosamente un borrador existente.
- [x] El borrador no aparece en el historial de presupuestos ni en el resumen mensual.
- [x] La persistencia evita exponer el borrador a cuentas de Telegram no autorizadas.

## Límites

No incluye varios usuarios, borradores concurrentes por cuenta, ni persistencia de historial conversacional completo salvo que se acuerde después.

## Comments

- Definición operativa acordada antes de implementar: el borrador expira 30 días después de su última modificación; descartarlo elimina inmediatamente sus datos locales; a OpenAI se envía únicamente el mensaje entrante, nunca el borrador previo. La base local conserva el borrador estructurado hasta que se confirme, descarte o expire.
- Implementado en SQLite como registro separado de presupuestos, con recuperación y descarte desde Telegram. La limpieza de vencidos se realiza al consultar el borrador.
