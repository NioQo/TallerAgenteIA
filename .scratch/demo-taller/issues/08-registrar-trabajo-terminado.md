# 08: Registrar el trabajo terminado

**Objetivo / Qué construir:** cerrar desde la web un trabajo aprobado, confirmar o corregir los repuestos efectivamente utilizados y registrar el importe final cobrado, conservando el presupuesto aprobado.

**Blocked by:** 07 — Aprobar o rechazar presupuestos.

**Status:** done

**Referencia:** [Gestión web e historial](../spec.md#gestión-web-e-historial); [Recorrido principal](../spec.md#recorrido-principal), pasos 5–6 y 8; [Glosario: Trabajo e Importe final cobrado](../../../GLOSSARY.md#trabajo).

## Alcance de la sesión

- Ofrecer un cierre para trabajos con presupuesto aprobado.
- Partir del detalle presupuestado para confirmar o corregir materiales realmente utilizados, incluyendo cantidades.
- Guardar el importe final cobrado, la fecha de cierre y el estado trabajo terminado.
- Mostrar por separado el presupuesto aprobado y los datos de ejecución y cobro.

## Criterios de aceptación

- [x] El administrador puede finalizar un trabajo aprobado, confirmar materiales sin cambios o agregar, quitar y corregir los utilizados.
- [x] El importe final cobrado se ingresa explícitamente en ARS y puede diferir del total presupuestado; valores negativos o no numéricos no se aceptan.
- [x] El cierre cambia el estado a trabajo terminado y registra la fecha para su posterior consulta mensual.
- [x] Un presupuesto de ARS 70.000 puede cerrarse con ARS 75.000 cobrados: el historial presenta ambos valores claramente diferenciados.
- [x] Los materiales del cierre pueden diferir de los presupuestados sin alterar ninguna versión ni PDF del presupuesto.
- [x] Un presupuesto pendiente o rechazado no permite registrar un cierre como trabajo terminado.
- [x] Repetir la misma solicitud de cierre no crea otro trabajo ni otro cobro para el mismo presupuesto.
- [x] Los datos del cierre se conservan después de reiniciar la aplicación mediante persistencia en base de datos.
- [x] Se verifican la diferencia entre presupuesto y cierre, la conservación de los materiales originales y el cierre sin duplicados.

## Límites

La demo registra un importe final cobrado al terminar el trabajo. No incluye pagos parciales, cuentas corrientes, conciliación ni facturación. La fecha de cierre permite agrupar los registros en el resumen mensual del ticket 10.
