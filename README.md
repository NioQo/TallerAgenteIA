# Demo local del taller

Aplicación local de demo: Django 5.2, SQLite persistente, bot de Telegram con `python-telegram-bot` en *long polling* y presupuestos PDF. La web y el bot se ejecutan en procesos separados en la computadora del taller; Telegram requiere conexión a Internet. La base de datos `db.sqlite3` conserva la información entre reinicios y los PDF confirmados se guardan en `media/presupuestos/`.

## Requisitos

- Windows 10/11 y Python 3.12 o compatible.
- Internet para instalar dependencias y para conectar el bot a Telegram.

## Preparación inicial

En PowerShell, desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` localmente. `DJANGO_SECRET_KEY` debe ser un valor aleatorio privado; para generarlo:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copia ese resultado a `DJANGO_SECRET_KEY`. Nunca publiques `.env` ni compartas el token del bot o la clave. El archivo está excluido por `.gitignore`.

## Crear el acceso del administrador

Ejecuta una sola vez para crear la base de datos y el administrador:

```powershell
$env:DJANGO_SECRET_KEY = (Select-String '^DJANGO_SECRET_KEY=' .env).Line.Split('=', 2)[1]
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
```

El usuario y contraseña se guardan en SQLite como credenciales con contraseña hasheada. La base de datos permanece en esta carpeta y no se debe borrar para conservar el acceso. Para crear otro administrador en el futuro, repite `createsuperuser`.

## Iniciar y detener la web

En una ventana de PowerShell:

```powershell
$env:DJANGO_SECRET_KEY = (Select-String '^DJANGO_SECRET_KEY=' .env).Line.Split('=', 2)[1]
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Abre <http://127.0.0.1:8000/>. Se redirige al inicio de sesión; las páginas del panel requieren una sesión válida. Usa el botón **Cerrar sesión** para salir. Detén el servidor con `Ctrl+C`.

## Configurar e iniciar Telegram

1. En Telegram, abre el chat oficial `@BotFather`, crea un bot con `/newbot` y copia el token que entrega.
2. Obtén el identificador numérico de la cuenta autorizada (por ejemplo, consultándolo con `@userinfobot`). No uses el nombre de usuario: se compara el identificador numérico de Telegram.
3. Completa `TELEGRAM_BOT_TOKEN` y `TELEGRAM_ALLOWED_USER_ID` en `.env`; conserva ambos valores privados.
4. En otra ventana de PowerShell, desde esta carpeta, inicia el bot:

```powershell
$env:DJANGO_SECRET_KEY = (Select-String '^DJANGO_SECRET_KEY=' .env).Line.Split('=', 2)[1]
.\.venv\Scripts\python.exe manage.py runbot
```

5. Desde la cuenta autorizada, abre el bot y envía `/start`; debe responder que está conectado. Envía `/start` o un mensaje de texto desde otra cuenta; debe responder que no está autorizada. Detén el proceso con `Ctrl+C`.

La interpretación IA de mensajes directos se configura con `OPENAI_API_KEY`, `OPENAI_MODEL` y `OPENAI_ENABLED` en `.env`. Permanece deshabilitada por defecto. Al habilitarla, solo se envía a OpenAI el texto del mensaje entrante, nunca los datos previos del borrador. El borrador estructurado se guarda localmente en SQLite y caduca a los 30 días desde su última modificación; al iniciar o reanudar la interacción se ofrecen las opciones de continuarlo o descartarlo. Descartar lo elimina inmediatamente. No se crea vehículo, presupuesto ni cambio de catálogo hasta la confirmación explícita por el flujo guiado `/presupuesto`. Los comandos y botones existentes siguen disponibles.

Con `/vehiculo`, el mecánico autorizado puede registrar vehículos o consultar uno existente por patente. Para un vehículo nuevo, el bot solicita marca, modelo, tipo de cliente, nombre y teléfono; los campos vacíos se pueden corregir enviando el dato de nuevo. Los vehículos y clientes asociados se conservan en SQLite y aparecen en el listado protegido de la web. Las patentes se comparan sin distinguir mayúsculas, espacios ni guiones.

Con `/presupuesto`, el mecánico inicia un presupuesto para un vehículo existente, describe el trabajo e ingresa uno o más repuestos con cantidad y precio unitario en ARS. Envía `/listo` al terminar la lista de repuestos, carga la mano de obra y revisa el resumen. Si un repuesto ya figura en el catálogo de precios, el bot muestra el precio guardado como sugerencia (no como cotización actual) y permite usarlo o ingresar otro; el precio elegido queda disponible para presupuestos futuros. Los botones permiten corregir descripción, repuestos o mano de obra antes de confirmar. Para importes con centavos se acepta coma o punto decimal, sin separador de miles. `/cancelar` abandona la operación. Al confirmar, se genera y conserva un PDF con identidad ficticia de demo y se intenta entregarlo al mecánico por Telegram. Si falla, el presupuesto no se pierde: reintenta con `/reenviar P-000001`. El mismo PDF se descarga desde el historial web protegido. La confirmación repetida no crea otro presupuesto.

Con `/corregir`, selecciona un presupuesto pendiente y revisa o edita descripción, repuestos y mano de obra antes de confirmar. La confirmación genera otra versión con número y PDF propios; no modifica el documento anterior. El historial web muestra cada versión como vigente o histórica y permite descargar su PDF. Solo puede corregirse la versión vigente mientras esté pendiente.

Los PDF son presupuestos (no facturas) y quedan guardados bajo `media/`; conserva esta carpeta junto con `db.sqlite3` al respaldar la demo. La identidad del taller impresa es ficticia y debe reemplazarse cuando se reciban los datos reales.

Si el proyecto ya tenía una base local previa, aplica la migración al actualizar con `.\.venv\Scripts\python.exe manage.py migrate`. No compartas el token con el proyecto ni con terceros. Si se expone, revócalo desde BotFather y configura el nuevo valor.

## Comprobaciones locales

```powershell
$env:DJANGO_SECRET_KEY = 'clave-temporal-solo-para-pruebas'
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
```

Las pruebas locales validan acceso web, autorización de Telegram, registro de vehículos, cálculos y correcciones de presupuestos, confirmación idempotente e historial web. No sustituyen la prueba en Telegram real.

## Ampliaciones documentadas (todavía no implementadas)

- [Asistente IA de Telegram para preparar presupuestos](.scratch/asistente-ia-presupuestos/spec.md): mensajes directos en texto, API de OpenAI, preguntas por datos faltantes, borrador recuperable y confirmación explícita. El flujo actual sigue usando comandos, botones y captura guiada.
- [Rediseño profesional de la web](.scratch/rediseno-web/spec.md): actualización visual adaptable de acceso, inicio/listado, historial y resumen mensual. La web actual mantiene su presentación existente.

Ambas ampliaciones son distintas del trabajo base documentado en `.scratch/demo-taller/`. La demo continúa ejecutándose localmente como se describe arriba. El despliegue en VPS para clientes queda para una etapa futura separada.
