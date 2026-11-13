# 14: Verificar el recorrido real de Telegram y persistencia

**What to build:** completar y registrar la aceptación manual del flujo base con Telegram real, web, datos persistidos y cuenta no autorizada, sin confundir simulaciones con integración real.

**Blocked by:** 01 — Validar el borrador completo antes de confirmar; 02 — Persistir ediciones y revocar confirmaciones descartadas; 04 — Seleccionar correctamente presupuestos para corregir; 09 — Escapar contenido del usuario en los PDF; 10 — Completar materiales y errores del cierre de trabajo; 12 — Validar límites del período mensual.

**Status:** pending-verification — La spec ya identifica pasos reales pendientes; no se afirma que la integración falle.

**Problema y requisito afectado:** spec base, criterios de recorrido 1–8 y registro manual líneas 99–102; ticket base 01, acceso no autorizado pendiente; ticket base 04, descarga manual pendiente; ticket base 10, aprobación, cierre, resumen y reinicio pendientes. E1–E8 previos fueron simulados/locales.

**Pasos para verificar:** con credenciales autorizadas del usuario y entorno local respaldado, ejecutar alta, presupuesto de dos unidades a ARS 15.000 más ARS 40.000 de mano de obra, recepción PDF, aprobación, cierre con ARS 75.000, consulta mensual, reinicio y acceso desde otra cuenta Telegram.

**Comportamiento actual:** hasta ARS 70.000 y consulta web existe registro previo; aprobación/cierre/resumen/reinicio y cuenta ajena no están acreditados mediante servicio real en esta revisión.

**Comportamiento esperado:** registrar evidencia de cada paso real; una cuenta no autorizada no puede operar; el resumen cuenta ARS 75.000 una sola vez tras reiniciar.

- [ ] Separar en el registro qué pasó por Telegram real, cliente web, DB/PDF en disco y prueba simulada.
- [ ] Completar y registrar cada paso 1–8 de la spec base sin publicar credenciales/datos personales.
- [ ] Probar cuenta Telegram no autorizada y confirmar que no crea ni modifica datos.
- [ ] Confirmar que la descarga web entrega el PDF correcto y restringe acceso anónimo.
- [ ] Tras reiniciar procesos, verificar vehículo, presupuesto, PDF, catálogo y cierre persistidos.
- [ ] Si faltan credenciales o servicio, anotar el bloqueo y mantener el criterio como no verificado, no cumplido.

**Dependencias:** 01, 02, 04, 09, 10, 12.

## Comments

- **2026-11-13 — Verificación local y de conectividad:** `manage.py check`, `makemigrations --check --dry-run` y la suite Django completa (82 pruebas) pasaron. Se consultó `getMe` con el token local y Telegram respondió correctamente; no se inició el polling ni se crearon/modificaron registros. Esto solo acredita conectividad e identidad del bot, no el recorrido funcional real.
- **Bloqueo y pendiente:** las credenciales locales están configuradas y Telegram responde; no falta el servicio. En esta sesión no hay interacción humana disponible con las cuentas autorizada y no autorizada para ejecutar el recorrido, y los tickets bloqueantes 01, 02, 04, 09, 10 y 12 siguen con estado `ready-for-agent`. Por eso permanecen sin verificar el alta/presupuesto/PDF por Telegram, aprobación y cierre en la web, resumen mensual, persistencia tras reiniciar, descarga protegida del PDF y rechazo desde otra cuenta; el ticket queda `pending-verification`.
