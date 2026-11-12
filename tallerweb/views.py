from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum
from django.http import FileResponse, Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from tallerweb.models import Budget, CompletedWork, Vehicle, WorkItem
from datetime import date


@login_required
def dashboard(request):
    vehicles = Vehicle.objects.all()
    budgets = Budget.objects.select_related("vehicle").all()
    filters = {"plate": request.GET.get("plate", "").strip(),
               "customer_type": request.GET.get("customer_type", ""),
               "date_from": request.GET.get("date_from", "").strip(),
               "date_to": request.GET.get("date_to", "").strip()}
    valid_types = {choice[0] for choice in Vehicle.CustomerType.choices}
    errors = []
    start = end = None
    for field, label in (("date_from", "inicio"), ("date_to", "fin")):
        value = filters[field]
        if value:
            try:
                parsed = date.fromisoformat(value)
                if parsed.isoformat() != value:
                    raise ValueError
                if field == "date_from":
                    start = parsed
                else:
                    end = parsed
            except ValueError:
                errors.append(f"La fecha de {label} no es válida.")
    if start and end and start > end:
        errors.append("La fecha de inicio debe ser anterior o igual a la fecha de fin.")
    if filters["customer_type"] and filters["customer_type"] not in valid_types:
        errors.append("El tipo de cliente seleccionado no es válido.")
    if not errors:
        plate = "".join(char for char in filters["plate"].upper() if char.isalnum())
        if plate:
            vehicles = vehicles.filter(normalized_plate__contains=plate)
            budgets = budgets.filter(vehicle__normalized_plate__contains=plate)
        if filters["customer_type"]:
            vehicles = vehicles.filter(customer_type=filters["customer_type"])
            budgets = budgets.filter(vehicle__customer_type=filters["customer_type"])
        if start:
            budgets = budgets.filter(created_at__date__gte=start)
        if end:
            budgets = budgets.filter(created_at__date__lte=end)
        if start or end:
            vehicles = vehicles.filter(pk__in=budgets.values("vehicle_id"))
    return render(request, "dashboard.html", {"vehicles": vehicles, "budgets": budgets,
                                                "filters": filters, "filter_errors": errors,
                                                "filters_active": any(filters.values())})


@login_required
def monthly_summary(request):
    today = timezone.localdate()
    raw_month = request.GET.get("month", str(today.month))
    raw_year = request.GET.get("year", str(today.year))
    error = ""
    month, year = today.month, today.year
    try:
        month, year = int(raw_month), int(raw_year)
        if not 1 <= month <= 12 or not 1 <= year <= 9999:
            raise ValueError
    except (TypeError, ValueError):
        error = "Selecciona un mes y año válidos."
    summary = {"count": 0, "total": Decimal("0.00")}
    if not error:
        summary = CompletedWork.objects.filter(closed_at__year=year, closed_at__month=month).aggregate(
            count=Count("pk"), total=Sum("final_amount")
        )
        summary["total"] = summary["total"] or Decimal("0.00")
    return render(request, "monthly_summary.html", {
        "month": f"{month:02d}", "year": year, "summary": summary, "summary_error": error,
        "months": [(f"{number:02d}", name) for number, name in enumerate(
            ("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
             "Septiembre", "Octubre", "Noviembre", "Diciembre"), 1)],
    })


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle.objects.prefetch_related("budgets__items"), pk=pk)
    return render(request, "vehicle_detail.html", {"vehicle": vehicle})


@login_required
def decide_budget(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    decision = request.POST.get("decision")
    if decision not in {Budget.Status.APPROVED, Budget.Status.REJECTED}:
        raise Http404("Decisión no válida.")
    with transaction.atomic():
        budget = get_object_or_404(Budget.objects.select_for_update(), pk=pk)
        if budget.next_versions.exists():
            raise Http404("Solo se puede decidir sobre la versión vigente.")
        if budget.status == Budget.Status.PENDING:
            budget.status = decision
            budget.save(update_fields=["status"])
    return redirect("vehicle_detail", pk=budget.vehicle_id)


@login_required
def complete_work(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    with transaction.atomic():
        budget = get_object_or_404(Budget.objects.select_for_update().prefetch_related("items"), pk=pk)
        if budget.next_versions.exists():
            raise Http404("Solo se puede cerrar la versión vigente.")
        if budget.status == Budget.Status.COMPLETED and hasattr(budget, "completed_work"):
            return redirect("vehicle_detail", pk=budget.vehicle_id)
        if budget.status != Budget.Status.APPROVED:
            raise Http404("Solo se pueden cerrar presupuestos aprobados.")

        try:
            amount = Decimal(request.POST.get("final_amount", ""))
            if not amount.is_finite() or amount < 0 or amount > Decimal("9999999999.99"):
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return redirect("vehicle_detail", pk=budget.vehicle_id)

        descriptions = request.POST.getlist("item_description")
        quantities = request.POST.getlist("item_quantity")
        if len(descriptions) != len(quantities):
            return redirect("vehicle_detail", pk=budget.vehicle_id)
        items = []
        try:
            for description, quantity in zip(descriptions, quantities):
                description = description.strip()
                if not description:
                    continue
                parsed_quantity = int(quantity)
                if parsed_quantity <= 0 or parsed_quantity > 2147483647:
                    raise ValueError
                items.append((description[:200], parsed_quantity))
        except ValueError:
            return redirect("vehicle_detail", pk=budget.vehicle_id)

        work = CompletedWork.objects.create(budget=budget, final_amount=amount)
        WorkItem.objects.bulk_create([WorkItem(work=work, description=name, quantity=quantity)
                                      for name, quantity in items])
        budget.status = Budget.Status.COMPLETED
        budget.save(update_fields=["status"])
    return redirect("vehicle_detail", pk=budget.vehicle_id)


@login_required
def budget_pdf_download(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    if not budget.pdf:
        raise Http404("El PDF todavía no está disponible.")
    return FileResponse(budget.pdf.open("rb"), as_attachment=True, filename=f"{budget.number}.pdf",
                        content_type="application/pdf")
