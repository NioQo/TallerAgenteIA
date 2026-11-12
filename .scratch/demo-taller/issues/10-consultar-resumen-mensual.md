# 10: Consultar el resumen mensual

**Objetivo / Qué construir:** mostrar al administrador cuántos trabajos se terminaron y cuánto se cobró en un mes, utilizando los cierres reales y evitando sumar presupuestos o versiones como ingresos adicionales.

**Blocked by:** 08 — Registrar el trabajo terminado.

**Status:** implementation-complete; recorrido real parcialmente verificado, cierre y resumen mensual pendientes

**Referencia:** [Gestión web e historial](../spec.md#gestión-web-e-historial); [Recorrido principal](../spec.md#recorrido-principal), pasos 1–8, especialmente el resumen sin doble conteo del paso 7.

## Alcance de la sesión

- Incorporar una vista web de resumen con selección de mes y año.
- Mostrar cantidad de trabajos terminados y suma del importe final cobrado en ARS.
- Usar la fecha de cierre del trabajo para la agrupación mensual y explicitarlo en la pantalla.
- Verificar el recorrido principal completo que queda habilitado por la cadena de dependencias de este ticket.

## Criterios de aceptación

- [x] El administrador selecciona un mes y año y obtiene la cantidad de trabajos terminados y el total cobrado correspondientes a ese período.
- [x] Se incluyen solamente cierres con fecha dentro del mes seleccionado; pendientes, aprobados sin cierre y rechazados no aportan cobros.
- [x] Un trabajo presupuestado en ARS 70.000 y terminado con ARS 75.000 cobrados aporta un trabajo y ARS 75.000, nunca ARS 145.000.
- [x] Las versiones anteriores no se cuentan como trabajos ni importes cobrados adicionales.
- [x] Un mes sin cierres muestra cero trabajos y ARS 0; los límites entre meses se asignan correctamente.
- [x] La consulta se basa en cierres persistidos en SQLite y permanece estable al reiniciar.
- [x] Se verifican con datos controlados la suma, exclusiones, límites mensuales y ausencia de doble conteo.
- [ ] Se ejecuta y registra el recorrido principal de la especificación: alta por Telegram, presupuesto de ARS 70.000, recepción del PDF, aprobación web, cierre de ARS 75.000, consulta mensual y comprobación tras reiniciar.

## Límites

No incluye gráficos avanzados, predicciones ni rentabilidad. Los filtros generales del ticket 09 y las sugerencias de catálogo del ticket 05 son ramas independientes y no bloquean este resumen.

## Implementación

- La pantalla protegida `/resumen-mensual/` permite elegir mes y año. Se accede desde el inicio web.
- El resumen agrupa por `CompletedWork.closed_at` (fecha de cierre local) y suma exclusivamente `CompletedWork.final_amount`; cada cierre representa un trabajo, sin consultar totales ni versiones de presupuesto.
- Pruebas: `manage.py test` (34 pruebas), `manage.py check` y `makemigrations --check --dry-run` pasan.
- El recorrido real se verificó hasta crear y consultar en web un presupuesto de ARS 70.000 y recibir su PDF. Quedan pendientes la aprobación web, el cierre por ARS 75.000, la consulta del resumen mensual y la comprobación tras reiniciar; las pruebas automáticas no sustituyen esos pasos manuales.
