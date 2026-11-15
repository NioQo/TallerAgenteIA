# Rediseño profesional de la web del taller

## Objetivo

Dar a la aplicación web existente una estética profesional, clara y coherente, sin alterar sus operaciones administrativas ni los datos que consulta.

Esta ampliación es independiente de la demo base en [Demo de presupuestos para taller](../demo-taller/spec.md) y del asistente de Telegram en [Asistente IA para presupuestos](../asistente-ia-presupuestos/spec.md).

> **Estado:** implementado (identidad ficticia "Taller Norte", paleta azul oscuro y naranja). Su dirección visual e identidad quedan **reemplazadas** por la ampliación [Identidad FT MOTORS y modo oscuro](../identidad-ft-motors/spec.md), todavía no implementada. Este documento conserva su historial original y no se reescribe.

## Alcance

- Rediseñar las cuatro pantallas propias: acceso, inicio/listado y filtros, historial del vehículo/presupuestos, resumen mensual.
- Identidad ficticia temporal del taller, consistente entre pantallas y fácil de sustituir por los datos reales.
- Dirección visual acordada: fondo claro, navegación azul oscuro, acentos naranjas y tipografía muy legible.
- Adaptación a computadora y celular, con formularios, navegación, estados y acciones usables en ambos tamaños.
- Mantener accesibilidad básica: jerarquía semántica, foco visible, contraste suficiente, etiquetas y mensajes de error claros.

## Compatibilidad funcional

- Mantener autenticación, cierre de sesión, protección de pantallas y método POST/CSRF de las acciones.
- Mantener búsqueda y filtros combinables, validación y limpieza, enlaces a vehículos, historial, versiones y descargas PDF.
- Mantener aprobación/rechazo, cierre de trabajo e importe final cobrado con sus estados actuales.
- Mantener selección de mes/año y resumen que cuenta exclusivamente trabajos cerrados e importes finales cobrados.
- No cambiar datos, URLs, cálculos, permisos ni contenido de los PDF como parte de un rediseño visual.

## Criterios de aceptación

1. Las cuatro pantallas comparten navegación, componentes, tipografía, paleta e identidad temporal coherentes.
2. En computadora y celular las pantallas no requieren desplazamiento horizontal y permiten completar las funciones existentes.
3. Los botones de estado y acciones son distinguibles; formularios y errores tienen etiquetas y mensajes claros.
4. Login continúa autenticando; panel y acciones siguen protegidos, con CSRF y restricciones HTTP existentes.
5. Filtros, historial, versiones, descargas, decisiones, cierre y resumen mensual siguen comportándose igual.
6. No se modifican el PDF ni los valores financieros por el cambio de presentación web.

## Fuera de alcance

- El panel técnico `/admin/`, el diseño de los PDF, funciones de negocio nuevas, portal de clientes y despliegue en VPS.
- La demo se sigue ejecutando localmente como ahora; VPS para vender a clientes es trabajo posterior separado.

## Plan de tickets

- [01 — Identidad visual y estructura compartida](issues/01-identidad-y-estructura.md)
- [02 — Rediseñar acceso, listado e historial](issues/02-acceso-listado-historial.md)
- [03 — Rediseñar resumen mensual y verificar responsive](issues/03-resumen-y-verificacion.md)
