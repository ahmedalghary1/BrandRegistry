from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import IndustrialDesign, SiteSettings, Trademark


@admin.register(Trademark)
class TrademarkAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "number",
        "status",
        "filing_date",
        "publication_deadline",
        "protection_expiry",
        "total_fees",
    )
    list_filter = ("status", "filing_date", "decision_date")
    search_fields = ("name", "number", "categories", "registration_number")
    readonly_fields = ("created_at", "updated_at", "publication_deadline", "protection_expiry", "total_fees")
    fieldsets = (
        ("البيانات الأساسية", {"fields": ("name", "image", "number", "categories", "status", "filing_date")}),
        (
            "مرحلة القرار والنشر",
            {
                "fields": (
                    "decision_date",
                    "announcement_date",
                    "publication_date",
                    "publication_number",
                    "publication_deadline",
                )
            },
        ),
        (
            "مرحلة التسجيل والرفض",
            {
                "fields": (
                    "registration_date",
                    "registration_number",
                    "protection_expiry",
                    "rejection_reasons",
                    "appeal_date",
                    "appeal_hearing_date",
                )
            },
        ),
        (
            "الرسوم",
            {
                "fields": (
                    "filing_fee",
                    "examination_fee",
                    "publication_fee",
                    "registration_fee",
                    "appeal_fee",
                    "additional_fee",
                    "total_fees",
                )
            },
        ),
        ("السجل", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(IndustrialDesign)
class IndustrialDesignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "number",
        "status",
        "filing_date",
        "publication_deadline",
        "protection_expiry",
        "total_fees",
    )
    list_filter = ("status", "filing_date", "decision_date")
    search_fields = ("name", "number", "description", "registration_number")
    readonly_fields = ("created_at", "updated_at", "publication_deadline", "protection_expiry", "total_fees")
    fieldsets = (
        ("البيانات الأساسية", {"fields": ("name", "description", "image", "number", "status", "filing_date")}),
        (
            "مرحلة القرار والنشر",
            {
                "fields": (
                    "decision_date",
                    "announcement_date",
                    "publication_date",
                    "publication_number",
                    "publication_deadline",
                )
            },
        ),
        (
            "مرحلة التسجيل والرفض",
            {
                "fields": (
                    "registration_date",
                    "registration_number",
                    "protection_expiry",
                    "rejection_reasons",
                    "appeal_date",
                    "appeal_hearing_date",
                )
            },
        ),
        (
            "الرسوم",
            {
                "fields": (
                    "filing_fee",
                    "examination_fee",
                    "publication_fee",
                    "registration_fee",
                    "appeal_fee",
                    "additional_fee",
                    "total_fees",
                )
            },
        ),
        ("السجل", {"fields": ("created_at", "updated_at")}),
    )


admin.site.register(SiteSettings, SingletonModelAdmin)
