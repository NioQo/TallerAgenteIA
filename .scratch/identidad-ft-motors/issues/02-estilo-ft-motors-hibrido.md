# 02: Estilo FT MOTORS híbrido

**Objetivo / Qué construir:** restilizar las cuatro pantallas con la estética de FT MOTORS en el modo híbrido por defecto (marco oscuro, contenido claro).

**Status:** done — implementado en el repo (commit `6968279`) y verificado en el PC (ver [ticket 04](04-verificacion-y-regresiones.md)).

**Blocked by:** None (puede avanzar en paralelo con el 01; el logotipo y los textos dependen de su fuente central).

**Referencia:** [Especificación](../spec.md), secciones "Alcance" y "Compatibilidad funcional".

## Alcance

- Encabezado, navegación, pie y pantalla de acceso en negro/grafito, con logotipo cromado y acentos rojos; líneas diagonales rojas y degradados como recurso gráfico. Sin fotos.
- Contenido (listados, historial, formularios, resumen) sobre fondo gris claro con tarjetas blancas.
- Barlow Condensed (OFL) incluida en el proyecto, sin CDN, para títulos, logotipo y navegación en mayúsculas; fuente actual para texto, formularios, tablas e importes con cifras tabulares.
- Botones principales en rojo con texto blanco; secundarios y "Rechazar" en grafito o con contorno.
- Errores con borde lateral, ícono y texto "Error:"; estados de presupuesto sin rojo y con contraste suficiente.
- Reemplaza la paleta azul/naranja del rediseño web anterior.

## Criterios de aceptación

- [x] Las cuatro pantallas comparten estructura, componentes, paleta y tipografía coherentes.
- [x] Texto normal alcanza 4,5:1; controles y texto grande alcanzan los umbrales WCAG; el foco es visible sobre superficies claras y oscuras. (Texto mínimo medido 4,97:1; no se midieron componentes no textuales ni estados hover.)
- [x] Estados y errores se distinguen por texto o forma además del color. (Errores con borde lateral, ícono y "Error:".)
- [x] Las fuentes se sirven desde archivos locales; no hay solicitudes a servicios externos. (0 solicitudes externas.)
- [x] A 320 px no hay desplazamiento horizontal.

## Límites

No incluye modo oscuro (ticket 03), `/admin/` ni el diseño del PDF.
