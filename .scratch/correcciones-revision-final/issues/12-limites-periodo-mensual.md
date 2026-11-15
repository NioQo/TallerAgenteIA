# 12: Validar límites del período mensual

**What to build:** aceptar períodos consultables sin excepciones y rechazar períodos fuera del rango temporal realmente soportado con un mensaje claro.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent — Corrección de error P2.

**Problema y requisito afectado:** `year=9999` pasa la validación actual (1–9999) y falla al construir límites de fecha en SQLite con `OverflowError`. Incumple spec web, criterios 3 y 5 sobre validación/errores; spec base, gestión web, resumen mensual.

**Pasos para reproducir:** autenticarse y consultar `/resumen-mensual/?month=12&year=9999`.

**Comportamiento actual:** excepción no controlada y respuesta de servidor 500.

**Comportamiento esperado:** período dentro del rango soportado consulta normalmente; período no soportado muestra validación comprensible sin 500.

- [ ] Definir y documentar el rango de años que SQLite/app soportan.
- [ ] Los límites admitidos consultan datos sin excepción; los no admitidos devuelven error de formulario.
- [ ] Validar mes vacío, no numérico, 0, 13 y años en ambos límites y fuera de ellos.
- [ ] Confirmar que conteo e importe mensual válidos, incluido un mes vacío, no cambian.

**Dependencias:** Ninguna.
