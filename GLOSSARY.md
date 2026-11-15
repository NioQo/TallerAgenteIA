# Glosario del taller

Términos del dominio acordados para la demo. Este archivo define vocabulario y no decisiones de implementación.

## Identidad del taller

Nombre, lema, dirección, teléfono y logotipo con los que el taller se presenta en la web y en los presupuestos. Es distinta del taller como negocio y puede ser ficticia hasta recibir los datos reales.

## Cliente

Persona u organización a la que el taller presta el servicio y presenta el presupuesto. Para esta demo, su tipo es **Municipalidad** o **particular**; se registran nombre y teléfono.

## Vehículo

Automóvil atendido por el taller. Se identifica por su patente y se describe, como mínimo, por marca y modelo. Tiene un historial de presupuestos y trabajos.

## Repuesto

Material o pieza que se incluye en un presupuesto o se registra como utilizado en un trabajo. Un ítem presupuestado incluye cantidad y precio unitario.

## Catálogo de precios

Conjunto de precios de repuestos previamente ingresados, que el sistema puede sugerir al preparar otro presupuesto. Una sugerencia puede confirmarse o cambiarse; los presupuestos existentes mantienen sus propios precios.

## Mano de obra

Importe total del trabajo de reparación, ingresado manualmente para cada presupuesto en la demo. Su forma de cálculo real no está confirmada.

## Presupuesto

Propuesta económica para un trabajo sobre un vehículo. Incluye cliente, vehículo, descripción del trabajo, repuestos, mano de obra, fecha y total. No es una factura ni acredita por sí mismo que el trabajo se haya realizado o cobrado.

## Borrador de presupuesto

Preparación incompleta y todavía no confirmada de un presupuesto. Puede incluir datos aportados por una persona, datos ya registrados y datos pendientes de aclaración; no constituye un presupuesto emitido.

## Operador de Telegram

Persona autorizada que utiliza el bot para registrar vehículos y preparar o corregir presupuestos; puede ser el mecánico o su ayudante.

## Versión de presupuesto

Registro inmutable de una versión confirmada del presupuesto. Una corrección crea una nueva versión relacionada, sin reemplazar la anterior.

## Trabajo

Reparación realizada o por realizar en un vehículo. Al terminar, se registran los repuestos efectivamente utilizados y el importe final cobrado, que pueden diferir del presupuesto.

## Importe final cobrado

Importe registrado al cierre del trabajo como efectivamente cobrado. Es el valor que se usa en el resumen mensual de cobros, en lugar del total estimado del presupuesto.

## Estado de presupuesto

Situación administrativa del presupuesto en la demo: **pendiente**, **aprobado**, **rechazado** o **trabajo terminado**.
