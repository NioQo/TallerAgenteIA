# 04: Verificación y regresiones

**Objetivo / Qué construir:** comprobar que la identidad real, el estilo y el modo oscuro cumplen los criterios de la ampliación sin regresiones funcionales.

**Status:** spec-ready

**Blocked by:** [01](01-identidad-central-ft-motors.md), [02](02-estilo-ft-motors-hibrido.md) y [03](03-modo-oscuro.md).

**Referencia:** [Especificación](../spec.md), criterios de aceptación 1–5.

## Criterios de aceptación

- [x] La suite Django completa y `manage.py check` pasan.
- [x] Navegador: las cuatro pantallas, en modo híbrido y oscuro, a 320, 390, 768 px y escritorio, sin desplazamiento horizontal, con contraste 4,5:1 en texto normal y foco visible; se registran viewport y métricas.
- [~] Botón de modo: cambia, persiste tras recargar y cerrar sesión, funciona con teclado y sin parpadeo. **Parcial:** el reinicio real del navegador no se probó (ver registro).
- [x] Inicio y cierre de sesión, filtros, historial, versiones, descargas, aprobación y rechazo, cierre de trabajo y resumen mensual se comportan igual; sin cambios en URLs, permisos, CSRF ni importes. (Descarga y versiones: solo pruebas automatizadas.)
- [x] Un presupuesto nuevo sale con la identidad de FT MOTORS; un PDF ya emitido descargado desde el historial sigue siendo el original. (Solo pruebas automatizadas.)
- [x] El registro distingue pruebas automatizadas de verificaciones manuales y no declara completo lo que no se probó.

## Registro de verificación (2026-11-14)

### Pruebas automatizadas
- `manage.py check`: sin incidencias. `manage.py test`: 99 pruebas OK.
- Identidad en web (`tests.py` ~77–99, sin "Taller Norte") y en PDF nuevo (~1383–1386, con "FT MOTORS", sin "TALLER DEMO").
- PDF emitido intacto tras revisar y descargar desde el historial (~1156–1170, ~1400–1417).

### Verificaciones manuales en navegador (Playwright, BD temporal con datos ficticios, no la real)
- **Pantallas:** acceso, vehículos, historial del vehículo y resumen mensual; modos híbrido y oscuro; 320×700, 390×800, 768×900 y 1280×900 (32 combinaciones).
- **Desplazamiento horizontal:** ninguno en las 32 combinaciones (`scrollWidth <= innerWidth`).
- **Recursos externos:** 0 solicitudes a otros orígenes (fuentes locales).
- **Contraste de texto (calculado con el DOM, tomando el peor tramo de cada degradado):** mínimo 4,97:1 (separador decorativo del pie, 14,4 px) en ambos modos. El logotipo `.brand-mark` (degradado con `background-clip:text`, `aria-hidden`) se excluyó por ser logotipo. No se midió contraste de componentes no textuales (bordes, íconos) ni de estados hover.
- **Foco:** anillo de 3 px oscuro más halo blanco de 5 px, visible en ambos modos (se probó con Tab en el menú).
- **Botón de modo:** cambia a oscuro y a claro; texto e ícono indican la acción siguiente; anuncia el estado por `role=status`; persiste tras recargar y tras cerrar e iniciar sesión (`localStorage`); funciona con Enter y Espacio; sin preferencia guardada sigue `prefers-color-scheme`.
- **Parpadeo:** solo verificación por orden en el HTML (el script que fija `data-theme` va antes de la primera hoja de estilos). No se midió con capturas del primer fotograma.
- **Flujos:** filtros (con y sin resultados), rechazo, cierre de trabajo (ARS 1700 cobrado sobre ARS 1500 presupuestado) y resumen mensual (1 trabajo, ARS 1700,00) coinciden con lo esperado. Formularios con CSRF y mismas URLs; un POST sin token devuelve 403.

### No verificado
- Reinicio real del navegador: `localStorage` persiste por diseño, pero no se cerró y reabrió el navegador.
- Descarga de PDF y versiones de presupuesto desde el navegador (el dato ficticio no tenía PDF, 404 esperado); solo cubiertos por pruebas automatizadas.
- Sin lector de pantalla real; la accesibilidad del estado se comprobó solo por el atributo `role=status` y el texto anunciado.
- Navegador único (Chromium de Playwright).

### Incidente
Durante la preparación, un error de escape hizo que un comando creara el superusuario `verif` en la BD real. Se comprobó que fue la única escritura (vehículos y presupuestos sin cambios) y se eliminó de inmediato. Usuarios actuales: `Nio`, `NioQ`.
