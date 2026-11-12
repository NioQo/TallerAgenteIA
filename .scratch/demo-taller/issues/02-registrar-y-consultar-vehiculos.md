# 02: Registrar y consultar vehículos

**Objetivo / Qué construir:** registrar o recuperar un vehículo y su cliente desde Telegram y consultar esos mismos datos en la web del administrador.

**Blocked by:** 01 — Accesos y ejecución local.

**Status:** implementation-complete; real Telegram vehicle registration and web lookup verified

**Referencia:** [Flujo para crear un presupuesto](../spec.md#flujo-para-crear-un-presupuesto), pasos 1–2; [Gestión web e historial](../spec.md#gestión-web-e-historial); [Recorrido principal](../spec.md#recorrido-principal), pasos 1 y 8.

## Alcance de la sesión

- Guiar mediante botones y texto la carga de patente, marca, modelo, tipo de cliente, nombre y teléfono.
- Recuperar vehículos existentes por patente para usarlos en presupuestos posteriores.
- Mostrar un listado y una ficha del vehículo en la web protegida.

## Criterios de aceptación

- [x] El mecánico autorizado puede registrar por Telegram un vehículo con todos los campos indicados, tanto para Municipalidad como para particular.
- [x] Los campos obligatorios vacíos no generan un registro incompleto: el bot explica qué dato falta y permite corregirlo.
- [x] Al ingresar una patente ya registrada se recupera el vehículo existente, sin crear otro vehículo para la misma patente.
- [x] Las diferencias de mayúsculas, espacios o guiones de una misma patente no crean duplicados.
- [x] El administrador encuentra en la web el vehículo cargado en Telegram y consulta sus datos y los del cliente.
- [x] Al reiniciar la aplicación, el vehículo sigue disponible tanto en Telegram como en la web (persistencia SQLite verificada).
- [x] Se verifican alta, recuperación por patente y persistencia, incluyendo al menos un caso municipal y uno particular mediante pruebas automatizadas.

## Límites

El historial de presupuestos podrá estar vacío hasta el ticket 03. Este ticket no incluye transferencias de titularidad ni una gestión independiente de clientes.

## Implementación

- `Vehicle` persiste los datos del vehículo y cliente asociado en SQLite. `normalized_plate` aplica mayúsculas y elimina caracteres no alfanuméricos; su unicidad se garantiza también en la base de datos.
- El comando `/vehiculo` ejecuta el alta guiada; `/start` mantiene la respuesta de autorización e informa el comando. Las interacciones requieren el identificador de Telegram autorizado.
- La web protegida lista vehículos y ofrece una ficha por vehículo con datos asociados del cliente.
- Verificación local: `manage.py test` (13 pruebas), `manage.py check` y `makemigrations --check --dry-run`. Además, el alta real por Telegram y la consulta del vehículo en la web se verificaron manualmente (ver Comments).

## Comments

- Verificación manual real: se registró por Telegram el vehículo de prueba AB123CD (Toyota Corolla, cliente particular Cliente Demo) y el usuario confirmó que aparece correctamente en la web. No se verificaron en esta sesión recuperación de patentes duplicadas ni reinicio/persistencia.
