# 09: Buscar y filtrar historiales

**Objetivo / Qué construir:** permitir al administrador localizar registros por fecha, patente y tipo de cliente y navegar desde los resultados al historial del vehículo y al detalle del presupuesto.

**Blocked by:** 03 — Preparar y confirmar presupuestos.

**Status:** implementation-complete; automated tests cover combined filters, validation, clearing, and empty results

**Referencia:** [Gestión web e historial](../spec.md#gestión-web-e-historial); [Criterios complementarios](../spec.md#criterios-complementarios), filtros por fecha, patente y tipo de cliente.

## Alcance de la sesión

- Incorporar controles de búsqueda y filtrado en los listados web del historial de presupuestos.
- Permitir combinar y limpiar filtros y acceder al vehículo o presupuesto encontrado.
- Mostrar los resultados sin perder la asociación de cada presupuesto a su vehículo y cliente.

## Criterios de aceptación

- [x] Buscar por patente permite encontrar el vehículo y acceder a su historial, sin distinguir mayúsculas de minúsculas.
- [x] Filtrar por Municipalidad o particular devuelve exclusivamente los registros del tipo seleccionado.
- [x] El filtro de fechas se identifica como fecha del presupuesto y permite un intervalo inclusivo de inicio y fin.
- [x] Combinar fecha, patente y tipo de cliente devuelve la intersección de las condiciones, no la unión.
- [x] Un intervalo inválido muestra una indicación corregible; una búsqueda sin coincidencias muestra un estado vacío comprensible.
- [x] Limpiar los filtros restaura el listado completo al que tiene acceso el administrador.
- [x] Cada resultado permite consultar el detalle del presupuesto y el historial del vehículo, incluyendo enlaces a PDFs disponibles.
- [x] Las pruebas automatizadas cubren combinación, extremos del intervalo, datos que no coinciden, limpieza y patente sin distinción de formato.

## Límites

No incluye exportación de datos, búsqueda inteligente ni análisis estadístico. La selección de mes del resumen de cobros se incorpora en el ticket 10.

## Implementación

- El dashboard protegido combina los filtros de patente, tipo de cliente y fecha del presupuesto; conserva enlaces al historial del vehículo.
- `tallerweb/tests.py` verifica filtros combinados, fechas inclusivas, entrada inválida, limpieza, búsqueda de patente y estado sin resultados. No se declara una verificación manual adicional.
