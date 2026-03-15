from datetime import timedelta
import csv
from io import BytesIO

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.db.models import Q

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl

from .forms import IndustrialDesignForm, SiteSettingsForm, TrademarkForm
from .models import IndustrialDesign, SiteSettings, Trademark


class DashboardView(generic.TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_trademarks'] = Trademark.objects.count()
        context['accepted_trademarks'] = Trademark.objects.filter(status=Trademark.STATUS_ACCEPTED).count()
        context['under_review_trademarks'] = Trademark.objects.filter(status=Trademark.STATUS_UNDER_REVIEW).count()
        context['total_designs'] = IndustrialDesign.objects.count()

        now = timezone.localdate()
        cutoff = now + timedelta(days=30)
        expiring = []
        for tm in Trademark.objects.filter(filing_date__isnull=False):
            expiry = tm.protection_expiry
            if expiry and now <= expiry <= cutoff:
                expiring.append(tm)

        context['expiring_trademarks'] = expiring
        return context


class TrademarkListView(generic.ListView):
    model = Trademark
    template_name = 'trademarks.html'
    context_object_name = 'trademarks'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().order_by('-created_at')
        status = self.request.GET.get('status')
        search = self.request.GET.get('q')
        if status in (Trademark.STATUS_UNDER_REVIEW, Trademark.STATUS_ACCEPTED, Trademark.STATUS_REJECTED):
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(number__icontains=search))
        return qs


class TrademarkCreateView(generic.CreateView):
    model = Trademark
    form_class = TrademarkForm
    template_name = 'trademark_form.html'
    success_url = reverse_lazy('registry:trademarks:list')

    def form_valid(self, form):
        messages.success(self.request, 'تم إضافة العلامة التجارية بنجاح.')
        return super().form_valid(form)


class TrademarkUpdateView(generic.UpdateView):
    model = Trademark
    form_class = TrademarkForm
    template_name = 'trademark_form.html'
    success_url = reverse_lazy('registry:trademarks:list')

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث العلامة التجارية بنجاح.')
        return super().form_valid(form)


class TrademarkDeleteView(generic.DeleteView):
    model = Trademark
    template_name = 'trademark_confirm_delete.html'
    success_url = reverse_lazy('registry:trademarks:list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف العلامة التجارية بنجاح.')
        return super().delete(request, *args, **kwargs)


class DesignListView(generic.ListView):
    model = IndustrialDesign
    template_name = 'designs.html'
    context_object_name = 'designs'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().order_by('-created_at')
        status = self.request.GET.get('status')
        search = self.request.GET.get('q')
        if status in (IndustrialDesign.STATUS_UNDER_REVIEW, IndustrialDesign.STATUS_ACCEPTED, IndustrialDesign.STATUS_REJECTED):
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(number__icontains=search))
        return qs


class DesignCreateView(generic.CreateView):
    model = IndustrialDesign
    form_class = IndustrialDesignForm
    template_name = 'design_form.html'
    success_url = reverse_lazy('registry:designs:list')

    def form_valid(self, form):
        messages.success(self.request, 'تم إضافة النموذج الصناعي بنجاح.')
        return super().form_valid(form)


class DesignUpdateView(generic.UpdateView):
    model = IndustrialDesign
    form_class = IndustrialDesignForm
    template_name = 'design_form.html'
    success_url = reverse_lazy('registry:designs:list')

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث النموذج الصناعي بنجاح.')
        return super().form_valid(form)


class DesignDeleteView(generic.DeleteView):
    model = IndustrialDesign
    template_name = 'design_confirm_delete.html'
    success_url = reverse_lazy('registry:designs:list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف النموذج الصناعي بنجاح.')
        return super().delete(request, *args, **kwargs)


class ReportsView(generic.TemplateView):
    template_name = 'reports.html'

    def get(self, request, *args, **kwargs):
        export = request.GET.get('export')
        status = request.GET.get('status')
        if export in ('trademarks_csv', 'designs_csv', 'trademarks_pdf', 'designs_pdf', 'trademarks_excel', 'designs_excel'):
            return self._export(export, status)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_trademarks'] = Trademark.objects.count()
        context['accepted_trademarks'] = Trademark.objects.filter(status=Trademark.STATUS_ACCEPTED).count()
        context['under_review_trademarks'] = Trademark.objects.filter(status=Trademark.STATUS_UNDER_REVIEW).count()
        context['rejected_trademarks'] = Trademark.objects.filter(status=Trademark.STATUS_REJECTED).count()
        context['total_designs'] = IndustrialDesign.objects.count()

        now = timezone.localdate()
        cutoff = now + timedelta(days=30)
        expiring = []
        for tm in Trademark.objects.filter(filing_date__isnull=False):
            expiry = tm.protection_expiry
            if expiry and now <= expiry <= cutoff:
                expiring.append(tm)

        context['expiring_trademarks'] = expiring
        return context

    def _export(self, export_type, status):
        if 'trademarks' in export_type:
            items = Trademark.objects.order_by('-created_at')
            if status in (Trademark.STATUS_UNDER_REVIEW, Trademark.STATUS_ACCEPTED, Trademark.STATUS_REJECTED):
                items = items.filter(status=status)
            filename_base = f'trademarks_{status or "all"}'
            headers = ['الاسم', 'الرقم', 'تاريخ الإيداع', 'تاريخ انتهاء الحماية', 'الحالة', 'الفئات']
            rows = [
                [
                    t.name,
                    t.number,
                    t.filing_date.strftime('%d/%m/%Y') if t.filing_date else '',
                    t.protection_expiry.strftime('%d/%m/%Y') if t.protection_expiry else '',
                    t.get_status_display(),
                    t.categories or '',
                ]
                for t in items
            ]
        else:
            items = IndustrialDesign.objects.order_by('-created_at')
            if status in (IndustrialDesign.STATUS_UNDER_REVIEW, IndustrialDesign.STATUS_ACCEPTED, IndustrialDesign.STATUS_REJECTED):
                items = items.filter(status=status)
            filename_base = f'designs_{status or "all"}'
            headers = ['الاسم', 'الرقم', 'تاريخ الإيداع', 'تاريخ انتهاء الحماية', 'الحالة']
            rows = [
                [
                    d.name,
                    d.number,
                    d.filing_date.strftime('%d/%m/%Y') if d.filing_date else '',
                    d.protection_expiry.strftime('%d/%m/%Y') if d.protection_expiry else '',
                    d.get_status_display(),
                ]
                for d in items
            ]

        if export_type.endswith('_csv'):
            return self._export_csv(filename_base, headers, rows)
        elif export_type.endswith('_pdf'):
            return self._export_pdf(filename_base, headers, rows)
        elif export_type.endswith('_excel'):
            return self._export_excel(filename_base, headers, rows)

    def _export_csv(self, filename_base, headers, rows):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response

    def _export_pdf(self, filename_base, headers, rows):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        title = Paragraph(f"تقرير {filename_base.replace('_', ' ')}", styles['Title'])
        elements.append(title)

        data = [headers] + rows
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.pdf"'
        return response

    def _export_excel(self, filename_base, headers, rows):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = filename_base

        for col_num, header in enumerate(headers, 1):
            ws.cell(row=1, column=col_num, value=header)

        for row_num, row_data in enumerate(rows, 2):
            for col_num, cell_value in enumerate(row_data, 1):
                ws.cell(row=row_num, column=col_num, value=cell_value)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.xlsx"'
        return response


class SettingsView(generic.UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'settings.html'
    success_url = reverse_lazy('registry:settings')

    def get_object(self, queryset=None):
        return SiteSettings.get_solo()


class NotFoundView(generic.TemplateView):
    template_name = '404.html'
