# 03: Preparar y confirmar presupuestos

**Objetivo / Qué construir:** completar desde Telegram un presupuesto con precios manuales, revisar y corregir su resumen, confirmarlo y consultar el resultado persistido en el historial web del vehículo.

**Blocked by:** 02 — Registrar y consultar vehículos.

**Status:** implementation-complete; real Telegram budget flow verified

**Referencia:** [Flujo para crear un presupuesto](../spec.md#flujo-para-crear-un-presupuesto), pasos 3–6; [Cálculo y precios](../spec.md#cálculo-y-precios); [Gestión web e historial](../spec.md#gestión-web-e-historial); [Criterios complementarios](../spec.md#criterios-complementarios).

## Alcance de la sesión

- Cargar descripción del trabajo, uno o más ítems de repuestos con cantidad y precio, e importe total de mano de obra.
- Mostrar un resumen editable antes de confirmar.
- Guardar el presupuesto confirmado con número, fecha, detalle económico y asociación al vehículo y cliente.
- Incorporar su consulta al historial web. La entrega del PDF corresponde al ticket 04.

## Criterios de aceptación

- [x] El mecánico completa el presupuesto con botones y texto, ingresando manualmente los precios consultados por WhatsApp.
- [x] Puede agregar varios repuestos y revisar y corregir los datos cargados antes de confirmar.
- [x] El resumen muestra cantidades, precios unitarios, subtotales, mano de obra y total en ARS.
- [x] Dos unidades a ARS 15.000 más ARS 40.000 de mano de obra producen exactamente ARS 70.000, sin cargos adicionales.
- [x] Los cálculos con centavos conservan la precisión monetaria; cantidades no positivas e importes negativos o no numéricos se rechazan con una indicación corregible.
- [x] Confirmar registra un presupuesto pendiente con número y fecha; volver a procesar la misma confirmación no genera presupuestos duplicados.
- [x] El administrador consulta el presupuesto y su desglose en el historial del vehículo, también después de reiniciar la aplicación.
- [x] Los datos económicos confirmados quedan conservados como valores propios del presupuesto, sin depender de futuros cambios del catálogo.
- [x] Se verifican el cálculo del caso principal, un caso con centavos, la corrección previa y la confirmación sin duplicados.

## Implementación

- `Budget` y `BudgetItem` guardan el presupuesto pendiente, los importes decimales y el desglose propio de cada presupuesto. La confirmación usa una clave idempotente y asigna número secuencial.
- `/presupuesto` guía la carga por Telegram; `/listo` termina la carga de repuestos; el resumen ofrece corrección de descripción, repuestos y mano de obra antes de confirmar. `/cancelar` abandona el borrador.
- El historial del vehículo en la web protegida muestra los presupuestos y su detalle económico.
- Verificación local: `manage.py test` (18 pruebas), `manage.py check` y `makemigrations --check --dry-run`. El flujo real de creación y confirmación por Telegram también se verificó manualmente (ver Comments).

## Límites

No automatizar consultas a proveedores ni incorporar tarifas por horas, impuestos, descuentos o márgenes. La mano de obra es un importe manual para ambos tipos de cliente.

## Comments

- Verificación manual real: se confirmó por Telegram el presupuesto P-000001 para AB123CD, con dos unidades a ARS 15.000 y ARS 40.000 de mano de obra; el PDF muestra un total de ARS 70.000. El usuario confirmó que el presupuesto también se ve correctamente en la web.
