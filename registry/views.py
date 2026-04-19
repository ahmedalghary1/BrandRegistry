from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from itertools import chain

import openpyxl
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import (
    IndustrialDesignForm,
    RecordFilterForm,
    SiteSettingsForm,
    TrademarkForm,
)
from .models import IndustrialDesign, SiteSettings, Trademark, add_years
from .utils import register_arabic_font, shape_arabic, with_total_fees


def apply_record_filters(queryset, cleaned_data):
    queryset = with_total_fees(queryset)

    search_name = cleaned_data.get("search_name")
    search_number = cleaned_data.get("search_number")
    status = cleaned_data.get("status")
    filing_date_from = cleaned_data.get("filing_date_from")
    filing_date_to = cleaned_data.get("filing_date_to")
    expiring_only = cleaned_data.get("expiring_only")
    fees_min = cleaned_data.get("fees_min")
    fees_max = cleaned_data.get("fees_max")

    if search_name:
        queryset = queryset.filter(name__icontains=search_name)
    if search_number:
        queryset = queryset.filter(number__icontains=search_number)
    if status:
        queryset = queryset.filter(status=status)
    if filing_date_from:
        queryset = queryset.filter(filing_date__gte=filing_date_from)
    if filing_date_to:
        queryset = queryset.filter(filing_date__lte=filing_date_to)
    if expiring_only:
        today = timezone.localdate()
        cutoff = today + timedelta(days=30)
        queryset = queryset.filter(
            filing_date__range=(add_years(today, -10), add_years(cutoff, -10))
        )
    if fees_min is not None:
        queryset = queryset.filter(total_fees_db__gte=fees_min)
    if fees_max is not None:
        queryset = queryset.filter(total_fees_db__lte=fees_max)

    return queryset


def build_status_counts(model):
    counts = {key: 0 for key, _ in model.STATUS_CHOICES}
    counts.update(model.objects.values("status").annotate(total=Count("id")).values_list("status", "total"))
    return counts


class DashboardView(generic.TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        trademark_counts = build_status_counts(Trademark)
        design_counts = build_status_counts(IndustrialDesign)
        trademark_records = list(Trademark.objects.all()[:6])
        design_records = list(IndustrialDesign.objects.all()[:6])

        expiring_trademarks = [item for item in Trademark.objects.all() if item.is_approaching_protection_expiry]
        expiring_designs = [item for item in IndustrialDesign.objects.all() if item.is_approaching_protection_expiry]

        recent_records = sorted(
            chain(
                [{"type": "علامة تجارية", "object": item} for item in trademark_records],
                [{"type": "نموذج صناعي", "object": item} for item in design_records],
            ),
            key=lambda item: item["object"].created_at,
            reverse=True,
        )[:8]

        context.update(
            {
                "trademark_counts": trademark_counts,
                "design_counts": design_counts,
                "total_trademarks": Trademark.objects.count(),
                "total_designs": IndustrialDesign.objects.count(),
                "expiring_trademarks": expiring_trademarks,
                "expiring_designs": expiring_designs,
                "current_alerts": len(expiring_trademarks) + len(expiring_designs),
                "recent_records": recent_records,
                "total_fees_trademarks": sum(
                    (item.total_fees for item in Trademark.objects.all()),
                    Decimal("0.00"),
                ),
                "total_fees_designs": sum(
                    (item.total_fees for item in IndustrialDesign.objects.all()),
                    Decimal("0.00"),
                ),
            }
        )
        return context


class BaseRecordListView(generic.ListView):
    paginate_by = 20
    filter_form_class = RecordFilterForm

    def get_filter_form(self):
        return self.filter_form_class(self.request.GET or None)

    def get_queryset(self):
        queryset = self.model.objects.all()
        self.filter_form = self.get_filter_form()
        if self.filter_form.is_valid():
            queryset = apply_record_filters(queryset, self.filter_form.cleaned_data)
        else:
            queryset = with_total_fees(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["status_counts"] = build_status_counts(self.model)
        context["active_filters"] = {
            key: value
            for key, value in self.request.GET.items()
            if value not in ("", None)
        }
        return context


class TrademarkListView(BaseRecordListView):
    model = Trademark
    template_name = "trademarks.html"
    context_object_name = "trademarks"


class TrademarkDetailView(generic.DetailView):
    model = Trademark
    template_name = "trademark_detail.html"
    context_object_name = "trademark"


class TrademarkCreateView(generic.CreateView):
    model = Trademark
    form_class = TrademarkForm
    template_name = "trademark_form.html"
    success_url = reverse_lazy("registry:trademarks:list")

    def form_valid(self, form):
        messages.success(self.request, "تم حفظ العلامة التجارية بنجاح.")
        return super().form_valid(form)


class TrademarkUpdateView(generic.UpdateView):
    model = Trademark
    form_class = TrademarkForm
    template_name = "trademark_form.html"
    success_url = reverse_lazy("registry:trademarks:list")

    def form_valid(self, form):
        messages.success(self.request, "تم تحديث بيانات العلامة التجارية بنجاح.")
        return super().form_valid(form)


class TrademarkDeleteView(generic.DeleteView):
    model = Trademark
    template_name = "trademark_confirm_delete.html"
    success_url = reverse_lazy("registry:trademarks:list")

    def form_valid(self, form):
        messages.success(self.request, "تم حذف العلامة التجارية بنجاح.")
        return super().form_valid(form)


class DesignListView(BaseRecordListView):
    model = IndustrialDesign
    template_name = "designs.html"
    context_object_name = "designs"


class DesignDetailView(generic.DetailView):
    model = IndustrialDesign
    template_name = "design_detail.html"
    context_object_name = "design"


class DesignCreateView(generic.CreateView):
    model = IndustrialDesign
    form_class = IndustrialDesignForm
    template_name = "design_form.html"
    success_url = reverse_lazy("registry:designs:list")

    def form_valid(self, form):
        messages.success(self.request, "تم حفظ النموذج الصناعي بنجاح.")
        return super().form_valid(form)


class DesignUpdateView(generic.UpdateView):
    model = IndustrialDesign
    form_class = IndustrialDesignForm
    template_name = "design_form.html"
    success_url = reverse_lazy("registry:designs:list")

    def form_valid(self, form):
        messages.success(self.request, "تم تحديث بيانات النموذج الصناعي بنجاح.")
        return super().form_valid(form)


class DesignDeleteView(generic.DeleteView):
    model = IndustrialDesign
    template_name = "design_confirm_delete.html"
    success_url = reverse_lazy("registry:designs:list")

    def form_valid(self, form):
        messages.success(self.request, "تم حذف النموذج الصناعي بنجاح.")
        return super().form_valid(form)


class ReportsView(generic.TemplateView):
    template_name = "reports.html"

    report_config = {
        "trademark": {
            "model": Trademark,
            "title": "العلامات التجارية",
        },
        "design": {
            "model": IndustrialDesign,
            "title": "النماذج الصناعية",
        },
    }

    def dispatch(self, request, *args, **kwargs):
        self.record_type = request.GET.get("record_type", "trademark")
        self.config = self.report_config.get(self.record_type, self.report_config["trademark"])
        self.filter_form = RecordFilterForm(request.GET or None)
        self.queryset = self.config["model"].objects.all()
        if self.filter_form.is_valid():
            self.queryset = apply_record_filters(self.queryset, self.filter_form.cleaned_data)
        else:
            self.queryset = with_total_fees(self.queryset)

        export = request.GET.get("export")
        if export in {"pdf", "excel"}:
            return self.export_report(export)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "record_type": self.record_type,
                "record_title": self.config["title"],
                "filter_form": self.filter_form,
                "records": self.queryset[:100],
                "records_count": self.queryset.count(),
                "trademark_counts": build_status_counts(Trademark),
                "design_counts": build_status_counts(IndustrialDesign),
                "expiring_trademarks": [item for item in Trademark.objects.all() if item.is_approaching_protection_expiry],
                "expiring_designs": [item for item in IndustrialDesign.objects.all() if item.is_approaching_protection_expiry],
            }
        )
        return context

    def export_report(self, export_format):
        title = f"تقرير {self.config['title']}"
        rows = []
        for record in self.queryset:
            rows.append(
                [
                    record.name,
                    record.number,
                    record.get_status_display(),
                    record.filing_date.strftime("%Y-%m-%d") if record.filing_date else "",
                    record.decision_date.strftime("%Y-%m-%d") if record.decision_date else "",
                    record.publication_deadline.strftime("%Y-%m-%d") if record.publication_deadline else "",
                    record.protection_expiry.strftime("%Y-%m-%d") if record.protection_expiry else "",
                    f"{record.total_fees:.2f}",
                ]
            )

        headers = [
            "الاسم",
            "الرقم",
            "القرار",
            "تاريخ الإيداع",
            "تاريخ القرار",
            "آخر يوم في النشر",
            "انتهاء الحماية",
            "إجمالي الرسوم",
        ]

        if export_format == "excel":
            return self.export_excel(title, headers, rows)
        return self.export_pdf(title, headers, rows)

    def export_excel(self, title, headers, rows):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = title[:31]
        sheet.sheet_view.rightToLeft = True

        header_fill = PatternFill("solid", fgColor="0F4C5C")
        header_font = Font(color="FFFFFF", bold=True)
        center = Alignment(horizontal="center", vertical="center")

        sheet.append(headers)
        for index, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=index)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center

        for row in rows:
            sheet.append(row)

        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 4, 28)
            for cell in column_cells:
                cell.alignment = center

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{self.record_type}-report.xlsx"'
        return response

    def export_pdf(self, title, headers, rows):
        font_name, bold_name = register_arabic_font()
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=18,
            leftMargin=18,
            topMargin=24,
            bottomMargin=24,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ArabicTitle",
            parent=styles["Title"],
            fontName=bold_name,
            fontSize=18,
            alignment=1,
        )
        cell_style = ParagraphStyle(
            "ArabicCell",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=12,
            alignment=1,
        )
        header_style = ParagraphStyle(
            "ArabicHeader",
            parent=cell_style,
            fontName=bold_name,
            textColor=colors.white,
        )

        data = [[Paragraph(shape_arabic(header), header_style) for header in headers]]
        for row in rows:
            data.append([Paragraph(shape_arabic(cell), cell_style) for cell in row])

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4C5C")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F8FA")]),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ]
            )
        )

        elements = [
            Paragraph(shape_arabic(title), title_style),
            Spacer(1, 12),
            table,
        ]
        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{self.record_type}-report.pdf"'
        return response


class SettingsView(generic.UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = "settings.html"
    success_url = reverse_lazy("registry:settings")

    def get_object(self, queryset=None):
        return SiteSettings.get_solo()

    def form_valid(self, form):
        messages.success(self.request, "تم تحديث إعدادات النظام بنجاح.")
        return super().form_valid(form)


class NotFoundView(generic.TemplateView):
    template_name = "404.html"
