# Generated for the vehicle registration ticket.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plate", models.CharField(max_length=20, verbose_name="patente")),
                ("normalized_plate", models.CharField(editable=False, max_length=20, unique=True, verbose_name="patente normalizada")),
                ("make", models.CharField(max_length=100, verbose_name="marca")),
                ("model", models.CharField(max_length=100, verbose_name="modelo")),
                ("customer_type", models.CharField(choices=[("municipalidad", "Municipalidad"), ("particular", "Particular")], max_length=20, verbose_name="tipo de cliente")),
                ("customer_name", models.CharField(max_length=200, verbose_name="nombre del cliente")),
                ("customer_phone", models.CharField(max_length=50, verbose_name="teléfono del cliente")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="fecha de registro")),
            ],
            options={"verbose_name": "vehículo", "verbose_name_plural": "vehículos", "ordering": ["plate"]},
        ),
    ]
