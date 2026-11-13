# 13: Verificar aislamiento del almacenamiento en pruebas

**What to build:** determinar y documentar si ejecutar la suite deja archivos de presupuesto en el almacenamiento normal; corregirlo solo si una prueba controlada demuestra contaminación.

**Blocked by:** None (can start immediately).

**Status:** verified — Contaminación confirmada en tres tests; aislada.

**Problema y requisito afectado:** varias pruebas invocan guardado de presupuesto y generación de PDF. La revisión final usó SQLite y almacenamiento en memoria para no tocar datos; no verificó dónde escribiría la suite con la configuración ordinaria. Afecta seguridad de datos de desarrollo y repetibilidad de las pruebas, no es un requisito funcional de las specs.

**Pasos para verificar:** en entorno temporal descartable, inventariar el almacenamiento antes y después de ejecutar la suite, ejecutar también un caso que falle durante guardado y revisar el estado Git.

**Comportamiento actual:** no verificado en almacenamiento normal; no asumir que hubo contaminación.

**Comportamiento esperado:** si la suite escribe, los archivos quedan aislados y se limpian; si no escribe, documentar evidencia y cerrar como no issue.

- [x] Ejecutar en un directorio de medios temporal y registrar el delta de archivos tras suite exitosa.
- [x] Evaluar caso de fallo/rollback y comprobar archivos huérfanos.
- [x] Aislar con `TemporaryDirectory` los tres tests existentes que guardaban PDFs sin redirigir `MEDIA_ROOT`.
- [x] Confirmar que la limpieza del directorio temporal cubre también un fallo ocurrido después de escribir el PDF.

**Evidencia:** la configuración ordinaria usa `MEDIA_ROOT = BASE_DIR / "media"`. Una ejecución inicial de la suite con `MEDIA_ROOT` temporal dejó tres PDFs tras fallar dos aserciones ajenas a almacenamiento. Los tres tests que escribían fuera de un directorio temporal fueron aislados. Un test controlado fuerza una excepción justo después de escribir el PDF: la transacción revierte los registros de base de datos, el archivo huérfano queda dentro del directorio temporal y desaparece al salir del contexto. La ejecución final de los 67 tests pasó y el inventario del directorio temporal quedó vacío antes y después (`MEDIA_DELTA=[]`). `manage.py check` no reportó problemas. No se modificó la lógica de almacenamiento de producción.

## Comments

- Verificación completada. No se usó el inventario previo de `media/` para atribuir archivos existentes a la suite; todas las ejecuciones se hicieron con medios y base de datos temporales.

**Dependencias:** Ninguna.
