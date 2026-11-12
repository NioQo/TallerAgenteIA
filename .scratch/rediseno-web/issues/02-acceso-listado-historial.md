# 02: Rediseñar acceso, listado e historial

**Objetivo / Qué construir:** aplicar el nuevo sistema visual a login, dashboard con filtros e historial del vehículo sin alterar los flujos.

**Status:** spec-ready

**Blocked by:** 01 — Identidad visual y estructura compartida.

**Referencia:** [Especificación del rediseño web](../spec.md), compatibilidad funcional y criterios 1–6.

## Criterios de aceptación

- [ ] Login mantiene autenticación, mensajes de error y navegación de retorno.
- [ ] Dashboard conserva filtros combinados, fecha, patente, tipo de cliente, limpieza y estado vacío.
- [ ] Se mantienen acceso a vehículos, historial, versiones y descarga de cada PDF disponible.
- [ ] El historial presenta con claridad estado, versión vigente/histórica, importes y acciones permitidas.
- [ ] Formularios de aprobación, rechazo y cierre conservan POST, CSRF y condiciones de estado.
- [ ] Layout usable con teclado y a tamaños de computadora y móvil.

## Límites

No cambia reglas, datos, rutas, permisos ni estados.
