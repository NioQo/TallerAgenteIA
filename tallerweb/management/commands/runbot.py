import re
import uuid
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils import timezone
from asgiref.sync import sync_to_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from django.core.files.base import ContentFile

from tallerweb.models import Budget, BudgetDraft, BudgetItem, PartCatalog, Vehicle, normalize_plate
from tallerweb.pdf import budget_pdf
from tallerweb.budget_ai import extract_budget, merge_correction, validate_candidate


PLATE, MAKE, MODEL, CUSTOMER_TYPE, CUSTOMER_NAME, CUSTOMER_PHONE = range(6)
BUDGET_VEHICLE, BUDGET_DESCRIPTION, BUDGET_ITEM_NAME, BUDGET_ITEM_QUANTITY, BUDGET_ITEM_PRICE, BUDGET_LABOR = range(6, 12)
CENT = Decimal("0.01")
DRAFT_TTL = timedelta(days=30)


def json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


@sync_to_async
def get_active_draft():
    draft = BudgetDraft.objects.filter(slot="authorized").first()
    if draft and draft.updated_at <= timezone.now() - DRAFT_TTL:
        draft.delete()
        return None
    return draft.data if draft else None


@sync_to_async
def save_active_draft(data):
    BudgetDraft.objects.update_or_create(slot="authorized", defaults={"data": json_safe(data)})


@sync_to_async
def delete_active_draft():
    BudgetDraft.objects.filter(slot="authorized").delete()


async def offer_draft_actions(message):
    draft = await get_active_draft()
    if draft is None:
        return False
    await message.reply_text(
        "Hay un borrador de presupuesto guardado. ¿Quieres continuarlo o descartarlo?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Continuar borrador", callback_data="draft:continue"),
            InlineKeyboardButton("Descartar borrador", callback_data="draft:discard"),
        ]]),
    )
    return True


@sync_to_async
def find_vehicle(normalized_plate):
    return Vehicle.objects.filter(normalized_plate=normalized_plate).first()


@sync_to_async
def save_vehicle(data):
    return Vehicle.objects.create(**data)


@sync_to_async
def get_vehicle(normalized_plate):
    return Vehicle.objects.get(normalized_plate=normalized_plate)


@sync_to_async
def find_catalog_part(description):
    return PartCatalog.objects.filter(description__iexact=description).first()


@sync_to_async
def save_catalog_price(description, price):
    part = PartCatalog.objects.filter(description__iexact=description).first()
    if part:
        part.suggested_unit_price = price
        part.save(update_fields=["suggested_unit_price", "updated_at"])
    else:
        part = PartCatalog.objects.create(description=description, suggested_unit_price=price)
    return part


def update_catalog_prices(items):
    """Persist confirmed item prices as the latest historical catalog suggestions."""
    for item in items:
        part = PartCatalog.objects.filter(description__iexact=item["description"]).first()
        if part:
            part.suggested_unit_price = item["unit_price"]
            part.save(update_fields=["suggested_unit_price", "updated_at"])
        else:
            PartCatalog.objects.create(description=item["description"], suggested_unit_price=item["unit_price"])


def validate_budget_data(data):
    """Validate and deterministically total a budget before any domain write."""
    description = data.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 2000:
        raise ValueError("Falta una descripción válida del trabajo.")
    if data.get("vehicle") is None:
        vehicle_data = data.get("vehicle_data")
        required_vehicle_fields = ("plate", "make", "model", "customer_type", "customer_name", "customer_phone")
        if (not isinstance(vehicle_data, dict)
                or any(not isinstance(vehicle_data.get(field), str) or not vehicle_data[field].strip()
                       for field in required_vehicle_fields)
                or vehicle_data.get("customer_type") not in Vehicle.CustomerType.values):
            raise ValueError("Faltan datos válidos del vehículo o del cliente.")
        limits = {"plate": 20, "make": 100, "model": 100, "customer_name": 200, "customer_phone": 50}
        if (any(len(vehicle_data[field].strip()) > limit for field, limit in limits.items())
                or not normalize_plate(vehicle_data["plate"])):
            raise ValueError("Los datos del vehículo o del cliente exceden los límites permitidos.")
    source_draft = data.get("ai_source_draft")
    if source_draft:
        if source_draft.get("uncertainties"):
            raise ValueError("Quedan aclaraciones pendientes en el borrador IA.")
        vehicle = data.get("vehicle")
        reference = vehicle if vehicle is not None else data.get("vehicle_data", {})
        for field in ("plate", "make", "model", "customer_type", "customer_name", "customer_phone"):
            proposed = source_draft.get(field)
            registered = getattr(reference, field, None) if vehicle is not None else reference.get(field)
            if proposed and registered and (normalize_plate(proposed) != normalize_plate(registered)
                                            if field == "plate" else proposed != registered):
                raise ValueError("El borrador IA contradice los datos del vehículo o cliente.")
        if any(item.get("unit_price") is None for item in source_draft.get("items", [])):
            raise ValueError("Cada repuesto del borrador IA requiere precio unitario explícito.")
    try:
        labor = Decimal(str(data["labor_amount"]))
        if (not labor.is_finite() or labor < 0 or labor.as_tuple().exponent < -2
                or labor > Decimal("9999999999.99")):
            raise InvalidOperation
    except (KeyError, InvalidOperation, ValueError, TypeError):
        raise ValueError("La mano de obra debe ser válida, no negativa y tener hasta dos decimales.")

    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("La lista de repuestos no es válida.")
    normalized_items = []
    total = labor
    for item in items:
        try:
            item_description = item["description"]
            quantity = item["quantity"]
            quantity_number = Decimal(str(quantity))
            unit_price = Decimal(str(item["unit_price"]))
            if (not isinstance(item_description, str) or not item_description.strip()
                    or len(item_description) > 200 or not quantity_number.is_finite()
                    or quantity_number <= 0 or quantity_number != quantity_number.to_integral_value()
                    or quantity_number > 2147483647 or not unit_price.is_finite() or unit_price < 0
                    or unit_price.as_tuple().exponent < -2 or unit_price > Decimal("9999999999.99")):
                raise InvalidOperation
        except (KeyError, InvalidOperation, ValueError, TypeError):
            raise ValueError("Cada repuesto requiere descripción, cantidad positiva y precio unitario válido.")
        quantity = int(quantity_number)
        subtotal = money(unit_price * quantity)
        total += subtotal
        normalized_items.append({"description": item_description.strip(), "quantity": quantity,
                                 "unit_price": unit_price, "subtotal": subtotal})
    if total > Decimal("9999999999.99"):
        raise ValueError("El total está fuera del rango permitido.")
    result = dict(data)
    result.update({"description": description.strip(), "labor_amount": labor,
                   "items": normalized_items, "total": money(total)})
    return result


@sync_to_async
def save_budget(data):
    data = validate_budget_data(data)
    try:
        with transaction.atomic():
            existing = Budget.objects.filter(confirmation_key=data["confirmation_key"]).first()
            if existing:
                return existing
            vehicle = data.get("vehicle")
            if vehicle is None:
                vehicle_data = data.get("vehicle_data")
                if not vehicle_data:
                    raise ValueError("Faltan los datos obligatorios del vehículo.")
                normalized = normalize_plate(vehicle_data["plate"])
                vehicle, created = Vehicle.objects.get_or_create(
                    normalized_plate=normalized,
                    defaults={**vehicle_data, "normalized_plate": normalized},
                )
                if not created and any(
                    getattr(vehicle, field) != vehicle_data[field]
                    for field in ("make", "model", "customer_type", "customer_name", "customer_phone")
                ):
                    raise ValueError("La patente ya está registrada con datos diferentes.")
            last = Budget.objects.select_for_update().order_by("-pk").first()
            number = f"P-{(last.pk if last else 0) + 1:06d}"
            fields = {k: v for k, v in data.items() if k not in {"items", "vehicle_data", "ai_source_draft"}}
            fields["vehicle"] = vehicle
            budget = Budget.objects.create(number=number, **fields)
            BudgetItem.objects.bulk_create([BudgetItem(budget=budget, **item) for item in data["items"]])
            update_catalog_prices(data["items"])
            budget.pdf.save(f"{budget.number}.pdf", ContentFile(budget_pdf(budget)), save=True)
            return budget
    except IntegrityError:
        existing = Budget.objects.filter(confirmation_key=data["confirmation_key"]).first()
        if existing:
            return existing
        raise


@sync_to_async
def find_budget_by_key(key):
    return Budget.objects.filter(confirmation_key=key).first()


@sync_to_async
def pending_budgets():
    return list(Budget.objects.select_related("vehicle").filter(
        status=Budget.Status.PENDING, next_versions__isnull=True))


@sync_to_async
def get_budget_with_items(number):
    return Budget.objects.select_related("vehicle").prefetch_related("items").filter(number=number).first()


@sync_to_async
def has_next_version(budget_id):
    return Budget.objects.filter(previous_version_id=budget_id).exists()


@sync_to_async
def save_budget_revision(original_id, data):
    with transaction.atomic():
        original = Budget.objects.select_for_update().get(pk=original_id)
        data = validate_budget_data({**data, "vehicle": original.vehicle})
        if original.status != Budget.Status.PENDING:
            raise ValueError("Solo se pueden crear versiones de presupuestos pendientes.")
        if Budget.objects.filter(previous_version=original).exists():
            raise ValueError("El presupuesto ya tiene una versión posterior.")
        last = Budget.objects.select_for_update().order_by("-pk").first()
        number = f"P-{(last.pk if last else 0) + 1:06d}"
        revision = Budget.objects.create(
            number=number, vehicle=original.vehicle, previous_version=original,
            version=original.version + 1, confirmation_key=data["confirmation_key"],
            description=data["description"], labor_amount=data["labor_amount"],
            total=data["total"], status=original.status,
        )
        BudgetItem.objects.bulk_create([BudgetItem(budget=revision, **item) for item in data["items"]])
        update_catalog_prices(data["items"])
        revision.pdf.save(f"{revision.number}.pdf", ContentFile(budget_pdf(revision)), save=True)
        return revision


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def format_money(value):
    return f"ARS {money(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def start_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.effective_message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    # An explicitly resumed AI draft may now enter the guided confirmation flow.
    ai_draft = context.user_data.get("ai_budget")
    resumed_ai_draft = bool(ai_draft)
    if not resumed_ai_draft and await offer_draft_actions(update.effective_message):
        return
    if ai_draft:
        checked = validate_candidate(ai_draft)
        if checked.get("plate"):
            existing_vehicle = await find_vehicle(normalize_plate(checked["plate"]))
            if existing_vehicle:
                fields = ("make", "model", "customer_type", "customer_name", "customer_phone")
                if any(checked.get(field) and checked[field] != getattr(existing_vehicle, field) for field in fields):
                    checked.setdefault("uncertainties", []).append(
                        "Los datos del cliente o vehículo contradicen el registro; confirma o corrige explícitamente."
                    )
        required = ("plate", "make", "model", "customer_type", "customer_name", "customer_phone",
                    "description", "labor_amount")
        incomplete = any(not checked.get(field) for field in required)
        invalid_items = any(not item.get("description", "").strip() or not item.get("quantity")
                            or item.get("unit_price") is None for item in checked.get("items", []))
        if (incomplete or invalid_items or (not checked.get("items") and not checked.get("labor_only")
                                            or checked.get("uncertainties"))):
            context.user_data["ai_budget"] = checked
            await show_ai_budget_draft(update.effective_message, checked)
            return
        ai_draft = checked
    context.user_data.clear()
    guided_draft = {"items": [], "confirmation_key": str(uuid.uuid4())}
    if ai_draft:
        vehicle = await find_vehicle(normalize_plate(ai_draft.get("plate", ""))) if ai_draft.get("plate") else None
        candidate_vehicle = None
        if not vehicle and all(ai_draft.get(key) for key in (
            "plate", "make", "model", "customer_type", "customer_name", "customer_phone"
        )):
            candidate_vehicle = {key: ai_draft[key] for key in (
                "plate", "make", "model", "customer_type", "customer_name", "customer_phone"
            )}
        if vehicle:
            guided_draft.update({
                "vehicle": vehicle,
                "description": ai_draft.get("description", ""),
                "labor_amount": Decimal(str(ai_draft["labor_amount"])) if ai_draft.get("labor_amount") is not None else None,
                "items": [
                    {"description": item["description"], "quantity": item["quantity"],
                     "unit_price": Decimal(str(item["unit_price"])),
                     "subtotal": money(Decimal(str(item["unit_price"])) * item["quantity"])}
                    for item in ai_draft.get("items", [])
                ],
            })
        elif candidate_vehicle:
            guided_draft.update({
                "vehicle_data": candidate_vehicle,
                "description": ai_draft.get("description", ""),
                "labor_amount": Decimal(str(ai_draft["labor_amount"])) if ai_draft.get("labor_amount") is not None else None,
                "items": [
                    {"description": item["description"], "quantity": item["quantity"],
                     "unit_price": Decimal(str(item["unit_price"])),
                     "subtotal": money(Decimal(str(item["unit_price"])) * item["quantity"])}
                    for item in ai_draft.get("items", [])
                ],
            })
        guided_draft["ai_source_draft"] = ai_draft
    context.user_data["budget"] = guided_draft
    context.user_data["budget"]["from_ai_draft"] = resumed_ai_draft
    context.user_data["budget_step"] = BUDGET_VEHICLE
    if (guided_draft.get("vehicle") or guided_draft.get("vehicle_data")) and guided_draft.get("description") and guided_draft.get("labor_amount") is not None:
        context.user_data["budget_step"] = None
        await show_budget_summary(update.effective_message, guided_draft)
    else:
        await update.effective_message.reply_text("Escribe la patente del vehículo para el presupuesto. Usa /cancelar para salir.")


async def start_revision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.effective_message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    budgets = await pending_budgets()
    if not budgets:
        await update.effective_message.reply_text("No hay presupuestos pendientes para corregir.")
        return
    keyboard = [[InlineKeyboardButton(
        f"{b.number} · v{b.version} · {b.vehicle.plate} · {format_money(b.total)}",
        callback_data=f"budget:revise:{b.pk}") ] for b in budgets]
    await update.effective_message.reply_text("Selecciona el presupuesto pendiente que deseas corregir:",
                                              reply_markup=InlineKeyboardMarkup(keyboard))


async def budget_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not is_authorized(update):
        await query.answer()
        await query.edit_message_text("Esta cuenta no está autorizada para operar el taller.")
        return
    await query.answer()
    action = query.data.removeprefix("budget:")
    draft = context.user_data.get("budget")
    if action.startswith("revise:"):
        try:
            budget = await get_budget_with_items(int(action.split(":", 1)[1]))
        except (TypeError, ValueError):
            budget = None
        if not budget or budget.status != Budget.Status.PENDING or await has_next_version(budget.pk):
            await query.edit_message_text("Ese presupuesto ya no está pendiente o ya tiene una versión posterior.")
            return
        context.user_data.clear()
        draft = {"items": [{"description": i.description, "quantity": i.quantity,
                            "unit_price": i.unit_price, "subtotal": i.subtotal} for i in budget.items.all()],
                 "confirmation_key": str(uuid.uuid4()), "vehicle": budget.vehicle,
                 "description": budget.description, "labor_amount": budget.labor_amount,
                 "revision_of": budget.pk}
        context.user_data["budget"] = draft
        context.user_data["budget_step"] = None
        await show_budget_summary(query.message, draft)
        return
    if action in {"catalog:accept", "catalog:change"}:
        if not draft or context.user_data.get("budget_step") != BUDGET_ITEM_PRICE:
            await query.edit_message_text("Esta sugerencia ya no está disponible. Continúa con /presupuesto.")
            return
        if action == "catalog:accept":
            price = draft.pop("suggested_price")
            await add_budget_item(draft, price)
            context.user_data["budget_step"] = BUDGET_ITEM_NAME
            await query.edit_message_text(
                f"Sugerencia aceptada: {format_money(price)}. Repuesto agregado. Escribe otro nombre o /listo."
            )
        else:
            draft.pop("suggested_price", None)
            await query.edit_message_text("Escribe el precio unitario elegido en ARS; la sugerencia no es una cotización actual.")
        return
    if action.startswith("confirm:"):
        key = action.split(":", 1)[1]
        existing = await find_budget_by_key(key)
        if existing:
            await query.edit_message_text(f"Presupuesto {existing.number} ya confirmado; no se creó otro.")
            context.user_data.clear()
            return
        if not draft or draft.get("confirmation_key") != key:
            await query.edit_message_text("Este resumen ya no está disponible. Inicia con /presupuesto.")
            return
        if draft.get("ai_source_draft", {}).get("uncertainties"):
            await query.edit_message_text("No se confirmó: primero resuelve las aclaraciones del borrador IA.")
            return
        try:
            data = {
                "confirmation_key": key, "vehicle": draft.get("vehicle"),
                "vehicle_data": draft.get("vehicle_data"), "description": draft.get("description"),
                "labor_amount": draft.get("labor_amount"), "items": draft.get("items"),
                "ai_source_draft": draft.get("ai_source_draft"),
            }
            data = validate_budget_data(data)
            if draft.get("revision_of"):
                budget = await save_budget_revision(draft["revision_of"], data)
            else:
                budget = await save_budget(data)
        except ValueError:
            if draft.get("revision_of"):
                await query.edit_message_text("No se creó la versión: el presupuesto ya no está pendiente.")
            else:
                await query.edit_message_text("No se confirmó: revisa los datos del borrador y vuelve a corregirlos.")
            context.user_data.clear()
            return
        except (InvalidOperation, KeyError, TypeError):
            await query.edit_message_text("No se confirmó: revisa los datos del borrador y vuelve a corregirlos.")
            context.user_data.clear()
            return
        try:
            with budget.pdf.open("rb") as pdf_file:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file,
                                                filename=f"{budget.number}.pdf")
            delivery = "PDF entregado por Telegram."
        except Exception:
            delivery = f"No se pudo entregar el PDF. Reintenta con /reenviar {budget.number}."
        await query.edit_message_text(f"Presupuesto {budget.number} · versión {budget.version} confirmada como pendiente por {format_money(budget.total)}. {delivery}")
        if draft.get("from_ai_draft"):
            await delete_active_draft()
        context.user_data.clear()
        return
    if not draft:
        await query.edit_message_text("No hay un presupuesto en preparación. Usa /presupuesto.")
        return
    if action == "description":
        draft["confirmation_key"] = str(uuid.uuid4())
        context.user_data["budget_step"] = BUDGET_DESCRIPTION
        await query.edit_message_text("Escribe la descripción del trabajo.")
    elif action == "items":
        draft["confirmation_key"] = str(uuid.uuid4())
        draft["items"] = []
        context.user_data["budget_step"] = BUDGET_ITEM_NAME
        await query.edit_message_text("Escribe el nombre del repuesto. Envía /listo cuando termines de agregarlos.")
    elif action == "labor":
        draft["confirmation_key"] = str(uuid.uuid4())
        context.user_data["budget_step"] = BUDGET_LABOR
        await query.edit_message_text("Escribe el importe total de mano de obra en ARS.")
    elif action == "cancel":
        context.user_data.clear()
        await query.edit_message_text("Presupuesto cancelado.")


def budget_total(draft):
    return money(sum((money(Decimal(item["quantity"]) * Decimal(item["unit_price"]))
                      for item in draft["items"]), Decimal("0")) + Decimal(draft["labor_amount"]))


async def show_budget_summary(message, draft):
    try:
        validated = validate_budget_data({
            "vehicle": draft.get("vehicle"), "vehicle_data": draft.get("vehicle_data"),
            "description": draft.get("description"), "labor_amount": draft.get("labor_amount"),
            "items": draft.get("items"),
        })
        if draft.get("ai_source_draft", {}).get("uncertainties"):
            raise ValueError("Quedan aclaraciones pendientes.")
        draft.update(validated)
    except (ValueError, InvalidOperation, TypeError):
        await message.reply_text("No se puede confirmar todavía: revisa los datos obligatorios, importes y repuestos del borrador.")
        return
    lines = ["Resumen del presupuesto:"]
    if draft.get("vehicle"):
        vehicle = draft["vehicle"]
        lines.append(f"Vehículo: {vehicle.plate} · {vehicle.make} {vehicle.model}")
        lines.append(f"Cliente: {vehicle.customer_name}")
    elif draft.get("vehicle_data"):
        vehicle = draft["vehicle_data"]
        lines.append(f"Vehículo: {vehicle['plate']} · {vehicle['make']} {vehicle['model']}")
        lines.append(f"Cliente: {vehicle['customer_name']}")
    lines.append(draft["description"])
    lines.extend(f"{item['description']}: {item['quantity']} × {format_money(item['unit_price'])} = {format_money(item['subtotal'])}" for item in draft["items"])
    lines.extend([f"Mano de obra: {format_money(draft['labor_amount'])}", f"TOTAL: {format_money(budget_total(draft))}"])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Editar descripción", callback_data="budget:description")],
        [InlineKeyboardButton("Editar repuestos", callback_data="budget:items")],
        [InlineKeyboardButton("Editar mano de obra", callback_data="budget:labor")],
        [InlineKeyboardButton("Confirmar", callback_data=f"budget:confirm:{draft['confirmation_key']}")],
        [InlineKeyboardButton("Cancelar", callback_data="budget:cancel")],
    ])
    await message.reply_text("\n".join(lines), reply_markup=keyboard)


async def budget_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.effective_message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    draft = context.user_data.get("budget")
    if not draft or context.user_data.get("budget_step") != BUDGET_ITEM_NAME or not draft["items"]:
        await update.effective_message.reply_text("Agrega al menos un repuesto antes de terminar. Usa /presupuesto para empezar.")
        return
    context.user_data["budget_step"] = BUDGET_LABOR
    await update.effective_message.reply_text("Escribe el importe total de mano de obra en ARS.")


async def cancel_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.effective_message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    context.user_data.clear()
    await update.effective_message.reply_text("Operación cancelada.")


@sync_to_async
def find_budget(number):
    return Budget.objects.filter(number=number).first()


async def resend_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.effective_message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("Uso: /reenviar P-000001")
        return
    budget = await find_budget(context.args[0])
    if not budget or not budget.pdf:
        await update.effective_message.reply_text("No encuentro ese presupuesto o todavía no tiene PDF.")
        return
    try:
        with budget.pdf.open("rb") as pdf_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file,
                                            filename=f"{budget.number}.pdf")
        await update.effective_message.reply_text(f"PDF de {budget.number} entregado.")
    except Exception:
        await update.effective_message.reply_text(f"No se pudo entregar. Puedes volver a intentar /reenviar {budget.number}.")


async def collect_budget_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not is_authorized(update):
        await message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        context.user_data.clear()
        return
    step = context.user_data.get("budget_step")
    if step is None:
        return
    value = (message.text or "").strip()
    draft = context.user_data["budget"]
    if step in {BUDGET_DESCRIPTION, BUDGET_ITEM_NAME}:
        if not value or len(value) > 2000:
            await message.reply_text("El dato es obligatorio y debe tener como máximo 2000 caracteres. Inténtalo de nuevo.")
            return
        if step == BUDGET_DESCRIPTION:
            draft["description"] = value
            context.user_data["budget_step"] = BUDGET_ITEM_NAME
            await message.reply_text("Escribe el nombre del primer repuesto.")
        else:
            draft["pending_item"] = value
            context.user_data["budget_step"] = BUDGET_ITEM_QUANTITY
            await message.reply_text("Escribe la cantidad (número entero mayor que cero).")
        return
    if step == BUDGET_VEHICLE:
        vehicle = await find_vehicle(normalize_plate(value))
        if not vehicle:
            await message.reply_text("No encuentro esa patente. Registra primero el vehículo con /vehiculo.")
            return
        draft["vehicle"] = vehicle
        context.user_data["budget_step"] = BUDGET_DESCRIPTION
        await message.reply_text("Escribe la descripción del trabajo.")
        return
    if step == BUDGET_ITEM_QUANTITY:
        if not value.isdigit() or int(value) <= 0:
            await message.reply_text("La cantidad debe ser un entero mayor que cero. Inténtalo de nuevo.")
            return
        draft["pending_quantity"] = int(value)
        context.user_data["budget_step"] = BUDGET_ITEM_PRICE
        part = await find_catalog_part(draft["pending_item"]) if draft.get("pending_item") else None
        if part:
            draft["pending_item"] = part.description
            draft["suggested_price"] = part.suggested_unit_price
            await message.reply_text(
                f"Precio guardado para {part.description}: {format_money(part.suggested_unit_price)}. "
                "Es una sugerencia, no una cotización actual garantizada por el proveedor. ¿Qué deseas hacer?",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Usar sugerencia", callback_data="budget:catalog:accept"),
                    InlineKeyboardButton("Cambiar precio", callback_data="budget:catalog:change"),
                ]]),
            )
        else:
            await message.reply_text("Escribe el precio unitario en ARS (se aceptan centavos; no uses separador de miles).")
        return
    if step in {BUDGET_ITEM_PRICE, BUDGET_LABOR}:
        try:
            amount = Decimal(value.replace(",", "."))
            if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
                raise InvalidOperation
            amount = money(amount)
        except (InvalidOperation, ValueError):
            await message.reply_text("Escribe un importe numérico válido y no negativo, con hasta dos decimales. Inténtalo de nuevo.")
            return
        if step == BUDGET_ITEM_PRICE:
            await add_budget_item(draft, amount)
            context.user_data["budget_step"] = BUDGET_ITEM_NAME
            await message.reply_text("Repuesto agregado. Escribe otro nombre o /listo para continuar.")
        else:
            if not draft.get("description") or not draft["items"]:
                await message.reply_text("Falta la descripción o al menos un repuesto. Usa /presupuesto para comenzar de nuevo.")
                return
            draft["labor_amount"] = amount
            context.user_data["budget_step"] = None
            await show_budget_summary(message, draft)


async def add_budget_item(draft, amount):
    quantity = draft.pop("pending_quantity")
    description = draft.pop("pending_item")
    draft.pop("suggested_price", None)
    draft["items"].append({"description": description, "quantity": quantity,
                           "unit_price": amount, "subtotal": money(amount * quantity)})


def is_authorized(update: Update) -> bool:
    user = update.effective_user
    return bool(user and settings.TELEGRAM_ALLOWED_USER_ID and str(user.id) == str(settings.TELEGRAM_ALLOWED_USER_ID))


async def reply_to_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return
    if not is_authorized(update):
        await message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    await message.reply_text(
        "Acceso autorizado. El bot del taller está conectado.\n"
        "Usa /vehiculo para registrar o consultar un vehículo."
    )
    await offer_draft_actions(message)


async def start_vehicle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.effective_message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    context.user_data.clear()
    context.user_data["vehicle_step"] = PLATE
    await update.effective_message.reply_text("Escribe la patente del vehículo. Puedes usar espacios o guiones.")


async def choose_customer_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not is_authorized(update):
        await query.answer()
        await query.edit_message_text("Esta cuenta no está autorizada para operar el taller.")
        return
    await query.answer()
    choice = query.data.removeprefix("customer:")
    if choice not in {Vehicle.CustomerType.MUNICIPALITY, Vehicle.CustomerType.PRIVATE}:
        return
    context.user_data["customer_type"] = choice
    context.user_data["vehicle_step"] = CUSTOMER_NAME
    await query.edit_message_text("Escribe el nombre del cliente.")


async def collect_vehicle_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not is_authorized(update):
        await message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        context.user_data.clear()
        return
    if context.user_data.get("budget_step") is not None:
        await collect_budget_field(update, context)
        return
    if context.user_data.get("ai_budget") is not None:
        await collect_ai_budget(update, context)
        return
    step = context.user_data.get("vehicle_step")
    if step is None:
        if settings.OPENAI_ENABLED and settings.OPENAI_API_KEY:
            if await offer_draft_actions(message):
                return
            context.user_data["ai_budget"] = {}
            await collect_ai_budget(update, context)
        return
    value = (message.text or "").strip()
    if not value:
        prompts = {
            PLATE: "La patente es obligatoria. Escríbela para continuar.",
            MAKE: "La marca es obligatoria. Escríbela para continuar.",
            MODEL: "El modelo es obligatorio. Escríbelo para continuar.",
            CUSTOMER_NAME: "El nombre del cliente es obligatorio. Escríbelo para continuar.",
            CUSTOMER_PHONE: "El teléfono es obligatorio. Escríbelo para continuar.",
        }
        await message.reply_text(prompts.get(step, "Selecciona un tipo de cliente con los botones."))
        return

    if step == PLATE:
        canonical = normalize_plate(value)
        if not canonical:
            await message.reply_text("La patente debe incluir al menos una letra o un número. Inténtalo de nuevo.")
            return
        existing = await find_vehicle(canonical)
        if existing:
            context.user_data.clear()
            await message.reply_text(format_vehicle(existing, "Vehículo existente recuperado; no se creó otro registro."))
            return
        context.user_data["plate"] = value
        context.user_data["vehicle_step"] = MAKE
        await message.reply_text("No existe todavía. Escribe la marca.")
    elif step == MAKE:
        context.user_data["make"] = value
        context.user_data["vehicle_step"] = MODEL
        await message.reply_text("Escribe el modelo.")
    elif step == MODEL:
        context.user_data["model"] = value
        context.user_data["vehicle_step"] = CUSTOMER_TYPE
        await message.reply_text(
            "Selecciona el tipo de cliente:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Municipalidad", callback_data="customer:municipalidad"),
                InlineKeyboardButton("Particular", callback_data="customer:particular"),
            ]]),
        )
    elif step == CUSTOMER_TYPE:
        await message.reply_text("Selecciona Municipalidad o Particular usando los botones.")
    elif step == CUSTOMER_NAME:
        context.user_data["customer_name"] = value
        context.user_data["vehicle_step"] = CUSTOMER_PHONE
        await message.reply_text("Escribe el teléfono del cliente.")
    elif step == CUSTOMER_PHONE:
        context.user_data["customer_phone"] = value
        try:
            vehicle = await save_vehicle({
                "plate": context.user_data["plate"],
                "make": context.user_data["make"],
                "model": context.user_data["model"],
                "customer_type": context.user_data["customer_type"],
                "customer_name": context.user_data["customer_name"],
                "customer_phone": value,
            })
        except IntegrityError:
            vehicle = await get_vehicle(normalize_plate(context.user_data["plate"]))
            context.user_data.clear()
            await message.reply_text(format_vehicle(vehicle, "La patente ya estaba registrada; recuperé el vehículo existente."))
            return
        context.user_data.clear()
        await message.reply_text(format_vehicle(vehicle, "Vehículo registrado correctamente."))


async def collect_ai_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not is_authorized(update):
        await message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    draft = context.user_data["ai_budget"]
    try:
        # Only the current message is transmitted; prior draft data remains local.
        candidate = await extract_budget(message.text or "", previous=draft)
    except Exception:
        await message.reply_text(
            "No pude interpretar el mensaje con IA. El borrador sigue intacto; puedes responder de nuevo "
            "o usar /cancelar y continuar con /presupuesto."
        )
        return
    draft = merge_correction(draft, candidate)
    context.user_data["ai_budget"] = draft
    await save_active_draft(draft)
    await show_ai_budget_draft(message, draft)


async def draft_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not is_authorized(update):
        await query.answer()
        await query.edit_message_text("Esta cuenta no está autorizada para operar el taller.")
        return
    await query.answer()
    action = query.data.removeprefix("draft:")
    if action == "discard":
        await delete_active_draft()
        context.user_data.pop("ai_budget", None)
        await query.edit_message_text("Borrador descartado y eliminado.")
    elif action == "continue":
        draft = await get_active_draft()
        if draft is None:
            await query.edit_message_text("El borrador ya no existe o expiró. Puedes iniciar uno nuevo.")
            return
        context.user_data.clear()
        context.user_data["ai_budget"] = draft
        await query.edit_message_text("Borrador recuperado. Responde las preguntas pendientes o envía una corrección.")
        await show_ai_budget_draft(query.message, draft)


async def show_ai_budget_draft(message, draft):
    """Show draft/missing fields only; never create a vehicle, catalog row, or budget here."""
    from tallerweb.models import normalize_plate

    draft.update(validate_candidate(draft))

    if draft.get("plate"):
        vehicle = await find_vehicle(normalize_plate(draft["plate"]))
        if vehicle:
            known = {"make": vehicle.make, "model": vehicle.model, "customer_type": vehicle.customer_type,
                     "customer_name": vehicle.customer_name, "customer_phone": vehicle.customer_phone}
            for key, value in known.items():
                if draft.get(key) and draft[key] != value:
                    draft.setdefault("uncertainties", []).append(f"{key}: el vehículo registrado tiene otro dato; confirma o corrige.")
                elif not draft.get(key):
                    draft[key] = value

    missing = []
    for key, label in (("plate", "patente"), ("make", "marca"), ("model", "modelo"),
                       ("customer_type", "tipo de cliente (Municipalidad o particular)"),
                       ("customer_name", "nombre del cliente"), ("customer_phone", "teléfono del cliente"),
                       ("description", "descripción del trabajo"), ("labor_amount", "importe total de mano de obra")):
        if not draft.get(key):
            missing.append(label)
    if not draft.get("items") and not draft.get("labor_only"):
        missing.append("repuestos o confirmar que es solo mano de obra")
    ambiguous = any(not item.get("description", "").strip() or item.get("quantity") is None
                    or item.get("unit_price") is None
                    for item in draft.get("items", []))
    if ambiguous:
        missing.append("aclarar descripción, cantidad y precio unitario de cada repuesto")
    if draft.get("items") and draft.get("labor_only"):
        missing.append("aclarar si se incluyen repuestos o el trabajo es solo mano de obra")
    missing.extend(draft.get("uncertainties", []))
    if missing:
        await message.reply_text("Para completar el borrador necesito: " + "; ".join(dict.fromkeys(missing)) + ".")
        return
    item_lines = []
    for item in draft.get("items", []):
        if item.get("unit_price") is not None:
            item_lines.append(f"{item['description']} · {item['quantity']} × ARS {item['unit_price']}")
        else:
            # Total-only prices cannot be safely converted to a unit price here.
            item_lines.append(f"{item['description']} · total informado ARS {item['total_price']} (requiere desglose unitario)")
    lines = ["Borrador (sin guardar):", f"Patente: {draft['plate']} · {draft['make']} {draft['model']}",
             f"Cliente: {draft['customer_name']} · {draft['customer_phone']}", f"Trabajo: {draft['description']}",
             *item_lines, f"Mano de obra: ARS {draft['labor_amount']}",
             "Revisa los datos y continúa con el flujo guiado /presupuesto para confirmar."]
    await message.reply_text("\n".join(lines))


async def start_ai_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.effective_message.reply_text("Esta cuenta no está autorizada para operar el taller.")
        return
    if not settings.OPENAI_ENABLED or not settings.OPENAI_API_KEY:
        await update.effective_message.reply_text("La interpretación con IA está deshabilitada; usa /presupuesto.")
        return
    if await offer_draft_actions(update.effective_message):
        return
    context.user_data.clear()
    context.user_data["ai_budget"] = {}
    await collect_ai_budget(update, context)


def format_vehicle(vehicle: Vehicle, heading: str) -> str:
    return (
        f"{heading}\nPatente: {vehicle.plate}\nMarca: {vehicle.make}\nModelo: {vehicle.model}\n"
        f"Cliente: {vehicle.get_customer_type_display()} — {vehicle.customer_name}\n"
        f"Teléfono: {vehicle.customer_phone}"
    )


class Command(BaseCommand):
    help = "Inicia el bot local de Telegram (requiere conexión a Internet)."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("Configura TELEGRAM_BOT_TOKEN en .env.")
        if not settings.TELEGRAM_ALLOWED_USER_ID:
            raise CommandError("Configura TELEGRAM_ALLOWED_USER_ID en .env.")
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", reply_to_authorized))
        application.add_handler(CommandHandler("vehiculo", start_vehicle))
        application.add_handler(CommandHandler("presupuesto", start_budget))
        application.add_handler(CommandHandler("borrador", start_ai_budget))
        application.add_handler(CommandHandler("corregir", start_revision))
        application.add_handler(CommandHandler("listo", budget_done))
        application.add_handler(CommandHandler("cancelar", cancel_budget))
        application.add_handler(CommandHandler("reenviar", resend_budget))
        application.add_handler(CallbackQueryHandler(choose_customer_type, pattern=r"^customer:"))
        application.add_handler(CallbackQueryHandler(draft_callback, pattern=r"^draft:"))
        application.add_handler(CallbackQueryHandler(budget_callback, pattern=r"^budget:"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_vehicle_field))
        self.stdout.write("Bot iniciado. Presiona Ctrl+C para detenerlo.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
