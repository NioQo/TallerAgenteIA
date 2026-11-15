# 09: Escapar contenido del usuario en los PDF

**What to build:** imprimir literalmente los datos de cliente, vehículo, trabajo y repuestos aunque incluyan caracteres especiales, sin romper ni alterar el contenido del PDF.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Corrección de error P2.

**Problema y requisito afectado:** la revisión produjo un `ValueError` de ReportLab con la descripción `Reparacion <b>`. La spec base exige esos datos en el PDF (sección PDF, líneas 45–53) y la aceptación complementaria 5–6.

**Pasos para reproducir:** confirmar presupuesto con descripción o repuesto que contenga `<b>`, `&`, `<` o `>`.

**Comportamiento actual:** texto con marcado incompleto impide generar el PDF; marcas válidas pueden interpretarse como formato.

**Comportamiento esperado:** el PDF se genera y muestra esos caracteres como texto del usuario, no como instrucciones de marcado.

- [ ] Escapar contenido dinámico en todos los párrafos/celdas renderizados.
- [ ] El caso `Reparacion <b>` produce PDF sin excepción y conserva el texto visible literal.
- [ ] Probar ampersand, corchetes angulares y marcas válidas en cliente, vehículo, descripción y repuestos.
- [ ] Confirmar que número, importes, paginación y contenido de presupuestos normales siguen sin cambios.

**Dependencias:** Ninguna.
