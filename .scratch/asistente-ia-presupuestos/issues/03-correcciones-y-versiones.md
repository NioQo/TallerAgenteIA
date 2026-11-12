# 03: Corregir versiones y preservar compatibilidad

**Objetivo / Qué construir:** habilitar correcciones por lenguaje natural de un borrador o de la versión vigente de un presupuesto pendiente, preservando todas las versiones confirmadas y permitiendo que la vigente continúe el ciclo administrativo.

**Status:** spec-ready

**Referencia:** [Especificación del asistente IA](../spec.md), reglas y criterios 6, 10 y 11; [ticket base 06](../../demo-taller/issues/06-corregir-mediante-nuevas-versiones.md); [ticket base 07](../../demo-taller/issues/07-aprobar-o-rechazar-presupuestos.md); [ticket base 08](../../demo-taller/issues/08-registrar-trabajo-terminado.md).

## Alcance

- Aplicar correcciones parciales únicamente a los campos mencionados y volver a mostrar resumen.
- Encontrar presupuestos pendientes por número; validar que la versión seleccionada sea la vigente.
- Corregir la selección defectuosa de presupuesto en `/corregir` identificada en el código existente.
- Corregir las acciones web que hoy bloquean aprobar y cerrar una versión vigente solo porque tiene una versión anterior.
- Mantener las reglas: solo presupuesto pendiente admite revisión; solo vigente admite decisión/cierre; versiones anteriores siguen consultables e inmutables.

## Criterios de aceptación

- [ ] “Cambiá la mano de obra a 60 mil” conserva ítems y demás datos.
- [ ] La selección de presupuesto corregible obtiene el registro por su identificador correcto y ofrece su versión vigente.
- [ ] Confirmar una revisión crea nueva versión/PDF y no cambia versión ni PDF previos.
- [ ] La versión vigente corregida puede aprobarse o rechazarse; solo aprobada puede cerrarse.
- [ ] Una histórica, rechazada, aprobada o terminada no admite revisión ni acciones de una versión independiente.
- [ ] Los datos ya existentes siguen visibles en historial y descarga.

## Límites

No agrega reapertura, fusión de versiones ni edición de presupuestos aprobados/rechazados/terminados.
