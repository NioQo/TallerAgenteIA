# 01: Identidad central de FT MOTORS

**Objetivo / Qué construir:** definir la identidad real de FT MOTORS en un único lugar y aplicarla a la web y a los PDF nuevos, incluyendo un logotipo de texto reemplazable.

**Status:** spec-ready

**Blocked by:** None (can start immediately).

**Referencia:** [Especificación](../spec.md), secciones "Identidad del taller" y "Compatibilidad funcional".

## Alcance

- Nombre, lema ("Tu vehículo en manos expertas"), teléfono (+54 9 11 5429 6017), dirección (Av. Dardo Rocha 1891, Ruta 25, Pilar, Buenos Aires) y logotipo de texto definidos en un solo lugar.
- Web: título, encabezado, pantalla de acceso y pie usan esa fuente en lugar de "Taller Norte / Servicio automotor".
- PDF nuevos: el encabezado usa nombre, dirección y teléfono reales en lugar de "TALLER DEMO", "Av. del Taller 123" y "(011) 4000-0000".
- El logotipo puede sustituirse por un archivo real cambiándolo en un solo lugar.

## Criterios de aceptación

- [ ] Cambiar un dato de identidad se hace en un solo lugar y se refleja en web y PDF.
- [ ] Ninguna pantalla ni PDF nuevo muestra "Taller Norte" ni "TALLER DEMO".
- [ ] Las pruebas que buscaban "Taller Norte" verifican "FT MOTORS" y los datos de contacto.
- [ ] Prueba nueva: el PDF nuevo contiene nombre, dirección y teléfono reales.
- [ ] Los PDF ya emitidos en `media/presupuestos/` no se modifican.
- [ ] No se agregan datos fiscales, email, horarios ni redes.

## Límites

No cambia el contenido del PDF más allá del encabezado. No incluye mensajes de Telegram ni `/admin/`.
