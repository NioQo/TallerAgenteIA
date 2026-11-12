# 01: Accesos y ejecución local

**Objetivo / Qué construir:** permitir que el administrador acceda a la web y que el mecánico autorizado interactúe con un bot real de Telegram, ejecutando la demo en una computadora. Entregar un recorrido mínimo de acceso funcional, con la base persistente necesaria para continuar.

**Blocked by:** Ninguno (puede comenzar inmediatamente).

**Status:** implementation-complete; authorized real Telegram connection verified

**Referencia:** [Especificación: Alcance de la demo](../spec.md#alcance-de-la-demo).

## Alcance de la sesión

- Elegir y documentar una solución técnica mínima para la demo local, sin servicios de alojamiento obligatorios.
- Implementar el acceso web de un administrador y el reconocimiento de una cuenta de Telegram autorizada.
- Proveer instrucciones reproducibles para configurar y ejecutar la aplicación con persistencia local.
- Mantener el alcance de un taller, sin registro público ni administración de múltiples usuarios.

## Criterios de aceptación

- [x] Dependencias instalables y comandos documentados para iniciar web y bot en la computadora del usuario.
- [x] El administrador inicia sesión con credenciales válidas, accede a una pantalla protegida y puede cerrar sesión; las credenciales incorrectas no permiten acceder.
- [x] Sin sesión no se puede acceder a la pantalla protegida mediante una petición directa.
- [x] La cuenta de Telegram autorizada recibe una respuesta del bot real. Verificado manualmente; la prueba desde una cuenta distinta sigue pendiente.
- [x] El token del bot, el identificador de Telegram autorizado y las credenciales se configuran localmente, sin incorporar secretos a los archivos compartidos del proyecto.
- [x] El administrador se guarda en SQLite persistente y no exige volver a crearlo al reiniciar.
- [x] La documentación explica cómo obtener y configurar el token del bot y el identificador autorizado, cómo iniciar y detener la demo y que necesita conexión a Internet para Telegram.
- [x] Se documentó el procedimiento y se registró la conexión real desde la cuenta autorizada. La comprobación con una cuenta no autorizada sigue pendiente.

## Implementación

- **Tecnología elegida:** Django 5.2 para autenticación, sesiones y vistas protegidas; SQLite para persistencia local; `python-telegram-bot` 22 con *long polling* para el bot. Web y bot corren como procesos locales separados, sin alojamiento obligatorio.
- La web usa el usuario administrador de Django, almacena la contraseña con hash y protege el panel con sesión y CSRF. `createsuperuser` crea el acceso inicial una sola vez; el usuario permanece en `db.sqlite3` al reiniciar.
- El bot permite únicamente una cuenta configurada por identificador numérico y responde tanto a `/start` como a mensajes de texto. No implementa aún operaciones del taller.
- Los secretos se leen del `.env` local, excluido por `.gitignore`; `.env.example` no incluye valores secretos.
- Guía reproducible, configuración y procedimiento de prueba: `README.md`.

## Estado de aceptación

- [x] Instrucciones locales para iniciar web y bot; dependencias declaradas.
- [x] Acceso administrador válido, rechazo de credenciales incorrectas y cierre de sesión.
- [x] El panel protegido requiere sesión.
- [x] Bot probado en Telegram real con la cuenta autorizada; respondió que está conectado. **Pendiente:** comprobar que otra cuenta no autorizada no puede iniciar operaciones.
- [x] Secretos y configuración local fuera de archivos compartidos.
- [x] Administrador persistido en SQLite entre reinicios.
- [x] Documentación para obtener/configurar datos de Telegram, iniciar/detener y requisito de Internet.
- [x] Resultado real registrado en Comments: la cuenta autorizada conecta; falta la prueba con cuenta no autorizada.
- [x] Pruebas automáticas locales: acceso web y autorización por identificador con límites simulados; no prueban conexión con Telegram.

## Notas de ejecución

Las credenciales se configuraron localmente y no se incorporaron secretos al repositorio. Se verificó la cuenta autorizada; queda pendiente probar una cuenta distinta.

## Comments

- Verificación manual real: el administrador inició sesión en la web y el bot respondió desde la cuenta autorizada: «Acceso autorizado. El bot del taller está conectado.» La prueba desde una cuenta no autorizada no se realizó todavía.
