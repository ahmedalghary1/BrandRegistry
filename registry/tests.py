from datetime import date
from decimal import Decimal

from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from .forms import IndustrialDesignForm, SiteSettingsForm, TrademarkForm
from .models import IndustrialDesign, Trademark
from .views import (
    DashboardView,
    DesignDetailView,
    DesignListView,
    ReportsView,
    SettingsView,
    TrademarkDetailView,
    TrademarkListView,
)


class TrademarkLogicTests(TestCase):
    def test_protection_and_publication_deadlines_are_computed(self):
        trademark = Trademark.objects.create(
            name="علامة اختبار",
            number="TM-100",
            filing_date=date(2024, 1, 1),
            publication_date=date(2024, 2, 1),
            filing_fee=Decimal("100.00"),
            examination_fee=Decimal("25.00"),
        )

        self.assertEqual(trademark.publication_deadline, date(2024, 4, 1))
        self.assertEqual(trademark.protection_expiry, date(2034, 1, 1))
        self.assertEqual(trademark.total_fees, Decimal("125.00"))

    def test_under_review_form_defaults_missing_fees_to_zero(self):
        form = TrademarkForm(
            data={
                "name": "علامة قيد الفحص",
                "number": "TM-200",
                "filing_date": "2026-04-19",
                "status": Trademark.STATUS_UNDER_REVIEW,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.filing_fee, Decimal("0.00"))
        self.assertEqual(instance.examination_fee, Decimal("0.00"))
        self.assertEqual(instance.additional_fee, Decimal("0.00"))


class RegistryViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.trademark = Trademark.objects.create(
            name="علامة واجهة",
            number="TM-300",
            filing_date=date(2024, 5, 10),
            status=Trademark.STATUS_REGISTERED,
            decision_date=date(2024, 6, 1),
            announcement_date=date(2024, 6, 2),
            publication_date=date(2024, 6, 5),
            publication_number="44",
            registration_date=date(2024, 8, 1),
            registration_number="REG-44",
            filing_fee=Decimal("100.00"),
            examination_fee=Decimal("50.00"),
            publication_fee=Decimal("75.00"),
            registration_fee=Decimal("150.00"),
        )
        self.design = IndustrialDesign.objects.create(
            name="نموذج واجهة",
            number="DM-300",
            filing_date=date(2024, 5, 10),
            description="وصف للتجربة",
        )

    def test_main_pages_return_success(self):
        view_specs = [
            (DashboardView.as_view(), reverse("registry:dashboard"), {}),
            (TrademarkListView.as_view(), reverse("registry:trademarks:list"), {}),
            (
                TrademarkDetailView.as_view(),
                reverse("registry:trademarks:detail", args=[self.trademark.pk]),
                {"pk": self.trademark.pk},
            ),
            (DesignListView.as_view(), reverse("registry:designs:list"), {}),
            (
                DesignDetailView.as_view(),
                reverse("registry:designs:detail", args=[self.design.pk]),
                {"pk": self.design.pk},
            ),
            (ReportsView.as_view(), reverse("registry:reports"), {}),
            (SettingsView.as_view(), reverse("registry:settings"), {}),
        ]

        for view, url, kwargs in view_specs:
            with self.subTest(url=url):
                request = self.factory.get(url)
                response = view(request, **kwargs)
                self.assertEqual(response.status_code, 200)

    def test_report_exports_work(self):
        pdf_response = self.client.get(reverse("registry:reports"), {"record_type": "trademark", "export": "pdf"})
        excel_response = self.client.get(reverse("registry:reports"), {"record_type": "design", "export": "excel"})

        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertEqual(excel_response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            excel_response["Content-Type"],
        )

    def test_forms_expose_dynamic_widget_metadata(self):
        forms_to_check = [TrademarkForm(), IndustrialDesignForm()]

        for form in forms_to_check:
            with self.subTest(form=form.__class__.__name__):
                self.assertEqual(form.fields["status"].widget.attrs["data-role"], "status-field")
                self.assertEqual(form.fields["filing_date"].widget.attrs["data-role"], "filing-date")
                self.assertEqual(form.fields["publication_date"].widget.attrs["data-role"], "publication-date")
                self.assertEqual(form.fields["image"].widget.attrs["data-role"], "image-input")
                self.assertEqual(
                    form.fields["decision_date"].widget.attrs["data-required-for"],
                    "accepted,registered,rejected",
                )
                self.assertEqual(form.fields["filing_fee"].widget.attrs["data-fee-field"], "true")
                self.assertEqual(form.fields["additional_fee"].widget.attrs["data-fee-field"], "true")

    def test_settings_form_required_fields_are_clear(self):
        form = SiteSettingsForm()
        self.assertTrue(form.fields["site_title"].required)
        self.assertTrue(form.fields["site_subtitle"].required)
        self.assertFalse(form.fields["site_logo"].required)

    def test_fee_fields_are_saved_with_trademark_record(self):
        response = self.client.post(
            reverse("registry:trademarks:add"),
            data={
                "name": "علامة برسوم",
                "number": "TM-400",
                "filing_date": "2026-04-19",
                "status": Trademark.STATUS_ACCEPTED,
                "decision_date": "2026-04-20",
                "announcement_date": "2026-04-21",
                "publication_date": "2026-04-22",
                "publication_number": "77",
                "filing_fee": "100.50",
                "examination_fee": "25.00",
                "publication_fee": "40.00",
                "registration_fee": "0",
                "appeal_fee": "0",
                "additional_fee": "10.25",
            },
        )

        self.assertEqual(response.status_code, 302)

        record = Trademark.objects.get(number="TM-400")
        self.assertEqual(record.filing_fee, Decimal("100.50"))
        self.assertEqual(record.examination_fee, Decimal("25.00"))
        self.assertEqual(record.publication_fee, Decimal("40.00"))
        self.assertEqual(record.additional_fee, Decimal("10.25"))
        self.assertEqual(record.total_fees, Decimal("175.75"))
