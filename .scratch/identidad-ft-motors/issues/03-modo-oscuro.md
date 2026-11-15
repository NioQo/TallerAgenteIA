# 03: Modo oscuro

**Objetivo / Qué construir:** agregar un modo oscuro completo y un botón para alternar entre éste y el modo híbrido, con la preferencia recordada en el navegador.

**Status:** done con verificación parcial — implementado en el repo (commit `ac0a9b6`); falta probar el reinicio real del navegador (ver [ticket 04](04-verificacion-y-regresiones.md)).

**Blocked by:** [02 — Estilo FT MOTORS híbrido](02-estilo-ft-motors-hibrido.md).

**Referencia:** [Especificación](../spec.md), sección "Alcance" (modo oscuro y botón de modo).

## Alcance

- Modo oscuro: fondo grafito/negro en todas las pantallas, tarjetas gris oscuro, texto claro.
- Botón en la navegación, visible en todas las pantallas incluida la de acceso, con texto e ícono del modo al que se pasa ("Modo oscuro" / "Modo claro").
- Primera visita: sigue la preferencia del sistema; sin preferencia, híbrido claro.
- La elección se guarda en el navegador (no en la base de datos ni por usuario) y se conserva al recargar, cerrar sesión y reiniciar.
- Sin parpadeo del modo equivocado al cargar.

## Criterios de aceptación

- [x] El botón cambia el modo y su texto/ícono refleja la acción siguiente.
- [~] La elección persiste tras recargar, cerrar sesión y reiniciar el navegador. **Parcial:** verificado al recargar y al cerrar e iniciar sesión; el reinicio real del navegador no se probó.
- [x] Es operable con teclado, con foco visible y estado anunciado de forma accesible. (Enter y Espacio; `role=status`; sin lector de pantalla real.)
- [x] No hay parpadeo al cargar en ninguno de los dos modos. (Verificado por orden del script antes de la hoja de estilos, no con capturas del primer fotograma.)
- [x] Ambos modos cumplen contraste 4,5:1 en texto normal; botones, errores y estados siguen distinguibles; sin desplazamiento horizontal desde 320 px.
- [x] No se crean migraciones ni cambios de datos.

## Límites

No guarda preferencias por usuario ni en la base de datos.
