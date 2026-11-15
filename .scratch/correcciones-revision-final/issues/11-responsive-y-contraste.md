# 11: Corregir accesibilidad y diseño responsive

**What to build:** usar las cuatro pantallas del taller a 320 px sin desplazamiento horizontal y con contraste legible en controles y estados.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Requisito incumplido P2, verificado en navegador.

**Problema y requisito afectado:** a 320 px el documento mide 320 px pero el área de cliente 305 px, generando 15 px de desplazamiento horizontal. El contraste calculado fue 4,23:1 para texto blanco sobre naranja y 3,91:1 para naranja sobre fondo claro. Incumple spec web, alcance 14–15 y criterio 2; ticket web 01, criterios 3–4; ticket web 03, criterio 3.

**Pasos para reproducir:** iniciar sesión y abrir acceso, dashboard, ficha de vehículo e informe mensual a 320 px; inspeccionar scroll horizontal y contraste de botones/eyebrows.

**Comportamiento actual:** scroll horizontal a 320 px; ciertos textos normales no alcanzan contraste 4,5:1.

**Comportamiento esperado:** layout utilizable sin desplazamiento horizontal y contraste WCAG suficiente para el tamaño de texto, conservando foco visible.

- [ ] Probar las cuatro pantallas a 320, 390, 768 y escritorio; `scrollWidth` no supera el ancho visible y no se depende del desplazamiento horizontal.
- [ ] Texto normal alcanza 4,5:1 como mínimo; texto grande/controles, cuando aplique, alcanzan los umbrales WCAG correspondientes.
- [ ] Foco, etiquetas y estados siguen distinguibles por forma/texto además del color.
- [ ] Pruebas visuales o de navegador registran viewport y métricas para las cuatro pantallas.

**Dependencias:** Ninguna.
