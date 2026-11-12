import re
import uuid

from django.db import models


def normalize_plate(value: str) -> str:
    """Return the canonical form used to identify a vehicle by its plate."""
    return re.sub(r"[^A-Z0-9]", "", value.upper())


class Vehicle(models.Model):
    class CustomerType(models.TextChoices):
        MUNICIPALITY = "municipalidad", "Municipalidad"
        PRIVATE = "particular", "Particular"

    plate = models.CharField("patente", max_length=20)
    normalized_plate = models.CharField("patente normalizada", max_length=20, unique=True, editable=False)
    make = models.CharField("marca", max_length=100)
    model = models.CharField("modelo", max_length=100)
    customer_type = models.CharField("tipo de cliente", max_length=20, choices=CustomerType.choices)
    customer_name = models.CharField("nombre del cliente", max_length=200)
    customer_phone = models.CharField("teléfono del cliente", max_length=50)
    created_at = models.DateTimeField("fecha de registro", auto_now_add=True)

    class Meta:
        ordering = ["plate"]
        verbose_name = "vehículo"
        verbose_name_plural = "vehículos"

    def save(self, *args, **kwargs):
        self.plate = self.plate.strip().upper()
        self.normalized_plate = normalize_plate(self.plate)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.plate} — {self.make} {self.model}"


class Budget(models.Model):
    class Status(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        APPROVED = "aprobado", "Aprobado"
        REJECTED = "rechazado", "Rechazado"
        COMPLETED = "trabajo terminado", "Trabajo terminado"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="budgets")
    previous_version = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                                         related_name="next_versions")
    version = models.PositiveIntegerField("versión", default=1)
    number = models.CharField("número", max_length=32, unique=True)
    confirmation_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField("fecha", auto_now_add=True)
    description = models.TextField("descripción del trabajo")
    labor_amount = models.DecimalField("mano de obra", max_digits=12, decimal_places=2)
    total = models.DecimalField("total", max_digits=12, decimal_places=2)
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.PENDING)
    pdf = models.FileField("PDF del presupuesto", upload_to="presupuestos/", blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "presupuesto"
        verbose_name_plural = "presupuestos"

    def __str__(self):
        return self.number


class BudgetItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="items")
    description = models.CharField("repuesto", max_length=200)
    quantity = models.PositiveIntegerField("cantidad")
    unit_price = models.DecimalField("precio unitario", max_digits=12, decimal_places=2)
    subtotal = models.DecimalField("subtotal", max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["pk"]
        verbose_name = "repuesto presupuestado"
        verbose_name_plural = "repuestos presupuestados"


class PartCatalog(models.Model):
    description = models.CharField("repuesto", max_length=200, unique=True)
    suggested_unit_price = models.DecimalField("precio sugerido", max_digits=12, decimal_places=2)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        ordering = ["description"]
        verbose_name = "repuesto del catálogo de precios"
        verbose_name_plural = "repuestos del catálogo de precios"

    def __str__(self):
        return self.description


class BudgetDraft(models.Model):
    """The single recoverable, unconfirmed AI budget draft for the authorized operator."""
    slot = models.CharField(max_length=32, unique=True, default="authorized")
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField("última modificación", auto_now=True)

    class Meta:
        verbose_name = "borrador de presupuesto"
        verbose_name_plural = "borradores de presupuesto"


class WorkItem(models.Model):
    work = models.ForeignKey("CompletedWork", on_delete=models.CASCADE, related_name="items")
    description = models.CharField("repuesto", max_length=200)
    quantity = models.PositiveIntegerField("cantidad")

    class Meta:
        ordering = ["pk"]
        verbose_name = "repuesto utilizado"
        verbose_name_plural = "repuestos utilizados"


class CompletedWork(models.Model):
    budget = models.OneToOneField(Budget, on_delete=models.PROTECT, related_name="completed_work")
    final_amount = models.DecimalField("importe final cobrado", max_digits=12, decimal_places=2)
    closed_at = models.DateTimeField("fecha de cierre", auto_now_add=True)

    class Meta:
        ordering = ["-closed_at", "-pk"]
        verbose_name = "trabajo terminado"
        verbose_name_plural = "trabajos terminados"
