# Correcciones de la revisión final del taller

## Objetivo

Corregir errores y requisitos incumplidos confirmados durante la revisión de `1c4178201973cdf5a1a6338eab92c40958217232`, sin ampliar el producto con mejoras opcionales. Los tickets de verificación registran incertidumbres sin afirmar que exista un defecto.

## Fuentes y alcance

- Demo base: [`.scratch/demo-taller/spec.md`](../demo-taller/spec.md).
- Asistente IA: [`.scratch/asistente-ia-presupuestos/spec.md`](../asistente-ia-presupuestos/spec.md).
- Rediseño web: [`.scratch/rediseno-web/spec.md`](../rediseno-web/spec.md).
- Evidencia: revisión reproducible de callbacks, serialización, borradores, validación económica, PDF, formularios, permisos y páginas responsivas.
- No incluye VPS, audio, nuevos roles, una refactorización general ni cambiar flujos que ya cumplen.

## Clasificación

- **Corrección de error:** comportamiento contrario al esperado que fue reproducido.
- **Requisito incumplido:** comportamiento requerido por la especificación que falta o no se puede completar.
- **Pendiente de verificación:** no hay evidencia suficiente para afirmar cumplimiento o defecto; requiere comprobación y registro.

## Plan de tickets

Los tickets 01–12 corrigen errores o requisitos incumplidos. El ticket 13 registra un pendiente de verificación de aislamiento de archivos de pruebas, no afirma un defecto confirmado. Los tickets 14–15 son verificaciones externas/manuales y no declaran fallos por anticipado.

1. [01 — Validar el borrador completo antes de confirmar](issues/01-validar-borrador-antes-de-confirmar.md)
2. [02 — Persistir ediciones y revocar confirmaciones descartadas](issues/02-persistir-y-descartar-borradores.md)
3. [03 — Enviar solo el mensaje actual a OpenAI](issues/03-aislar-solicitud-openai.md)
4. [04 — Seleccionar correctamente presupuestos para corregir](issues/04-seleccion-corregir-presupuestos.md)
5. [05 — Aplicar correcciones parciales sin perder datos](issues/05-correcciones-parciales.md)
6. [06 — Continuar el borrador por el flujo guiado](issues/06-continuar-borrador-manualmente.md)
7. [07 — Completar el flujo de presupuesto por lenguaje natural](issues/07-flujo-natural-y-catalogo.md)
8. [08 — Corregir presupuestos pendientes mediante lenguaje natural](issues/08-correccion-natural-versiones.md)
9. [09 — Escapar contenido del usuario en los PDF](issues/09-escapar-texto-pdf.md)
10. [10 — Completar materiales y errores del cierre de trabajo](issues/10-formulario-cierre.md)
11. [11 — Corregir accesibilidad y diseño responsive](issues/11-responsive-y-contraste.md)
12. [12 — Validar límites del período mensual](issues/12-limites-periodo-mensual.md)
13. [13 — Verificar aislamiento del almacenamiento en pruebas](issues/13-verificar-aislamiento-pruebas.md)
14. [14 — Verificar el recorrido real de Telegram y persistencia](issues/14-verificacion-telegram-persistencia.md)
15. [15 — Verificar extracción con OpenAI real](issues/15-verificacion-openai-real.md)

Los tickets de corrección se consideran nuevas tareas. Los tickets originales y su registro histórico no se reemplazan ni se modifican.
