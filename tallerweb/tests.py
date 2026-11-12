from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from decimal import Decimal
from uuid import uuid4

from tallerweb.models import Budget, BudgetDraft, BudgetItem, CompletedWork, PartCatalog, Vehicle, normalize_plate


class AdministratorAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="admin", password="Strong-password-92")

    def test_dashboard_requires_login_and_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_valid_credentials_open_protected_dashboard(self):
        self.assertTrue(self.client.login(username="admin", password="Strong-password-92"))

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin")

    def test_invalid_credentials_do_not_open_dashboard(self):
        self.assertFalse(self.client.login(username="admin", password="incorrect"))

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)


class SharedVisualSystemTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="visual-admin", password="Strong-password-92")
        self.vehicle = Vehicle.objects.create(plate="VIS-001", make="Ford", model="Ranger",
                                              customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                              customer_name="Municipalidad", customer_phone="123")

    def test_all_four_pages_use_shared_identity_navigation_and_responsive_shell(self):
        login_response = self.client.get(reverse("login"))
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "Taller Norte")
        self.assertContains(login_response, 'name="viewport"')
        self.assertContains(login_response, 'class="site-nav"')
        self.assertContains(login_response, 'id="contenido"')
        self.assertContains(login_response, "tallerweb/site.css")

        self.client.force_login(self.user)
        urls = [
            reverse("dashboard"),
            reverse("vehicle_detail", args=[self.vehicle.pk]),
            reverse("monthly_summary"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Taller Norte")
                self.assertContains(response, 'name="viewport"')
                self.assertContains(response, 'class="site-nav"')
                self.assertContains(response, 'id="contenido"')
                self.assertContains(response, "tallerweb/site.css")

    def test_shared_shell_has_keyboard_skip_link_and_labeled_navigation(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, 'class="skip-link"')
        self.assertContains(response, 'aria-label="Navegación principal"')
        self.assertContains(response, "aria-current=\"page\"")
        self.assertContains(response, "Cerrar sesión")

    def test_login_and_dashboard_have_clear_page_and_filter_hierarchy(self):
        login = self.client.get(reverse("login"))
        self.assertContains(login, 'login-layout"')
        self.assertContains(login, 'autocomplete="username"')
        self.assertContains(login, 'autocomplete="current-password"')

        self.client.force_login(self.user)
        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, 'class="dashboard-heading"')
        self.assertContains(dashboard, 'class="filter-grid"')
        self.assertContains(dashboard, 'class="record-list"')

    def test_vehicle_history_groups_each_budget_and_labels_actions_and_amounts(self):
        budget = Budget.objects.create(vehicle=self.vehicle, number="P-VISUAL", description="Revisión",
                                       labor_amount=Decimal("1200.00"), total=Decimal("1200.00"))
        self.client.force_login(self.user)

        response = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))

        self.assertContains(response, 'class="vehicle-heading"')
        self.assertContains(response, 'class="budget-card"')
        self.assertContains(response, 'class="status-badge status-pendiente"')
        self.assertContains(response, 'aria-label="Acciones para P-VISUAL"')
        self.assertContains(response, "ARS 1200,00")

    def test_logout_closes_session(self):
        self.client.force_login(self.user)

        self.client.post(reverse("logout"))
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)


class TelegramAuthorizationTests(TestCase):
    def test_authorized_telegram_id_is_compared_exactly(self):
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import reply_to_authorized

        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.reply_text = AsyncMock()
        context = Mock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            import asyncio
            asyncio.run(reply_to_authorized(update, context))

        update.effective_message.reply_text.assert_awaited_once_with(
            "Acceso autorizado. El bot del taller está conectado.\n"
            "Usa /vehiculo para registrar o consultar un vehículo."
        )

    def test_other_telegram_id_is_rejected(self):
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import reply_to_authorized

        update = Mock()
        update.effective_user.id = 654321
        update.effective_message.reply_text = AsyncMock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            import asyncio
            asyncio.run(reply_to_authorized(update, Mock()))

        update.effective_message.reply_text.assert_awaited_once_with(
            "Esta cuenta no está autorizada para operar el taller."
        )


class BudgetAIExtractionTests(TestCase):
    def test_ai_correction_updates_only_explicit_fields_and_preserves_existing_draft(self):
        from tallerweb.budget_ai import merge_correction

        original = {
            "plate": "AA123BB", "description": "Cambio de frenos", "labor_amount": Decimal("40000"),
            "items": [{"description": "Pastillas", "quantity": 1, "unit_price": Decimal("30000")}],
            "uncertainties": [],
        }
        candidate = {"plate": None, "description": None, "labor_amount": Decimal("60000"),
                     "items": [], "uncertainties": []}

        corrected = merge_correction(original, candidate)

        self.assertEqual(corrected["labor_amount"], Decimal("60000"))
        self.assertEqual(corrected["plate"], "AA123BB")
        self.assertEqual(corrected["description"], "Cambio de frenos")
        self.assertEqual(corrected["items"], original["items"])

    def test_candidate_validation_rejects_invalid_values_without_writing_records(self):
        from tallerweb.budget_ai import validate_candidate

        candidate = validate_candidate({
            "items": [{"description": "Discos", "quantity": 0, "unit_price": "NaN", "total_price": None}],
            "uncertainties": [],
        })

        self.assertIsNone(candidate["items"][0]["quantity"])
        self.assertIsNone(candidate["items"][0]["unit_price"])
        self.assertTrue(candidate["uncertainties"])
        self.assertEqual(Vehicle.objects.count(), 0)
        self.assertEqual(Budget.objects.count(), 0)

    def test_real_extraction_is_disabled_by_default(self):
        import asyncio
        from unittest.mock import patch
        from tallerweb.budget_ai import extract_budget

        with patch("tallerweb.budget_ai.settings.OPENAI_ENABLED", False), \
             patch("tallerweb.budget_ai.AsyncOpenAI") as client:
            with self.assertRaises(RuntimeError):
                asyncio.run(extract_budget("mensaje"))
        client.assert_not_called()

    def test_ai_api_failure_keeps_existing_draft_and_offers_guided_flow(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import collect_ai_budget

        existing = {"plate": "AA123BB", "description": "Frenos", "items": [],
                    "uncertainties": ["falta precio"]}
        context = Mock()
        context.user_data = {"ai_budget": existing}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "actualiza el precio"
        update.effective_message.reply_text = AsyncMock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.extract_budget", new=AsyncMock(side_effect=TimeoutError)),
              patch("tallerweb.management.commands.runbot.save_active_draft", new=AsyncMock()) as save_draft):
            asyncio.run(collect_ai_budget(update, context))

        self.assertEqual(context.user_data["ai_budget"], existing)
        self.assertEqual(BudgetDraft.objects.count(), 0)
        self.assertEqual(Budget.objects.count(), 0)
        save_draft.assert_not_awaited()
        self.assertIn("borrador sigue intacto", update.effective_message.reply_text.await_args.args[0])


class BudgetDraftPersistenceTests(TestCase):
    def test_draft_is_json_persisted_and_expires_after_thirty_days(self):
        from datetime import timedelta
        from django.utils import timezone
        from tallerweb.management.commands.runbot import get_active_draft, save_active_draft

        value = {"description": "Cambio de filtro", "items": [], "amount": Decimal("125.50"),
                 "pending_question": "patente"}
        save_active_draft.__wrapped__(value)
        self.assertEqual(BudgetDraft.objects.count(), 1)
        self.assertEqual(get_active_draft.__wrapped__(), {
            "description": "Cambio de filtro", "items": [], "amount": "125.50", "pending_question": "patente"
        })

        BudgetDraft.objects.filter(slot="authorized").update(updated_at=timezone.now() - timedelta(days=31))
        self.assertIsNone(get_active_draft.__wrapped__())
        self.assertFalse(BudgetDraft.objects.exists())

    def test_discard_removes_only_draft_without_creating_domain_records(self):
        from tallerweb.management.commands.runbot import delete_active_draft, save_active_draft

        save_active_draft.__wrapped__({"plate": "AA123AA", "items": []})
        delete_active_draft.__wrapped__()
        self.assertFalse(BudgetDraft.objects.exists())
        self.assertEqual(Vehicle.objects.count(), 0)
        self.assertEqual(Budget.objects.count(), 0)
        self.assertEqual(PartCatalog.objects.count(), 0)


class VehicleModelTests(TestCase):
    def test_plate_normalization_ignores_case_spaces_and_hyphens(self):
        self.assertEqual(normalize_plate(" ab - 123 cd "), "AB123CD")

    def test_normalized_plate_prevents_duplicate_vehicle(self):
        Vehicle.objects.create(plate="AB-123-CD", make="Ford", model="Ranger", customer_type="municipalidad",
                               customer_name="Municipalidad", customer_phone="111")
        with self.assertRaises(IntegrityError):
            Vehicle.objects.create(plate="ab 123 cd", make="Ford", model="Ranger", customer_type="particular",
                                   customer_name="Cliente", customer_phone="222")


class VehicleWebTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="admin", password="Strong-password-92")
        self.vehicle = Vehicle.objects.create(plate="AA-123-AA", make="Toyota", model="Hilux",
                                              customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                              customer_name="Municipalidad", customer_phone="123")

    def test_vehicle_list_and_detail_require_login(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)
        self.assertEqual(self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk])).status_code, 302)

    def test_authenticated_admin_can_consult_vehicle_and_customer(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("dashboard")), "AA-123-AA")
        response = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))
        self.assertContains(response, "Municipalidad")
        self.assertContains(response, "123")

    def test_dashboard_filters_budget_date_plate_and_customer_as_intersection(self):
        from datetime import datetime, timezone

        private_vehicle = Vehicle.objects.create(plate="BB-456-BB", make="Ford", model="Ka",
                                                 customer_type=Vehicle.CustomerType.PRIVATE,
                                                 customer_name="Ana", customer_phone="456")
        matching = Budget.objects.create(vehicle=self.vehicle, number="P-MATCH", description="Dentro",
                                         labor_amount=Decimal("1"), total=Decimal("1"))
        Budget.objects.filter(pk=matching.pk).update(created_at=datetime(2025, 5, 10, 12, tzinfo=timezone.utc))
        other_type = Budget.objects.create(vehicle=private_vehicle, number="P-OTHER", description="Tipo",
                                           labor_amount=Decimal("1"), total=Decimal("1"))
        Budget.objects.filter(pk=other_type.pk).update(created_at=datetime(2025, 5, 10, 12, tzinfo=timezone.utc))
        outside = Budget.objects.create(vehicle=self.vehicle, number="P-OLD", description="Fecha",
                                        labor_amount=Decimal("1"), total=Decimal("1"))
        Budget.objects.filter(pk=outside.pk).update(created_at=datetime(2025, 4, 30, 12, tzinfo=timezone.utc))
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"), {"plate": "aa123aa", "customer_type": "municipalidad",
                                                            "date_from": "2025-05-10", "date_to": "2025-05-10"})
        self.assertContains(response, "P-MATCH")
        self.assertNotContains(response, "P-OTHER")
        self.assertNotContains(response, "P-OLD")
        self.assertContains(response, reverse("vehicle_detail", args=[self.vehicle.pk]))

    def test_dashboard_rejects_invalid_date_range_and_can_clear_filters(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"), {"date_from": "2025-06-02", "date_to": "2025-06-01"})
        self.assertContains(response, "La fecha de inicio debe ser anterior o igual a la fecha de fin.")
        self.assertContains(self.client.get(reverse("dashboard")), "AA-123-AA")

    def test_dashboard_plate_search_is_case_insensitive_and_no_results_are_explained(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("dashboard"), {"plate": "aa-123-aa"}), "AA-123-AA")
        self.assertContains(self.client.get(reverse("dashboard"), {"plate": "NO-EXISTE"}),
                            "No se encontraron vehículos ni presupuestos")


class TelegramVehicleFlowTests(TransactionTestCase):
    def test_empty_required_field_prompts_for_correction_without_saving(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import MAKE, collect_vehicle_field

        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "   "
        update.effective_message.reply_text = AsyncMock()
        context = Mock()
        context.user_data = {"vehicle_step": MAKE, "plate": "AA123AA"}
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(collect_vehicle_field(update, context))

        update.effective_message.reply_text.assert_awaited_once_with("La marca es obligatoria. Escríbela para continuar.")
        self.assertEqual(context.user_data["vehicle_step"], MAKE)
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_authorized_user_can_register_municipal_and_private_vehicles(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import (
            CUSTOMER_NAME, CUSTOMER_PHONE, CUSTOMER_TYPE, MAKE, MODEL, PLATE,
            choose_customer_type, collect_vehicle_field,
        )

        async def send_text(text, state):
            update = Mock()
            update.effective_user.id = 123456
            update.effective_message.text = text
            update.effective_message.reply_text = AsyncMock()
            context.user_data = state
            await collect_vehicle_field(update, context)

        async def run_registration(customer_type, plate):
            state = {"vehicle_step": PLATE}
            await send_text(plate, state)
            await send_text("Toyota", state)
            await send_text("Hilux", state)

            callback_update = Mock()
            callback_update.effective_user.id = 123456
            callback_update.callback_query.data = f"customer:{customer_type}"
            callback_update.callback_query.answer = AsyncMock()
            callback_update.callback_query.edit_message_text = AsyncMock()
            context.user_data = state
            await choose_customer_type(callback_update, context)
            await send_text(f"Cliente {plate}", state)
            await send_text("555-0100", state)

        context = Mock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(run_registration("municipalidad", "MUNI-001"))
            asyncio.run(run_registration("particular", "PRIV-001"))

        self.assertEqual(Vehicle.objects.count(), 2)
        self.assertEqual(set(Vehicle.objects.values_list("customer_type", flat=True)), {"municipalidad", "particular"})

    def test_authorized_user_recovers_existing_vehicle_by_normalized_plate(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import PLATE, collect_vehicle_field

        vehicle = Vehicle.objects.create(plate="AA-123-BB", make="Fiat", model="Cronos",
                                         customer_type=Vehicle.CustomerType.PRIVATE,
                                         customer_name="Ana", customer_phone="456")
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = " aa 123 bb "
        update.effective_message.reply_text = AsyncMock()
        context = Mock()
        context.user_data = {"vehicle_step": PLATE}
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(collect_vehicle_field(update, context))

        self.assertEqual(Vehicle.objects.count(), 1)
        self.assertIn("Ana", update.effective_message.reply_text.await_args.args[0])
        self.assertIn("recuperado", update.effective_message.reply_text.await_args.args[0])
        self.assertEqual(context.user_data, {})


class BudgetModelAndWebTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="budget-admin", password="Strong-password-92")
        self.vehicle = Vehicle.objects.create(plate="BB-123-CC", make="Ford", model="Ranger",
                                              customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                              customer_name="Municipalidad", customer_phone="123")

    def test_budget_total_preserves_cents_and_main_example(self):
        from tallerweb.management.commands.runbot import budget_total

        draft = {"items": [{"quantity": 2, "unit_price": Decimal("15000.00"), "subtotal": Decimal("30000.00")}],
                 "labor_amount": Decimal("40000.00")}
        self.assertEqual(budget_total(draft), Decimal("70000.00"))
        draft["items"] = [{"quantity": 3, "unit_price": Decimal("10.15"), "subtotal": Decimal("30.45")}]
        draft["labor_amount"] = Decimal("0.10")
        draft["items"][0]["subtotal"] = Decimal("900.00")
        self.assertEqual(budget_total(draft), Decimal("30.55"))

    def test_confirmation_key_replay_returns_one_persisted_budget(self):
        from tallerweb.management.commands.runbot import save_budget

        key = uuid4()
        data = {"confirmation_key": key, "vehicle": self.vehicle, "description": "Cambio de aceite",
                "labor_amount": Decimal("40000.00"), "total": Decimal("70000.00"),
                "items": [{"description": "Filtro", "quantity": 2, "unit_price": Decimal("15000.00"),
                           "subtotal": Decimal("30000.00")}]}
        first = save_budget.__wrapped__(data)
        second = save_budget.__wrapped__(data)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Budget.objects.count(), 1)
        self.assertEqual(first.items.count(), 1)

    def test_confirming_new_ai_vehicle_creates_vehicle_budget_and_catalog_together(self):
        from tallerweb.management.commands.runbot import save_budget

        data = {
            "confirmation_key": uuid4(), "vehicle": None,
            "vehicle_data": {"plate": "CC-456-DD", "make": "Toyota", "model": "Hilux",
                             "customer_type": "particular", "customer_name": "Ana", "customer_phone": "555"},
            "description": "Cambio de filtro", "labor_amount": Decimal("1000.00"),
            "total": Decimal("2500.00"),
            "items": [{"description": "Filtro", "quantity": 1, "unit_price": Decimal("1500.00"),
                       "subtotal": Decimal("1500.00")}],
        }

        budget = save_budget.__wrapped__(data)

        self.assertEqual(Vehicle.objects.filter(normalized_plate="CC456DD").count(), 1)
        self.assertEqual(budget.vehicle.customer_name, "Ana")
        self.assertEqual(PartCatalog.objects.get(description="Filtro").suggested_unit_price, Decimal("1500.00"))
        self.assertTrue(budget.pdf)

    def test_summary_allows_correcting_description_before_confirmation(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import BUDGET_DESCRIPTION, budget_callback, collect_budget_field

        context = Mock()
        context.user_data = {"budget": {"description": "Descripción inicial", "items": [],
                                        "confirmation_key": str(uuid4())}}
        query_update = Mock()
        query_update.effective_user.id = 123456
        query_update.callback_query.data = "budget:description"
        query_update.callback_query.answer = AsyncMock()
        query_update.callback_query.edit_message_text = AsyncMock()
        text_update = Mock()
        text_update.effective_user.id = 123456
        text_update.effective_message.text = "Descripción corregida"
        text_update.effective_message.reply_text = AsyncMock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(budget_callback(query_update, context))
            self.assertEqual(context.user_data["budget_step"], BUDGET_DESCRIPTION)
            context.user_data["budget"]["items"] = [{"description": "Filtro", "quantity": 1,
                                                       "unit_price": Decimal("1.00"), "subtotal": Decimal("1.00")}]
            context.user_data["budget"]["labor_amount"] = Decimal("0.00")
            asyncio.run(collect_budget_field(text_update, context))
        self.assertEqual(context.user_data["budget"]["description"], "Descripción corregida")

    def test_budget_input_rejects_nonpositive_quantity_and_negative_amount(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import BUDGET_ITEM_QUANTITY, BUDGET_ITEM_PRICE, collect_budget_field

        context = Mock()
        context.user_data = {"budget_step": BUDGET_ITEM_QUANTITY, "budget": {"items": []}}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "0"
        update.effective_message.reply_text = AsyncMock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(collect_budget_field(update, context))
            self.assertEqual(context.user_data["budget_step"], BUDGET_ITEM_QUANTITY)
            update.effective_message.text = "1"
            asyncio.run(collect_budget_field(update, context))
            context.user_data["budget"]["pending_item"] = "Filtro"
            update.effective_message.text = "-1"
            asyncio.run(collect_budget_field(update, context))
        self.assertEqual(context.user_data["budget_step"], BUDGET_ITEM_PRICE)
        self.assertEqual(context.user_data["budget"]["items"], [])

    def test_admin_sees_budget_breakdown_in_vehicle_history(self):
        budget = Budget.objects.create(vehicle=self.vehicle, number="P-000001", description="Cambio de aceite",
                                       labor_amount=Decimal("40000.00"), total=Decimal("70000.00"))
        BudgetItem.objects.create(budget=budget, description="Filtro", quantity=2,
                                  unit_price=Decimal("15000.00"), subtotal=Decimal("30000.00"))
        response = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))
        self.assertContains(response, "P-000001")
        self.assertContains(response, "Cambio de aceite")
        self.assertContains(response, "Filtro")
        self.assertContains(response, "70000,00")

    def test_admin_can_approve_or_reject_only_current_pending_version(self):
        from tempfile import TemporaryDirectory
        from tallerweb.management.commands.runbot import save_budget

        self.client.force_login(self.user)
        for decision, expected in (("aprobado", Budget.Status.APPROVED),
                                   ("rechazado", Budget.Status.REJECTED)):
            with self.subTest(decision=decision), TemporaryDirectory() as media_dir, \
                    override_settings(MEDIA_ROOT=media_dir):
                budget = save_budget.__wrapped__({
                    "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Trabajo",
                    "labor_amount": Decimal("10.00"), "total": Decimal("10.00"), "items": [],
                })
                with budget.pdf.open("rb") as pdf_file:
                    pdf_before = pdf_file.read()
                response = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))
                self.assertContains(response, "Pendiente")
                self.assertContains(response, "Marcar como aprobado")
                response = self.client.post(reverse("decide_budget", args=[budget.pk]), {"decision": decision})
                self.assertRedirects(response, reverse("vehicle_detail", args=[self.vehicle.pk]))
                budget.refresh_from_db()
                self.assertEqual(budget.status, expected)
                with budget.pdf.open("rb") as pdf_file:
                    self.assertEqual(pdf_file.read(), pdf_before)
                self.assertEqual(budget.total, Decimal("10.00"))

    def test_approved_budget_can_be_closed_without_changing_snapshot_and_replay_is_idempotent(self):
        from tempfile import TemporaryDirectory
        from tallerweb.management.commands.runbot import save_budget

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            budget = save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Reparación",
                "labor_amount": Decimal("40000.00"), "total": Decimal("70000.00"),
                "items": [{"description": "Filtro", "quantity": 2, "unit_price": Decimal("15000.00"),
                           "subtotal": Decimal("30000.00")}],
            })
            Budget.objects.filter(pk=budget.pk).update(status=Budget.Status.APPROVED)
            with budget.pdf.open("rb") as handle:
                original_pdf = handle.read()
            self.client.force_login(self.user)
            url = reverse("complete_work", args=[budget.pk])
            payload = {"final_amount": "75000", "item_description": ["Filtro", "Bujía"],
                       "item_quantity": ["1", "4"]}
            self.assertRedirects(self.client.post(url, payload), reverse("vehicle_detail", args=[self.vehicle.pk]))
            self.assertRedirects(self.client.post(url, payload), reverse("vehicle_detail", args=[self.vehicle.pk]))
            budget.refresh_from_db()
            self.assertEqual(budget.status, Budget.Status.COMPLETED)
            self.assertEqual(budget.total, Decimal("70000.00"))
            self.assertEqual(budget.items.get().description, "Filtro")
            self.assertEqual(budget.completed_work.final_amount, Decimal("75000.00"))
            self.assertEqual(budget.completed_work.items.count(), 2)
            with budget.pdf.open("rb") as handle:
                self.assertEqual(handle.read(), original_pdf)
            self.assertEqual(budget.completed_work.items.get(description="Bujía").quantity, 4)
            self.assertContains(self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk])), "Importe final cobrado")

    def test_work_closure_rejects_invalid_amount_and_nonapproved_budget(self):
        budget = Budget.objects.create(vehicle=self.vehicle, number="P-CIERRE", description="Trabajo",
                                       labor_amount=Decimal("0"), total=Decimal("100"))
        self.client.force_login(self.user)
        url = reverse("complete_work", args=[budget.pk])
        for status, amount in ((Budget.Status.PENDING, "100"), (Budget.Status.REJECTED, "100"),
                               (Budget.Status.APPROVED, "-1"), (Budget.Status.APPROVED, "abc")):
            with self.subTest(status=status, amount=amount):
                Budget.objects.filter(pk=budget.pk).update(status=status)
                self.client.post(url, {"final_amount": amount})
                budget.refresh_from_db()
                self.assertFalse(hasattr(budget, "completed_work"))
                self.assertEqual(budget.status, status)

    def test_historical_version_cannot_be_decided(self):
        from tempfile import TemporaryDirectory
        from tallerweb.management.commands.runbot import save_budget, save_budget_revision

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            original = save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Original",
                "labor_amount": Decimal("1.00"), "total": Decimal("1.00"), "items": [],
            })
            current = save_budget_revision.__wrapped__(original.pk, {
                "confirmation_key": uuid4(), "description": "Corregido", "labor_amount": Decimal("2.00"),
                "total": Decimal("2.00"), "items": [],
            })
        self.client.force_login(self.user)
        response = self.client.post(reverse("decide_budget", args=[original.pk]), {"decision": "aprobado"})
        self.assertEqual(response.status_code, 404)
        original.refresh_from_db()
        self.assertEqual(original.status, Budget.Status.PENDING)
        self.assertEqual(current.status, Budget.Status.PENDING)

    def test_current_revision_can_be_decided_and_closed(self):
        from tempfile import TemporaryDirectory
        from tallerweb.management.commands.runbot import save_budget, save_budget_revision

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            original = save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Original",
                "labor_amount": Decimal("1.00"), "total": Decimal("1.00"), "items": [],
            })
            current = save_budget_revision.__wrapped__(original.pk, {
                "confirmation_key": uuid4(), "description": "Corregido", "labor_amount": Decimal("2.00"),
                "total": Decimal("2.00"), "items": [],
            })

        self.client.force_login(self.user)
        history = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))
        self.assertContains(history, f'action="{reverse("decide_budget", args=[current.pk])}"')
        self.assertNotContains(history, f'action="{reverse("decide_budget", args=[original.pk])}"')
        response = self.client.post(reverse("decide_budget", args=[current.pk]), {"decision": "aprobado"})
        self.assertRedirects(response, reverse("vehicle_detail", args=[self.vehicle.pk]))
        current.refresh_from_db()
        self.assertEqual(current.status, Budget.Status.APPROVED)
        history = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))
        self.assertContains(history, f'action="{reverse("complete_work", args=[current.pk])}"')
        self.assertNotContains(history, f'action="{reverse("complete_work", args=[original.pk])}"')

        response = self.client.post(reverse("complete_work", args=[current.pk]), {"final_amount": "2.00"})
        self.assertRedirects(response, reverse("vehicle_detail", args=[self.vehicle.pk]))
        current.refresh_from_db()
        self.assertEqual(current.status, Budget.Status.COMPLETED)

    def test_revision_started_before_decision_is_rejected_at_confirmation(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tempfile import TemporaryDirectory
        from tallerweb.management.commands.runbot import save_budget

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            original = save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Original",
                "labor_amount": Decimal("1.00"), "total": Decimal("1.00"), "items": [],
            })
        self.client.force_login(self.user)
        self.client.post(reverse("decide_budget", args=[original.pk]), {"decision": "rechazado"})

        context = Mock()
        key = str(uuid4())
        context.user_data = {"budget": {"revision_of": original.pk, "confirmation_key": key,
                                         "vehicle": self.vehicle, "description": "Corregido",
                                         "labor_amount": Decimal("2.00"), "items": []}}
        update = Mock()
        update.effective_user.id = 123456
        update.callback_query.data = f"budget:confirm:{key}"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        from tallerweb.management.commands.runbot import budget_callback
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.find_budget_by_key", new=AsyncMock(return_value=None)),
              patch("tallerweb.management.commands.runbot.save_budget_revision",
                    new=AsyncMock(side_effect=ValueError("Solo se pueden crear versiones de presupuestos pendientes.")))):
            asyncio.run(budget_callback(update, context))

        update.callback_query.edit_message_text.assert_awaited_once_with(
            "No se creó la versión: el presupuesto ya no está pendiente.")
        self.assertEqual(Budget.objects.count(), 1)

    def test_pdf_is_generated_and_download_requires_login(self):
        from tempfile import TemporaryDirectory
        from tallerweb.management.commands.runbot import save_budget

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            budget = save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle,
                "description": "Cambio de aceite", "labor_amount": Decimal("40000.00"),
                "total": Decimal("70000.00"),
                "items": [{"description": "Filtro", "quantity": 2,
                           "unit_price": Decimal("15000.00"), "subtotal": Decimal("30000.00")}],
            })
            self.assertTrue(budget.pdf)
            with budget.pdf.open("rb") as handle:
                self.assertTrue(handle.read(8).startswith(b"%PDF-"))
            url = reverse("budget_pdf_download", args=[budget.pk])
            self.assertEqual(self.client.get(url).status_code, 302)
            self.client.force_login(self.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/pdf")
            self.assertIn(f'{budget.number}.pdf', response["Content-Disposition"])
            response.close()

    def test_revision_keeps_previous_snapshot_and_both_pdfs_downloadable(self):
        from tempfile import TemporaryDirectory
        from tallerweb.management.commands.runbot import save_budget, save_budget_revision

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            original = save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Reparación inicial",
                "labor_amount": Decimal("40000.00"), "total": Decimal("70000.00"),
                "items": [{"description": "Filtro", "quantity": 2, "unit_price": Decimal("15000.00"),
                           "subtotal": Decimal("30000.00")}],
            })
            with original.pdf.open("rb") as handle:
                original_pdf = handle.read()
            revision = save_budget_revision.__wrapped__(original.pk, {
                "confirmation_key": uuid4(), "description": "Reparación corregida",
                "labor_amount": Decimal("42000.00"), "total": Decimal("72000.00"),
                "items": [{"description": "Filtro", "quantity": 2, "unit_price": Decimal("15000.00"),
                           "subtotal": Decimal("30000.00")}],
            })
            with original.pdf.open("rb") as handle:
                self.assertEqual(handle.read(), original_pdf)
            with revision.pdf.open("rb") as handle:
                self.assertTrue(handle.read().startswith(b"%PDF-"))
            self.client.force_login(self.user)
            response = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))
            self.assertContains(response, "Histórica")
            self.assertContains(response, "VIGENTE")
            for budget in (original, revision):
                downloaded = self.client.get(reverse("budget_pdf_download", args=[budget.pk]))
                self.assertEqual(downloaded.status_code, 200)
                self.assertTrue(b"".join(downloaded.streaming_content).startswith(b"%PDF-"))
                downloaded.close()

        original.refresh_from_db()
        self.assertEqual(revision.previous_version_id, original.pk)
        self.assertEqual(revision.version, 2)
        self.assertEqual(original.total, Decimal("70000.00"))
        self.assertEqual(revision.total, Decimal("72000.00"))
        self.assertEqual(original.items.get().unit_price, Decimal("15000.00"))
        self.assertEqual(revision.items.get().unit_price, Decimal("15000.00"))

    def test_revision_save_rejects_budget_that_is_not_pending(self):
        from tallerweb.management.commands.runbot import save_budget, save_budget_revision

        original = save_budget.__wrapped__({
            "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Trabajo",
            "labor_amount": Decimal("0.00"), "total": Decimal("1.00"),
            "items": [{"description": "Filtro", "quantity": 1, "unit_price": Decimal("1.00"),
                       "subtotal": Decimal("1.00")}],
        })
        Budget.objects.filter(pk=original.pk).update(status="aprobado")
        with self.assertRaises(ValueError):
            save_budget_revision.__wrapped__(original.pk, {
                "confirmation_key": uuid4(), "description": "Cambio", "labor_amount": Decimal("0.00"),
                "total": Decimal("1.00"), "items": [],
            })
        self.assertEqual(Budget.objects.count(), 1)


class PartCatalogTests(TransactionTestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(plate="CC-123-DD", make="Ford", model="Ranger",
                                              customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                              customer_name="Municipalidad", customer_phone="123")

    def test_manual_price_is_saved_and_existing_budget_keeps_its_price(self):
        from tempfile import TemporaryDirectory
        from django.test import override_settings
        from tallerweb.management.commands.runbot import save_budget, save_catalog_price

        save_catalog_price.__wrapped__("Filtro de aceite", Decimal("15000.00"))
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            old_budget = save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Cambio de filtro",
                "labor_amount": Decimal("0.00"), "total": Decimal("15000.00"),
                "items": [{"description": "Filtro de aceite", "quantity": 1,
                           "unit_price": Decimal("15000.00"), "subtotal": Decimal("15000.00")}],
            })
            with old_budget.pdf.open("rb") as pdf_file:
                old_pdf = pdf_file.read()

            save_catalog_price.__wrapped__("filtro de aceite", Decimal("18000.00"))

            with old_budget.pdf.open("rb") as pdf_file:
                self.assertEqual(pdf_file.read(), old_pdf)

        self.assertEqual(PartCatalog.objects.get().suggested_unit_price, Decimal("18000.00"))
        self.assertEqual(old_budget.items.get().unit_price, Decimal("15000.00"))
        self.assertEqual(old_budget.total, Decimal("15000.00"))

    def test_bot_offers_catalog_price_and_acceptance_uses_it(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import BUDGET_ITEM_QUANTITY, budget_callback, collect_budget_field

        PartCatalog.objects.create(description="Filtro", suggested_unit_price=Decimal("18000.00"))
        context = Mock()
        context.user_data = {"budget_step": BUDGET_ITEM_QUANTITY,
                             "budget": {"items": [], "pending_item": "filtro"}}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "1"
        update.effective_message.reply_text = AsyncMock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(collect_budget_field(update, context))
            self.assertIn("sugerencia, no una cotización actual", update.effective_message.reply_text.await_args.args[0])
            query_update = Mock()
            query_update.effective_user.id = 123456
            query_update.callback_query.data = "budget:catalog:accept"
            query_update.callback_query.answer = AsyncMock()
            query_update.callback_query.edit_message_text = AsyncMock()
            asyncio.run(budget_callback(query_update, context))

        self.assertEqual(context.user_data["budget"]["items"][0]["unit_price"], Decimal("18000.00"))
        self.assertEqual(PartCatalog.objects.get().suggested_unit_price, Decimal("18000.00"))


class MonthlySummaryTests(TransactionTestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="summary-admin", password="Strong-password-92")
        self.client.force_login(self.admin)
        self.vehicle = Vehicle.objects.create(plate="SUM-001", make="Ford", model="Ranger",
                                              customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                              customer_name="Municipalidad", customer_phone="123")

    def add_budget(self, number, status, amount=None, closed_at=None, previous_version=None):
        budget = Budget.objects.create(vehicle=self.vehicle, number=number, description="Trabajo",
                                       labor_amount=Decimal("40000"), total=Decimal("70000"),
                                       status=status, previous_version=previous_version,
                                       version=2 if previous_version else 1)
        if amount is not None:
            work = CompletedWork.objects.create(budget=budget, final_amount=Decimal(amount))
            if closed_at:
                CompletedWork.objects.filter(pk=work.pk).update(closed_at=closed_at)
        return budget

    def test_summary_uses_final_amount_once_and_groups_month_boundaries(self):
        from datetime import datetime
        from django.utils import timezone as django_timezone

        old_version = self.add_budget("P-OLD-SUM", Budget.Status.PENDING)
        revised = self.add_budget("P-NEW-SUM", Budget.Status.COMPLETED, "75000.00",
                                  django_timezone.make_aware(datetime(2025, 5, 31, 23, 59)), old_version)
        self.add_budget("P-MAY-SECOND", Budget.Status.COMPLETED, "5000.00",
                        django_timezone.make_aware(datetime(2025, 5, 1, 0, 0)))
        self.add_budget("P-JUNE", Budget.Status.COMPLETED, "12500.00",
                        django_timezone.make_aware(datetime(2025, 6, 1, 0, 0)))
        self.add_budget("P-APPROVED", Budget.Status.APPROVED)
        self.add_budget("P-REJECTED", Budget.Status.REJECTED)

        may = self.client.get(reverse("monthly_summary"), {"month": "05", "year": "2025"})
        self.assertContains(may, '<p class="summary-value">2</p>')
        self.assertContains(may, "<span class=\"summary-currency\">ARS</span> 80000,00")
        self.assertNotContains(may, "145000")
        june = self.client.get(reverse("monthly_summary"), {"month": "6", "year": "2025"})
        self.assertContains(june, '<p class="summary-value">1</p>')
        self.assertContains(june, "<span class=\"summary-currency\">ARS</span> 12500,00")
        empty = self.client.get(reverse("monthly_summary"), {"month": "07", "year": "2025"})
        self.assertContains(empty, '<p class="summary-value">0</p>')
        self.assertContains(empty, "<span class=\"summary-currency\">ARS</span> 0,00")
        self.assertEqual(revised.previous_version_id, old_version.pk)

    def test_summary_requires_login_and_rejects_invalid_month(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("monthly_summary")).status_code, 302)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("monthly_summary"), {"month": "13", "year": "2025"})
        self.assertContains(response, "Selecciona un mes y año válidos.")

    def test_monthly_summary_presents_period_totals_empty_state_and_validation_error(self):
        empty = self.client.get(reverse("monthly_summary"), {"month": "07", "year": "2025"})

        self.assertContains(empty, 'class="summary-grid"')
        self.assertContains(empty, 'class="summary-card"')
        self.assertContains(empty, 'id="summary-month"')
        self.assertContains(empty, 'id="summary-year"')
        self.assertContains(empty, "El resumen se agrupa por la fecha de cierre del trabajo")
        self.assertContains(empty, 'class="empty-state summary-empty"')
        self.assertContains(empty, "No hay trabajos terminados en este período.")

        invalid = self.client.get(reverse("monthly_summary"), {"month": "13", "year": "2025"})
        self.assertContains(invalid, 'role="alert"')
        self.assertContains(invalid, "Selecciona un mes y año válidos.")

    def test_entered_replacement_updates_draft_but_not_catalog_before_confirmation(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import BUDGET_ITEM_PRICE, budget_callback, collect_budget_field

        PartCatalog.objects.create(description="Filtro", suggested_unit_price=Decimal("15000.00"))
        context = Mock()
        context.user_data = {"budget_step": BUDGET_ITEM_PRICE,
                             "budget": {"items": [], "pending_item": "Filtro", "pending_quantity": 1,
                                        "suggested_price": Decimal("15000.00")}}
        callback_update = Mock()
        callback_update.effective_user.id = 123456
        callback_update.callback_query.data = "budget:catalog:change"
        callback_update.callback_query.answer = AsyncMock()
        callback_update.callback_query.edit_message_text = AsyncMock()
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "18000"
        update.effective_message.reply_text = AsyncMock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(budget_callback(callback_update, context))
            asyncio.run(collect_budget_field(update, context))

        self.assertEqual(context.user_data["budget"]["items"][0]["unit_price"], Decimal("18000.00"))
        self.assertEqual(PartCatalog.objects.get().suggested_unit_price, Decimal("15000.00"))

    def test_editing_summary_invalidates_the_previous_confirmation_button(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import budget_callback

        old_key = str(uuid4())
        context = Mock()
        context.user_data = {"budget": {"description": "Trabajo", "items": [], "confirmation_key": old_key}}
        update = Mock()
        update.effective_user.id = 123456
        update.callback_query.data = "budget:description"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        with patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"):
            asyncio.run(budget_callback(update, context))

        self.assertNotEqual(context.user_data["budget"]["confirmation_key"], old_key)
