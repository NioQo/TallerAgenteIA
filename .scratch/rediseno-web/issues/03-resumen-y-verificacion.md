# 03: Rediseñar resumen mensual y verificar responsive

**Objetivo / Qué construir:** completar la presentación profesional del resumen mensual y revisar de punta a punta las cuatro pantallas y los flujos existentes.

**Status:** spec-ready

**Blocked by:** 01 — Identidad visual y estructura compartida.

**Referencia:** [Especificación del rediseño web](../spec.md), compatibilidad funcional y criterios 1–6; [Demo base, verificación manual](../../demo-taller/spec.md#registro-de-verificación-manual).

## Criterios de aceptación

- [x] El resumen mensual conserva selector de período, cantidad de trabajos, total cobrado y explicación de la fecha de cierre.
- [x] Cero resultados y errores de entrada se muestran claramente.
- [ ] Login, dashboard, historial y resumen se prueban a anchos móvil y escritorio sin desbordamiento horizontal.
- [x] Se verifica autenticación, filtros, navegación a historial, descarga, decisión y cierre de trabajo mediante pruebas automatizadas.
- [x] Se comprueba que importes, estados y datos presentados no cambiaron respecto del comportamiento base mediante pruebas automatizadas.
- [x] Las verificaciones registradas distinguen pruebas automatizadas de pruebas manuales y no marcan como completo el recorrido financiero base aún pendiente.

## Verificación

- **Automatizada:** `MonthlySummaryTests` valida cantidades e importes finales por mes, límites de período, cero resultados, autenticación, parámetro inválido y presentación del resumen. La suite completa pasó (48 pruebas) y `manage.py check` no reportó problemas.
- **Manual con navegador:** la pantalla de acceso se abrió a 390 px y no mostró desbordamiento horizontal. No se pudo verificar visualmente el resto de las pantallas ni los flujos autenticados porque el navegador no disponía de sesión; no se alteró la base local para crear una. La prueba responsive de las cuatro pantallas queda pendiente.
- **Recorrido financiero real:** continúa pendiente aprobar, cerrar el trabajo con ARS 75.000, verificar el resumen y persistencia tras reiniciar, según el registro manual de la especificación base. Las pruebas automatizadas existentes no se presentan como prueba manual.

## Límites

No incluye `/admin/`, PDF, VPS ni implementación de funciones de negocio.
