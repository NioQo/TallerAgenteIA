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


class ThemeToggleTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="theme-admin", password="Strong-password-92")
        self.vehicle = Vehicle.objects.create(plate="THM-001", make="Ford", model="Ranger",
                                              customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                              customer_name="Municipalidad", customer_phone="123")

    def test_toggle_and_no_flash_script_on_every_page(self):
        urls = [reverse("login")]
        self.client.force_login(self.user)
        urls += [reverse("dashboard"), reverse("vehicle_detail", args=[self.vehicle.pk]), reverse("monthly_summary")]
        self.client.logout()
        for url in urls:
            with self.subTest(url=url):
                if url != reverse("login"):
                    self.client.force_login(self.user)
                content = self.client.get(url).content.decode()
                self.assertIn('id="theme-toggle"', content)
                self.assertIn("tallerweb/theme.js", content)
                # Inline script must run before the stylesheet to avoid a flash.
                self.assertLess(content.index("ftm-theme"), content.index("tallerweb/site.css"))
                self.client.logout()

    def test_theme_assets_have_dark_styles_and_persistence(self):
        from django.contrib.staticfiles import finders
        css = open(finders.find("tallerweb/site.css"), encoding="utf-8").read()
        js = open(finders.find("tallerweb/theme.js"), encoding="utf-8").read()
        self.assertIn('[data-theme="dark"]', css)
        self.assertIn("localStorage", js)
        self.assertIn("Modo claro", js)


class SharedVisualSystemTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="visual-admin", password="Strong-password-92")
        self.vehicle = Vehicle.objects.create(plate="VIS-001", make="Ford", model="Ranger",
                                              customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                              customer_name="Municipalidad", customer_phone="123")

    def test_all_four_pages_use_shared_identity_navigation_and_responsive_shell(self):
        login_response = self.client.get(reverse("login"))
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "FT MOTORS")
        self.assertContains(login_response, "Tu vehículo en manos expertas")
        self.assertContains(login_response, "+54 9 11 5429 6017")
        self.assertContains(login_response, "Av. Dardo Rocha 1891 (Ruta 25), Pilar, Buenos Aires")
        self.assertNotContains(login_response, "Taller Norte")
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
                self.assertContains(response, "FT MOTORS")
                self.assertContains(response, "+54 9 11 5429 6017")
                self.assertNotContains(response, "Taller Norte")
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
    def test_ai_draft_shows_formatted_part_subtotals_and_estimated_total(self):
        import asyncio
        from unittest.mock import AsyncMock, patch
        from tallerweb.management.commands.runbot import show_ai_budget_draft

        draft = {
            "plate": "AA123BB", "make": "Toyota", "model": "Corolla",
            "customer_type": Vehicle.CustomerType.PRIVATE,
            "customer_name": "Cliente Demo", "customer_phone": "555",
            "description": "Cambio de frenos", "labor_amount": Decimal("25000"),
            "items": [
                {"description": "Discos", "quantity": 2, "unit_price": Decimal("30000"), "total_price": None},
                {"description": "Pastillas", "quantity": 1, "unit_price": Decimal("20000"), "total_price": None},
            ],
            "labor_only": False, "uncertainties": [],
        }
        message = type("Message", (), {"reply_text": AsyncMock()})()

        with patch("tallerweb.management.commands.runbot.find_vehicle", new=AsyncMock(return_value=None)):
            asyncio.run(show_ai_budget_draft(message, draft))

        output = message.reply_text.await_args.args[0]
        self.assertIn("Discos: 2 × ARS 30.000,00 = ARS 60.000,00", output)
        self.assertIn("Pastillas: 1 × ARS 20.000,00 = ARS 20.000,00", output)
        self.assertIn("Mano de obra: ARS 25.000,00", output)
        self.assertIn("TOTAL ESTIMADO: ARS 105.000,00", output)

    def test_incomplete_ai_draft_marks_total_pending_instead_of_calculating(self):
        import asyncio
        from unittest.mock import AsyncMock, patch
        from tallerweb.management.commands.runbot import show_ai_budget_draft

        draft = {
            "plate": "AA123BB", "make": "Toyota", "model": "Corolla",
            "customer_type": Vehicle.CustomerType.PRIVATE,
            "customer_name": "Cliente Demo", "customer_phone": "555",
            "description": "Cambio de frenos", "labor_amount": Decimal("25000"),
            "items": [{"description": "Discos", "quantity": 2, "unit_price": None, "total_price": None}],
            "labor_only": False, "uncertainties": [],
        }
        message = type("Message", (), {"reply_text": AsyncMock()})()

        with patch("tallerweb.management.commands.runbot.find_vehicle", new=AsyncMock(return_value=None)):
            asyncio.run(show_ai_budget_draft(message, draft))

        output = message.reply_text.await_args.args[0]
        self.assertIn("TOTAL ESTIMADO: pendiente", output)
        self.assertNotIn("TOTAL ESTIMADO: ARS", output)
        self.assertIn("aclarar descripción, cantidad y precio unitario de cada repuesto", output)

    def test_complete_natural_language_message_enters_budget_confirmation_flow(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import collect_ai_budget

        context = Mock()
        context.user_data = {"ai_budget": {}}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "Presupuesto completo"
        update.effective_message.reply_text = AsyncMock()
        candidate = {
            "plate": "AA123BB", "make": "Toyota", "model": "Hilux",
            "customer_type": "particular", "customer_name": "Ana", "customer_phone": "555",
            "description": "Cambio de filtro", "items": [{"description": "Filtro", "quantity": 1,
                "unit_price": Decimal("1500"), "total_price": None}], "labor_amount": Decimal("500"),
            "labor_only": False, "uncertainties": [],
        }
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.extract_budget", new=AsyncMock(return_value=candidate)),
              patch("tallerweb.management.commands.runbot.find_catalog_part", new=AsyncMock(return_value=None)),
              patch("tallerweb.management.commands.runbot.save_active_draft", new=AsyncMock()),
              patch("tallerweb.management.commands.runbot.start_budget", new=AsyncMock()) as start,
              patch("tallerweb.management.commands.runbot.show_ai_budget_draft", new=AsyncMock()) as show):
            asyncio.run(collect_ai_budget(update, context))

        start.assert_awaited_once_with(update, context)
        show.assert_not_awaited()

    def test_missing_fields_are_grouped_and_partial_facts_remain_in_draft(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import collect_ai_budget

        context = Mock()
        context.user_data = {"ai_budget": {}}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "Tengo patente y trabajo"
        update.effective_message.reply_text = AsyncMock()
        candidate = {"plate": "AA123BB", "description": "Revisar frenos", "items": [],
                     "labor_amount": None, "labor_only": None, "uncertainties": []}
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.extract_budget", new=AsyncMock(return_value=candidate)),
              patch("tallerweb.management.commands.runbot.find_catalog_part", new=AsyncMock(return_value=None)),
              patch("tallerweb.management.commands.runbot.save_active_draft", new=AsyncMock()),
              patch("tallerweb.management.commands.runbot.show_ai_budget_draft", new=AsyncMock()) as show):
            asyncio.run(collect_ai_budget(update, context))

        show.assert_awaited_once()
        self.assertEqual(context.user_data["ai_budget"]["plate"], "AA123BB")
        self.assertEqual(context.user_data["ai_budget"]["description"], "Revisar frenos")

    def test_catalog_price_requires_explicit_choice_before_budget_summary(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import collect_ai_budget

        vehicle = Vehicle.objects.create(plate="CAT-001", make="Toyota", model="Hilux",
                                         customer_type=Vehicle.CustomerType.PRIVATE,
                                         customer_name="Ana", customer_phone="555")
        part = PartCatalog.objects.create(description="Filtro", suggested_unit_price=Decimal("1800.00"))
        candidate = {"plate": vehicle.plate, "make": vehicle.make, "model": vehicle.model,
                     "customer_type": vehicle.customer_type, "customer_name": vehicle.customer_name,
                     "customer_phone": vehicle.customer_phone, "description": "Cambio de filtro",
                     "items": [{"description": "Filtro", "quantity": 1, "unit_price": None, "total_price": None}],
                     "labor_amount": Decimal("500"), "labor_only": False, "uncertainties": []}
        context = Mock()
        context.user_data = {"ai_budget": {}}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "Presupuesto de filtro"
        update.effective_message.reply_text = AsyncMock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.extract_budget", new=AsyncMock(return_value=candidate)),
              patch("tallerweb.management.commands.runbot.find_vehicle", new=AsyncMock(return_value=vehicle)),
              patch("tallerweb.management.commands.runbot.find_catalog_part", new=AsyncMock(return_value=part)),
              patch("tallerweb.management.commands.runbot.save_active_draft", new=AsyncMock())):
            asyncio.run(collect_ai_budget(update, context))

        self.assertIn("Referencia histórica", update.effective_message.reply_text.await_args.args[0])
        keyboard = update.effective_message.reply_text.await_args.kwargs["reply_markup"].inline_keyboard
        self.assertIn("budget:ai-catalog:accept:0", [button.callback_data for button in keyboard[0]])
        self.assertEqual(Budget.objects.count(), 0)
        self.assertEqual(part.suggested_unit_price, Decimal("1800.00"))

    def test_accepting_ai_catalog_reference_changes_only_draft_until_confirmation(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import budget_callback

        vehicle = Vehicle.objects.create(plate="CAT-002", make="Toyota", model="Hilux",
                                         customer_type=Vehicle.CustomerType.PRIVATE,
                                         customer_name="Ana", customer_phone="555")
        part = PartCatalog.objects.create(description="Filtro", suggested_unit_price=Decimal("1800.00"))
        context = Mock()
        context.user_data = {"budget": {"vehicle": vehicle, "description": "Cambio de filtro",
            "labor_amount": Decimal("500"), "confirmation_key": str(uuid4()), "items": [
                {"description": "Filtro", "quantity": 1, "unit_price": Decimal("1500"),
                 "subtotal": Decimal("1500")}], "ai_catalog_reviews": [
                {"item_index": 0, "suggested_price": part.suggested_unit_price,
                 "extracted_price": Decimal("1500")} ]}}
        update = Mock()
        update.effective_user.id = 123456
        update.callback_query.data = "budget:ai-catalog:accept:0"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.message = Mock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.show_budget_summary", new=AsyncMock()) as summary):
            asyncio.run(budget_callback(update, context))

        summary.assert_awaited_once()
        self.assertEqual(context.user_data["budget"]["items"][0]["unit_price"], Decimal("1800.00"))
        self.assertEqual(part.suggested_unit_price, Decimal("1800.00"))
        self.assertEqual(Budget.objects.count(), 0)

    def test_replacing_ai_catalog_reference_changes_only_draft_until_confirmation(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import BUDGET_ITEM_PRICE, budget_callback, collect_budget_field

        vehicle = Vehicle.objects.create(plate="CAT-003", make="Toyota", model="Hilux",
                                         customer_type=Vehicle.CustomerType.PRIVATE,
                                         customer_name="Ana", customer_phone="555")
        part = PartCatalog.objects.create(description="Filtro", suggested_unit_price=Decimal("1800.00"))
        context = Mock()
        context.user_data = {"budget": {"vehicle": vehicle, "description": "Cambio de filtro",
            "labor_amount": Decimal("500"), "confirmation_key": str(uuid4()), "items": [
                {"description": "Filtro", "quantity": 1, "unit_price": Decimal("1800"),
                 "subtotal": Decimal("1800")}], "ai_catalog_reviews": [
                {"item_index": 0, "suggested_price": part.suggested_unit_price,
                 "extracted_price": None}]}}
        update = Mock()
        update.effective_user.id = 123456
        update.callback_query.data = "budget:ai-catalog:replace:0"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.message = Mock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.show_budget_summary", new=AsyncMock()) as summary):
            asyncio.run(budget_callback(update, context))
            self.assertEqual(context.user_data["budget_step"], BUDGET_ITEM_PRICE)
            update.effective_message.text = "1750"
            update.effective_message.reply_text = AsyncMock()
            asyncio.run(collect_budget_field(update, context))

        summary.assert_awaited_once()
        self.assertEqual(context.user_data["budget"]["items"][0]["unit_price"], Decimal("1750.00"))
        self.assertEqual(part.suggested_unit_price, Decimal("1800.00"))
        self.assertEqual(Budget.objects.count(), 0)

    def test_openai_request_contains_only_current_message_not_previous_draft(self):
        import asyncio
        from unittest.mock import AsyncMock, patch
        from tallerweb.budget_ai import extract_budget

        previous = {
            "plate": "AA123BB", "customer_name": "Persona de prueba",
            "customer_phone": "555-0100", "items": [{"unit_price": Decimal("125.50")}],
            "history": ["mensaje anterior"],
        }
        response = type("Response", (), {"choices": [type("Choice", (), {
            "message": type("Message", (), {"content": '{"plate":null,"make":null,"model":null,'
                '"customer_type":null,"customer_name":null,"customer_phone":null,"description":null,'
                '"items":[],"labor_amount":null,"labor_only":false,"uncertainties":[]}'} )()
        })()]})()
        with (patch("tallerweb.budget_ai.settings.OPENAI_ENABLED", True),
              patch("tallerweb.budget_ai.settings.OPENAI_API_KEY", "test-key"),
              patch("tallerweb.budget_ai.AsyncOpenAI") as client_class):
            client_class.return_value.chat.completions.create = AsyncMock(return_value=response)
            asyncio.run(extract_budget("cambio el precio"))

        payload = client_class.return_value.chat.completions.create.await_args.kwargs
        self.assertEqual(payload["messages"][1]["content"], "cambio el precio")
        serialized_payload = str(payload)
        for private_value in ("AA123BB", "Persona de prueba", "555-0100", "125.50", "mensaje anterior"):
            self.assertNotIn(private_value, serialized_payload)

    def test_two_turn_correction_persists_decimal_and_merges_locally(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import collect_ai_budget

        draft = {"plate": "AA123BB", "description": "Frenos", "items": [
            {"description": "Pastillas", "quantity": 1, "unit_price": Decimal("125.50")}
        ], "uncertainties": []}
        context = Mock()
        context.user_data = {"ai_budget": draft}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "cambia la mano de obra a 60000"
        update.effective_message.reply_text = AsyncMock()
        candidate = {"labor_amount": Decimal("60000"), "plate": None, "items": [], "uncertainties": []}
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.extract_budget", new=AsyncMock(return_value=candidate)) as extract,
              patch("tallerweb.management.commands.runbot.find_catalog_part", new=AsyncMock(return_value=None)),
              patch("tallerweb.management.commands.runbot.save_active_draft", new=AsyncMock()) as save,
              patch("tallerweb.management.commands.runbot.show_ai_budget_draft", new=AsyncMock())):
            asyncio.run(collect_ai_budget(update, context))

        extract.assert_awaited_once_with(update.effective_message.text)
        save.assert_awaited_once()
        self.assertEqual(save.await_args.args[0]["items"][0]["unit_price"], Decimal("125.50"))
        self.assertEqual(context.user_data["ai_budget"]["labor_amount"], Decimal("60000"))

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

    def test_ai_correction_clears_stale_registered_vehicle_conflict(self):
        from tallerweb.budget_ai import merge_correction

        corrected = merge_correction(
            {"customer_name": "Dato anterior", "uncertainties": [
                "customer_name: el vehículo registrado tiene otro dato; confirma o corrige.",
                "falta confirmar si se incluyen repuestos",
            ]},
            {"customer_name": "Municipalidad", "uncertainties": []},
        )

        self.assertEqual(corrected["customer_name"], "Municipalidad")
        self.assertEqual(corrected["uncertainties"], ["falta confirmar si se incluyen repuestos"])

    def test_ai_correction_preserves_unrelated_registered_vehicle_conflict(self):
        from tallerweb.budget_ai import merge_correction

        conflict = "customer_name: el vehículo registrado tiene otro dato; confirma o corrige."
        corrected = merge_correction(
            {"customer_name": "Dato anterior", "description": "Frenos", "uncertainties": [conflict]},
            {"description": "Cambio de frenos", "uncertainties": []},
        )

        self.assertEqual(corrected["customer_name"], "Dato anterior")
        self.assertEqual(corrected["uncertainties"], [conflict])

    def test_ai_correction_resolves_old_total_only_price_uncertainty(self):
        from tallerweb.budget_ai import merge_correction

        corrected = merge_correction(
            {"labor_amount": Decimal("100"), "items": [{
                "description": "Discos", "quantity": 2, "unit_price": None, "total_price": Decimal("10000")
            }], "uncertainties": [
                "El repuesto requiere un precio unitario explícito; no se calcula desde un precio total."
            ]},
            {"items": [{"description": "Discos", "quantity": 2,
                         "unit_price": Decimal("5000"), "total_price": None}], "uncertainties": []},
        )

        self.assertEqual(corrected["items"][0]["unit_price"], Decimal("5000"))
        self.assertIsNone(corrected["items"][0]["total_price"])
        self.assertEqual(corrected["uncertainties"], [])

    def test_ai_correction_updates_one_item_and_preserves_the_rest(self):
        from tallerweb.budget_ai import merge_correction

        original = {"items": [
            {"description": "Discos", "quantity": 2, "unit_price": Decimal("1000")},
            {"description": "Pastillas", "quantity": 1, "unit_price": Decimal("500")},
        ], "uncertainties": []}
        candidate = {"items": [
            {"description": "Discos", "quantity": 2, "unit_price": Decimal("1200")},
        ], "uncertainties": []}

        corrected = merge_correction(original, candidate)

        self.assertEqual([item["description"] for item in corrected["items"]], ["Discos", "Pastillas"])
        self.assertEqual(corrected["items"][0]["unit_price"], Decimal("1200"))
        self.assertEqual(corrected["items"][1]["unit_price"], Decimal("500"))

    def test_ai_correction_drops_an_empty_placeholder_item_when_replacing_items(self):
        from tallerweb.budget_ai import merge_correction

        corrected = merge_correction(
            {"items": [
                {"description": "", "quantity": None, "unit_price": None, "total_price": None},
                {"description": "Discos", "quantity": 2, "unit_price": Decimal("30000"), "total_price": None},
            ], "uncertainties": ["Repuesto sin descripción o cantidad válida; requiere aclaración."]},
            {"items": [
                {"description": "Discos", "quantity": 2, "unit_price": Decimal("28000"), "total_price": None},
                {"description": "Pastillas", "quantity": 1, "unit_price": Decimal("20000"), "total_price": None},
            ], "uncertainties": ["Repuesto sin descripción o cantidad válida; requiere aclaración."]},
        )

        self.assertEqual([item["description"] for item in corrected["items"]], ["Discos", "Pastillas"])
        self.assertEqual(corrected["uncertainties"], [])

    def test_labor_named_as_an_item_is_not_counted_as_a_spare_part(self):
        from tallerweb.budget_ai import validate_candidate

        corrected = validate_candidate({
            "items": [
                {"description": "Filtro de aceite", "quantity": 1, "unit_price": "10000", "total_price": None},
                {"description": "Mano de obra", "quantity": 1, "unit_price": "15000", "total_price": None},
            ],
            "labor_amount": "15000",
            "uncertainties": [],
        })

        self.assertEqual(len(corrected["items"]), 1)
        self.assertEqual(corrected["items"][0]["description"], "Filtro de aceite")

    def test_ai_correction_retains_unresolved_item_uncertainty(self):
        from tallerweb.budget_ai import merge_correction

        original = {"items": [
            {"description": "Discos", "quantity": 2, "unit_price": None},
            {"description": "Pastillas", "quantity": 1, "unit_price": None},
        ], "uncertainties": [
            "El repuesto requiere un precio unitario explícito; no se calcula desde un precio total."
        ]}
        candidate = {"items": [
            {"description": "Discos", "quantity": 2, "unit_price": Decimal("1200")},
        ], "uncertainties": []}

        corrected = merge_correction(original, candidate)

        self.assertEqual(corrected["items"][0]["unit_price"], Decimal("1200"))
        self.assertIsNone(corrected["items"][1]["unit_price"])
        self.assertIn(
            "El repuesto requiere un precio unitario explícito; no se calcula desde un precio total.",
            corrected["uncertainties"],
        )

    def test_correction_does_not_change_labor_only_when_not_mentioned(self):
        from tallerweb.budget_ai import merge_correction

        corrected = merge_correction(
            {"labor_only": True, "items": [], "uncertainties": []},
            {"labor_only": None, "labor_amount": Decimal("60000"), "items": [], "uncertainties": []},
        )

        self.assertTrue(corrected["labor_only"])

    def test_ai_correction_updates_description_without_overwriting_other_fields(self):
        from tallerweb.budget_ai import merge_correction

        corrected = merge_correction(
            {"description": "Cambio de aceite", "labor_amount": Decimal("40000"),
             "items": [], "uncertainties": []},
            {"description": "Cambio de aceite y filtro", "labor_amount": None,
             "items": [], "uncertainties": []},
        )

        self.assertEqual(corrected["description"], "Cambio de aceite y filtro")
        self.assertEqual(corrected["labor_amount"], Decimal("40000"))

    def test_ai_correction_resolves_one_doubt_and_retains_unrelated_doubt(self):
        from tallerweb.budget_ai import LOCAL_VALIDATION_UNCERTAINTIES, merge_correction

        unrelated = "falta confirmar si se incluyen repuestos"
        price_uncertainty = next(value for value in LOCAL_VALIDATION_UNCERTAINTIES
                                 if value.startswith("El repuesto requiere"))
        corrected = merge_correction(
            {"items": [{"description": "Discos", "quantity": 2, "unit_price": None}],
             "uncertainties": [price_uncertainty, unrelated]},
            {"items": [{"description": "Discos", "quantity": 2, "unit_price": Decimal("5000")}],
             "uncertainties": []},
        )

        self.assertEqual(corrected["uncertainties"], [unrelated])

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

    def test_candidate_validation_marks_negative_labor_and_total_only_parts_as_unresolved(self):
        from tallerweb.budget_ai import validate_candidate

        candidate = validate_candidate({
            "labor_amount": "-100",
            "items": [{"description": "Discos", "quantity": 2,
                       "unit_price": None, "total_price": "10000"}],
            "uncertainties": [],
        })

        self.assertIsNone(candidate["labor_amount"])
        self.assertIsNone(candidate["items"][0]["unit_price"])
        self.assertIn("total_price", candidate["items"][0])
        self.assertTrue(candidate["uncertainties"])

    def test_candidate_validation_rejects_nonfinite_and_out_of_range_labor(self):
        from tallerweb.budget_ai import validate_candidate

        for amount in ("NaN", "Infinity", "10000000000", "1.001"):
            with self.subTest(amount=amount):
                candidate = validate_candidate({"labor_amount": amount, "items": [], "uncertainties": []})
                self.assertIsNone(candidate["labor_amount"])
                self.assertTrue(candidate["uncertainties"])

    def test_starting_guided_flow_does_not_offer_summary_for_contradictory_ai_customer(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch

        from tallerweb.management.commands.runbot import start_budget

        vehicle = Vehicle.objects.create(plate="AI-123-AA", make="Ford", model="Ranger",
                                          customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                          customer_name="Municipalidad", customer_phone="123")
        context = Mock()
        context.user_data = {"ai_budget": {
            "plate": vehicle.plate, "make": vehicle.make, "model": vehicle.model,
            "customer_type": vehicle.customer_type, "customer_name": "Otro cliente",
            "customer_phone": vehicle.customer_phone, "description": "Reparación",
            "items": [], "labor_amount": "100", "labor_only": True, "uncertainties": [],
        }}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.reply_text = AsyncMock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.find_vehicle", new=AsyncMock(return_value=vehicle)),
              patch("tallerweb.management.commands.runbot.show_ai_budget_draft", new=AsyncMock()) as show_draft,
              patch("tallerweb.management.commands.runbot.show_budget_summary", new=AsyncMock()) as show_summary):
            asyncio.run(start_budget(update, context))

        show_draft.assert_awaited_once()
        show_summary.assert_not_awaited()
        self.assertTrue(context.user_data["ai_budget"]["uncertainties"])

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


class GuidedBudgetContinuationTests(TestCase):
    def test_start_budget_transfers_partial_ai_draft_into_guided_budget(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import BUDGET_VEHICLE, start_budget

        context = Mock()
        context.user_data = {"ai_budget": {
            "plate": "AA123BB", "make": "Toyota",
            "description": "Cambio de frenos", "labor_amount": None,
            "items": [], "labor_only": True, "uncertainties": [],
        }}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.reply_text = AsyncMock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.find_vehicle", new=AsyncMock(return_value=None)),
              patch("tallerweb.management.commands.runbot.show_budget_summary", new=AsyncMock())):
            asyncio.run(start_budget(update, context))

        self.assertEqual(context.user_data["budget_step"], BUDGET_VEHICLE)
        self.assertEqual(context.user_data["budget"]["vehicle_data"]["plate"], "AA123BB")
        self.assertEqual(context.user_data["budget"]["vehicle_field"], "model")
        self.assertTrue(context.user_data["budget"]["ai_source_draft"]["labor_only"])
        update.effective_message.reply_text.assert_awaited_once()

    def test_labor_only_can_finish_without_repair_parts(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import BUDGET_ITEM_NAME, BUDGET_LABOR, budget_done

        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.reply_text = AsyncMock()
        context = Mock()
        context.user_data = {"budget": {"items": []}, "budget_step": BUDGET_ITEM_NAME}
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.show_budget_summary", new=AsyncMock())):
            asyncio.run(budget_done(update, context))

        self.assertEqual(context.user_data["budget_step"], BUDGET_LABOR)
        self.assertTrue(context.user_data["budget"]["labor_only"])
        update.effective_message.reply_text.assert_awaited()


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
        from tempfile import TemporaryDirectory
        from django.test import override_settings
        from tallerweb.management.commands.runbot import save_budget

        key = uuid4()
        data = {"confirmation_key": key, "vehicle": self.vehicle, "description": "Cambio de aceite",
                "labor_amount": Decimal("40000.00"), "total": Decimal("70000.00"),
                "items": [{"description": "Filtro", "quantity": 2, "unit_price": Decimal("15000.00"),
                           "subtotal": Decimal("30000.00")}]}
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            first = save_budget.__wrapped__(data)
            second = save_budget.__wrapped__(data)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Budget.objects.count(), 1)
        self.assertEqual(first.items.count(), 1)

    def test_confirming_new_ai_vehicle_creates_vehicle_budget_and_catalog_together(self):
        from tempfile import TemporaryDirectory
        from django.test import override_settings
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

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            budget = save_budget.__wrapped__(data)

        self.assertEqual(Vehicle.objects.filter(normalized_plate="CC456DD").count(), 1)
        self.assertEqual(budget.vehicle.customer_name, "Ana")
        self.assertEqual(PartCatalog.objects.get(description="Filtro").suggested_unit_price, Decimal("1500.00"))
        self.assertTrue(budget.pdf)

    def test_invalid_budget_is_rejected_before_vehicle_budget_catalog_or_pdf_write(self):
        from tallerweb.management.commands.runbot import save_budget

        for amount in ("-100.00", "NaN", "Infinity", "1.001", "10000000000"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                save_budget.__wrapped__({
                    "confirmation_key": uuid4(), "vehicle": None,
                    "vehicle_data": {"plate": "CC-456-DD", "make": "Toyota", "model": "Hilux",
                                     "customer_type": "particular", "customer_name": "Ana", "customer_phone": "555"},
                    "description": "Cambio de filtro", "labor_amount": Decimal(amount),
                    "total": Decimal("0.00"),
                    "items": [{"description": "Filtro", "quantity": 1, "unit_price": Decimal("1500.00"),
                               "subtotal": Decimal("1500.00")}],
                })

        self.assertEqual(Vehicle.objects.filter(normalized_plate="CC456DD").count(), 0)
        self.assertEqual(Budget.objects.count(), 0)
        self.assertEqual(PartCatalog.objects.count(), 0)

    def test_total_only_or_incomplete_part_is_rejected_at_budget_write_boundary(self):
        from tallerweb.management.commands.runbot import save_budget

        for item in (
            {"description": "Discos", "quantity": 2, "total_price": Decimal("10000.00"),
             "subtotal": Decimal("10000.00")},
            {"description": "Discos", "quantity": 0, "unit_price": Decimal("5000.00"),
             "subtotal": Decimal("0.00")},
        ):
            with self.subTest(item=item), self.assertRaises(ValueError):
                save_budget.__wrapped__({
                    "confirmation_key": uuid4(), "vehicle": self.vehicle, "description": "Reparación",
                    "labor_amount": Decimal("100.00"), "total": Decimal("10100.00"), "items": [item],
                })

        self.assertEqual(Budget.objects.count(), 0)
        self.assertEqual(PartCatalog.objects.count(), 0)

    def test_contradictory_ai_vehicle_is_rejected_at_budget_write_boundary(self):
        from tallerweb.management.commands.runbot import save_budget

        with self.assertRaises(ValueError):
            save_budget.__wrapped__({
                "confirmation_key": uuid4(), "vehicle": self.vehicle,
                "description": "Reparación", "labor_amount": Decimal("100.00"), "items": [],
                "ai_source_draft": {
                    "plate": self.vehicle.plate, "make": self.vehicle.make, "model": self.vehicle.model,
                    "customer_type": self.vehicle.customer_type, "customer_name": "Otro cliente",
                    "customer_phone": self.vehicle.customer_phone, "items": [], "uncertainties": [],
                },
            })

        self.assertEqual(Budget.objects.count(), 0)
        self.assertEqual(PartCatalog.objects.count(), 0)

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

    def test_invalid_closure_renders_field_errors_and_preserves_submitted_values(self):
        budget = Budget.objects.create(vehicle=self.vehicle, number="P-FORM", description="Trabajo",
                                       labor_amount=Decimal("0"), total=Decimal("100"),
                                       status=Budget.Status.APPROVED)
        self.client.force_login(self.user)

        response = self.client.post(reverse("complete_work", args=[budget.pk]), {
            "final_amount": "no-es-numero",
            "item_description": ["Filtro nuevo", "Bujía"],
            "item_quantity": ["2", "0"],
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El importe final cobrado debe ser un número válido y no negativo.")
        self.assertContains(response, "La cantidad debe ser un entero positivo.")
        self.assertContains(response, 'value="Filtro nuevo"')
        self.assertContains(response, 'value="Bujía"')
        self.assertContains(response, 'value="no-es-numero"')
        self.assertFalse(hasattr(budget, "completed_work"))
        self.assertEqual(CompletedWork.objects.count(), 0)

    def test_closure_form_supports_zero_or_many_material_rows(self):
        budget = Budget.objects.create(vehicle=self.vehicle, number="P-MANY", description="Trabajo",
                                       labor_amount=Decimal("0"), total=Decimal("100"),
                                       status=Budget.Status.APPROVED)
        self.client.force_login(self.user)

        response = self.client.get(reverse("vehicle_detail", args=[self.vehicle.pk]))

        self.assertContains(response, 'data-work-items')
        self.assertContains(response, 'data-add-work-item')
        self.assertContains(response, 'name="item_description"')
        self.assertContains(response, 'name="item_quantity"')

    def test_closure_requires_csrf_token(self):
        from django.test import Client

        budget = Budget.objects.create(vehicle=self.vehicle, number="P-CSRF", description="Trabajo",
                                       labor_amount=Decimal("0"), total=Decimal("100"),
                                       status=Budget.Status.APPROVED)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(reverse("complete_work", args=[budget.pk]), {"final_amount": "100"})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(CompletedWork.objects.count(), 0)

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

    def test_pdf_renders_user_text_with_markup_characters_without_error(self):
        from tallerweb.pdf import budget_pdf

        self.vehicle.customer_name = "Cliente <b>& 'Especial'"
        self.vehicle.make = "Ford & Hijos"
        self.vehicle.model = "<Ranger>"
        self.vehicle.save()
        budget = Budget.objects.create(
            vehicle=self.vehicle,
            number="P-ESCAPE",
            description="Reparacion <b> & < y >",
            labor_amount=Decimal("1200.00"),
            total=Decimal("1200.00"),
        )
        BudgetItem.objects.create(
            budget=budget,
            description="Repuesto <b> & < y >",
            quantity=1,
            unit_price=Decimal("1200.00"),
            subtotal=Decimal("1200.00"),
        )

        self.assertTrue(budget_pdf(budget).startswith(b"%PDF-"))

    def test_new_pdf_header_shows_real_workshop_identity(self):
        from reportlab import rl_config
        from tallerweb.pdf import budget_pdf

        budget = Budget.objects.create(vehicle=self.vehicle, number="P-IDENT", description="Revisión",
                                       labor_amount=Decimal("100.00"), total=Decimal("100.00"))
        previous = rl_config.pageCompression
        rl_config.pageCompression = 0
        try:
            content = budget_pdf(budget)
        finally:
            rl_config.pageCompression = previous

        self.assertIn(b"FT MOTORS", content)
        self.assertIn(b"Av. Dardo Rocha 1891 \\(Ruta 25\\), Pilar, Buenos Aires", content)
        self.assertIn(b"+54 9 11 5429 6017", content)
        self.assertNotIn(b"TALLER DEMO", content)
        self.assertNotIn(b"4000-0000", content)

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
        from tempfile import TemporaryDirectory
        from django.test import override_settings
        from tallerweb.management.commands.runbot import save_budget, save_budget_revision

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
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

    def test_failed_budget_save_leaves_file_only_in_temporary_media(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from django.test import override_settings
        from tallerweb.management.commands.runbot import save_budget

        original_save = Budget.save

        def fail_after_pdf_is_written(budget, *args, **kwargs):
            result = original_save(budget, *args, **kwargs)
            if budget.pdf.name:
                raise RuntimeError("simulated failure after PDF storage")
            return result

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            with patch.object(Budget, "save", fail_after_pdf_is_written):
                with self.assertRaisesRegex(RuntimeError, "simulated failure"):
                    save_budget.__wrapped__({
                        "confirmation_key": uuid4(), "vehicle": self.vehicle,
                        "description": "Trabajo", "labor_amount": Decimal("1.00"),
                        "total": Decimal("1.00"), "items": [],
                    })

            self.assertEqual(Budget.objects.count(), 0)
            stored_files = [path for path in Path(media_dir).rglob("*") if path.is_file()]
            self.assertEqual(len(stored_files), 1)
            self.assertEqual(stored_files[0].suffix, ".pdf")


class RevisionCallbackTests(TransactionTestCase):
    def test_natural_language_message_selects_numbered_pending_budget_for_correction(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import collect_vehicle_field

        vehicle = Vehicle.objects.create(plate="NZ-111-NZ", make="Ford", model="Ranger",
                                         customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                         customer_name="Municipalidad", customer_phone="123")
        budget = Budget.objects.create(vehicle=vehicle, number="P-009998", description="Trabajo vigente",
                                       labor_amount=Decimal("120.00"), total=Decimal("120.00"))
        context = Mock()
        context.user_data = {}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = "Corrige P-009998: cambia la descripción a revisar frenos"
        update.effective_message.reply_text = AsyncMock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.settings.OPENAI_ENABLED", True),
              patch("tallerweb.management.commands.runbot.settings.OPENAI_API_KEY", "test"),
              patch("tallerweb.management.commands.runbot.offer_draft_actions", new=AsyncMock(return_value=False)),
              patch("tallerweb.management.commands.runbot.extract_budget", new=AsyncMock(return_value={
                  "description": "Revisar frenos", "items": [], "uncertainties": []
              })),
              patch("tallerweb.management.commands.runbot.save_active_draft", new=AsyncMock()),
              patch("tallerweb.management.commands.runbot.find_ai_catalog_reviews", new=AsyncMock(return_value=[])),
              patch("tallerweb.management.commands.runbot.start_budget", new=AsyncMock()) as start,
              patch("tallerweb.management.commands.runbot.show_ai_budget_draft", new=AsyncMock())):
            asyncio.run(collect_vehicle_field(update, context))

        start.assert_awaited_once_with(update, context)
        self.assertEqual(context.user_data["ai_budget"]["revision_of"], budget.pk)
        self.assertEqual(context.user_data["ai_budget"]["description"], "Revisar frenos")

    def test_natural_language_correction_rejects_non_pending_or_historical_number(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import collect_vehicle_field

        vehicle = Vehicle.objects.create(plate="NZ-112-NZ", make="Ford", model="Ranger",
                                         customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                         customer_name="Municipalidad", customer_phone="123")
        budget = Budget.objects.create(vehicle=vehicle, number="P-009997", description="Trabajo",
                                       labor_amount=Decimal("120.00"), total=Decimal("120.00"),
                                       status=Budget.Status.APPROVED)
        context = Mock()
        context.user_data = {}
        update = Mock()
        update.effective_user.id = 123456
        update.effective_message.text = f"Corrige {budget.number}: cambia descripción"
        update.effective_message.reply_text = AsyncMock()
        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.settings.OPENAI_ENABLED", True),
              patch("tallerweb.management.commands.runbot.settings.OPENAI_API_KEY", "test"),
              patch("tallerweb.management.commands.runbot.offer_draft_actions", new=AsyncMock(return_value=False)),
              patch("tallerweb.management.commands.runbot.collect_ai_budget", new=AsyncMock()) as collect):
            asyncio.run(collect_vehicle_field(update, context))

        collect.assert_not_awaited()
        update.effective_message.reply_text.assert_awaited_once()
        self.assertIn("Solo se pueden corregir", update.effective_message.reply_text.await_args.args[0])

    def test_revision_callback_resolves_selected_budget_by_primary_key(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from tallerweb.management.commands.runbot import budget_callback

        vehicle = Vehicle.objects.create(plate="ZZ-111-ZZ", make="Ford", model="Ranger",
                                         customer_type=Vehicle.CustomerType.MUNICIPALITY,
                                         customer_name="Municipalidad", customer_phone="123")
        budget = Budget.objects.create(vehicle=vehicle, number="P-009999", description="Trabajo vigente",
                                       labor_amount=Decimal("120.00"), total=Decimal("120.00"))
        context = Mock()
        context.user_data = {}
        update = Mock()
        update.effective_user.id = 123456
        update.callback_query.data = f"budget:revise:{budget.pk}"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.message = Mock()

        with (patch("tallerweb.management.commands.runbot.settings.TELEGRAM_ALLOWED_USER_ID", "123456"),
              patch("tallerweb.management.commands.runbot.show_budget_summary", new=AsyncMock()) as show_summary):
            asyncio.run(budget_callback(update, context))

        self.assertEqual(context.user_data["budget"]["revision_of"], budget.pk)
        self.assertEqual(context.user_data["budget"]["description"], "Trabajo vigente")
        show_summary.assert_awaited_once_with(update.callback_query.message, context.user_data["budget"])


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

    def test_summary_rejects_years_outside_supported_date_range(self):
        for year in ("0", "9999", "10000", "no-es-numero", ""):
            with self.subTest(year=year):
                response = self.client.get(reverse("monthly_summary"), {"month": "12", "year": year})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Selecciona un mes y año válidos.")

    def test_summary_accepts_supported_year_boundaries(self):
        for year in ("1", "9998"):
            with self.subTest(year=year):
                response = self.client.get(reverse("monthly_summary"), {"month": "12", "year": year})
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "Selecciona un mes y año válidos.")

    def test_summary_rejects_blank_and_non_numeric_months(self):
        for month in ("", "abc", "0", "13"):
            with self.subTest(month=month):
                response = self.client.get(reverse("monthly_summary"), {"month": month, "year": "2025"})
                self.assertEqual(response.status_code, 200)
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
