# 10: Completar materiales y errores del cierre de trabajo

**What to build:** registrar cualquier cantidad de repuestos utilizados y permitir corregir errores del formulario de cierre antes de confirmar el trabajo.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Error reproducido y requisito de la interfaz incumplido P2.

**Problema y requisito afectado:** la pantalla solo ofrece una fila para agregar un material adicional. Con importe inválido, la vista redirige sin error visible ni conservación de campos. Incumple spec base, gestión web, criterio 62; spec web, accesibilidad 15, criterios 3 y 5; ticket base 08, criterio 1; ticket web 02, criterios 5–6.

**Pasos para reproducir:** cerrar un trabajo agregando más de un repuesto nuevo; luego volver a enviar con importe no numérico o cantidad inválida.

**Comportamiento actual:** no hay controles para añadir múltiples filas nuevas; la entrada inválida redirige silenciosamente.

**Comportamiento esperado:** poder editar la lista completa de materiales y ver qué campo debe corregirse sin perder valores válidos.

- [ ] La interfaz permite añadir/quitar varias filas de materiales en un único cierre.
- [ ] La cantidad puede ser positiva para cada material; nombres vacíos se manejan explícitamente.
- [ ] Importe/cantidad inválidos muestran mensajes asociados y conservan los demás campos enviados.
- [ ] La validación no crea trabajo parcial y solo aprobados pueden cerrarse.
- [ ] Repetir un cierre válido sigue siendo idempotente y no modifica presupuesto ni PDF.
- [ ] Pruebas de navegador y servidor para cero/varios materiales, valores inválidos, CSRF, permisos, estado y repetición.

**Dependencias:** Ninguna.
