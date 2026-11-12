# 05: Reutilizar precios del catálogo

**Objetivo / Qué construir:** reutilizar desde Telegram los precios de repuestos ingresados en presupuestos anteriores, permitiendo confirmarlos o reemplazarlos sin modificar documentos previos.

**Blocked by:** 03 — Preparar y confirmar presupuestos.

**Status:** implementation-complete; real Telegram verification pending user credentials

**Referencia:** [Flujo para crear un presupuesto](../spec.md#flujo-para-crear-un-presupuesto), paso 4; [Cálculo y precios](../spec.md#cálculo-y-precios); [Criterios complementarios](../spec.md#criterios-complementarios), sugerencias y conservación de precios.

## Alcance de la sesión

- Guardar repuestos y precios ingresados para reutilización posterior.
- Permitir seleccionar un repuesto existente o ingresar uno nuevo desde el bot.
- Mostrar el precio guardado como sugerencia explícita que se puede aceptar o cambiar.

## Criterios de aceptación

- [x] Un repuesto ingresado con precio manual queda disponible en el catálogo y puede seleccionarse al preparar otro presupuesto.
- [x] El bot presenta el precio guardado como sugerencia, no como una cotización actual garantizada por el proveedor.
- [x] El mecánico puede aceptar la sugerencia o ingresar otro precio; el resumen usa el valor elegido.
- [x] Tras registrar un repuesto a ARS 15.000 y luego actualizarlo a ARS 18.000, un presupuesto posterior puede usar ARS 18.000 mientras el anterior conserva ARS 15.000.
- [x] Cambiar el catálogo no modifica totales ni detalles de presupuestos ya confirmados y tampoco sus PDFs.
- [x] El catálogo y sus precios siguen disponibles después de reiniciar la aplicación (persistencia en SQLite).
- [x] Se verifica la sugerencia, su reemplazo y la conservación de los precios históricos.

## Implementación

- `PartCatalog` persiste un precio sugerido por repuesto; se consulta sin distinguir mayúsculas y minúsculas y se actualiza al ingresar un precio elegido.
- En `/presupuesto`, tras indicar nombre y cantidad, el bot permite aceptar la sugerencia o cambiarla. Para repuestos nuevos solicita el precio manual, que se registra en el catálogo.
- Los presupuestos confirmados y sus PDF conservan los importes originales; el catálogo no se usa para recalcular documentos existentes.
- Verificación local: `manage.py test` (22 pruebas), `manage.py check` y `makemigrations --check --dry-run`. La prueba con Telegram real requiere credenciales configuradas localmente.

## Límites

No incluye stock, compras, comparación de proveedores, consultas automáticas ni un panel independiente de administración del catálogo. Se puede completar sin esperar al ticket 04, comprobando la conservación del presupuesto persistido.
