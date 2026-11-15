# Identidad FT MOTORS y modo oscuro en la web del taller

## Objetivo

Reemplazar la identidad ficticia temporal ("Taller Norte" en la web, "TALLER DEMO" en los PDF) por la identidad real de FT MOTORS, y restilizar el panel interno con la estética del taller (negro/grafito, cromo y rojo), con un botón para alternar entre un modo híbrido y un modo oscuro completo.

Esta ampliación es independiente del trabajo ya completado: la demo base ([Demo de presupuestos para taller](../demo-taller/spec.md)), el asistente de Telegram ([Asistente IA para presupuestos](../asistente-ia-presupuestos/spec.md)), el [rediseño web anterior](../rediseno-web/spec.md) (implementado, con dirección visual azul y naranja que esta ampliación **reemplaza**) y las [correcciones de revisión final](../correcciones-revision-final/spec.md). No afirma que esté implementada.

## Referencia visual

Cartel del taller en Google Maps: fondo negro, logotipo cromado en cursiva pesada con silueta de pickup, acento rojo, íconos de línea blancos y tipografía en mayúsculas espaciadas.

## Identidad del taller

Se centraliza en un único lugar, usado por la web y por el PDF, y reemplazable sin tocar cada pantalla:

- **Nombre:** FT MOTORS
- **Lema** (reemplaza "Servicio automotor"): "Tu vehículo en manos expertas"
- **Teléfono / WhatsApp:** +54 9 11 5429 6017
- **Dirección:** Av. Dardo Rocha 1891 (Ruta 25), Pilar, Buenos Aires
- **Logotipo:** de texto "FT MOTORS", mayúsculas, cursiva pesada, efecto plateado/cromado. El archivo real del logo (SVG o PNG transparente) está pendiente; debe poder sustituirse en un solo lugar.
- No se agregan datos fiscales (CUIT, IVA), email, horarios ni redes: el PDF es un presupuesto, no una factura.

## Alcance

- Restilizar las cuatro pantallas propias del panel interno: acceso, inicio/listado y filtros, historial del vehículo/presupuestos, resumen mensual.
- Aplicar la identidad real al encabezado, pie, título y acceso de la web, y al encabezado de los PDF **nuevos**.
- **Modo híbrido (por defecto):** encabezado, navegación, pie y pantalla de acceso en negro/grafito con logotipo cromado y acentos rojos; contenido sobre fondo gris claro con tarjetas blancas.
- **Modo oscuro completo:** fondo grafito/negro en todas las pantallas, tarjetas gris oscuro y texto claro.
- **Botón de modo:** en la navegación, visible en todas las pantallas incluida la de acceso, con texto e ícono del modo al que se pasa ("Modo oscuro" / "Modo claro"). La primera vez sigue la preferencia del sistema; sin preferencia, arranca en híbrido. La elección se recuerda en el navegador (no en la base de datos ni por usuario), sobrevive al cierre de sesión y al reinicio, y no produce parpadeo del modo equivocado al cargar.
- **Tipografía:** Barlow Condensed (licencia OFL) para títulos, logotipo y navegación, en mayúsculas; cursiva solo en logotipo y títulos grandes. Texto, formularios, tablas e importes mantienen la fuente legible actual con cifras tabulares. Los archivos de fuente se incluyen en el proyecto; no se cargan desde CDN ni servicios externos.
- **Sin fotos:** el estilo se recrea con degradados, líneas diagonales rojas, brillo cromado y, como máximo, íconos de línea simples.
- **Color:** rojo FT MOTORS en las acciones principales (Ingresar, Filtrar, Aprobar, Registrar cierre), con texto blanco y contraste mínimo de 4,5:1 en ambos modos. Acciones secundarias y "Rechazar" en grafito o con contorno. Errores en rojo, distinguibles también por forma (borde lateral, ícono y texto "Error:"). Estados de presupuesto conservan sus códigos (pendiente ámbar, aprobado verde, rechazado gris, trabajo terminado azul), ajustados para contrastar en ambos modos; el rojo no se usa para ningún estado.

## Compatibilidad funcional

- Mantener autenticación, cierre de sesión, protección de pantallas, método POST y CSRF.
- Mantener filtros combinables, historial, versiones, descargas PDF, aprobación/rechazo, cierre de trabajo e importe final cobrado, y resumen mensual.
- No cambiar URLs, permisos, cálculos ni importes.
- Accesibilidad: jerarquía semántica, foco visible, contraste WCAG 4,5:1 para texto normal y sin desplazamiento horizontal desde 320 px, en ambos modos.
- Los PDF ya emitidos y guardados en `media/presupuestos/` no se modifican (las versiones confirmadas son inmutables). Solo cambia la identidad del encabezado de los PDF nuevos; el resto del contenido y diseño del PDF no cambia.

## Criterios de aceptación

1. La suite Django completa y `manage.py check` pasan. Las pruebas que buscaban "Taller Norte" verifican "FT MOTORS" y los datos de contacto. Una prueba nueva comprueba que el PDF nuevo contiene nombre, dirección y teléfono reales y ya no "TALLER DEMO".
2. Las cuatro pantallas, en ambos modos, a 320, 390, 768 px y escritorio: sin desplazamiento horizontal, contraste 4,5:1 en texto normal y foco visible. Se registran viewport y métricas, como en el ticket 11 de correcciones de revisión final.
3. El botón de modo cambia el modo, lo recuerda al recargar, cerrar sesión y reiniciar el navegador, funciona con teclado y no produce parpadeo.
4. Inicio y cierre de sesión, filtros, historial, versiones, descargas, aprobación y rechazo, cierre de trabajo y resumen mensual se comportan igual; no cambian URLs, permisos, CSRF ni importes.
5. Un presupuesto nuevo se genera con la identidad de FT MOTORS; un PDF ya emitido descargado desde el historial sigue siendo el original.

## Fuera de alcance

- Página pública para clientes (servicios, contacto, ubicación).
- Fotos o imágenes del taller.
- Panel técnico `/admin/`, mensajes del bot de Telegram, datos fiscales, y diseño del PDF más allá de su encabezado.
- Despliegue en VPS.
- Logo definitivo en archivo: queda como reemplazo posterior en un solo lugar.

## Plan de tickets

- [01 — Identidad central de FT MOTORS](issues/01-identidad-central-ft-motors.md)
- [02 — Estilo FT MOTORS híbrido](issues/02-estilo-ft-motors-hibrido.md)
- [03 — Modo oscuro](issues/03-modo-oscuro.md)
- [04 — Verificación y regresiones](issues/04-verificacion-y-regresiones.md)
