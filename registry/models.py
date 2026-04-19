from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from solo.models import SingletonModel


def add_years(value, years):
    if not value:
        return None
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        # Handles leap-day filings by moving to the last valid day in February.
        return value.replace(month=2, day=28, year=value.year + years)


class BaseIPModel(models.Model):
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_REGISTERED = "registered"

    STATUS_CHOICES = [
        (STATUS_UNDER_REVIEW, "تحت الفحص"),
        (STATUS_ACCEPTED, "قبول"),
        (STATUS_REJECTED, "رفض"),
        (STATUS_REGISTERED, "تسجيل"),
    ]

    status = models.CharField(
        "القرار",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_UNDER_REVIEW,
        db_index=True,
    )
    filing_date = models.DateField("تاريخ الإيداع", db_index=True)
    decision_date = models.DateField("تاريخ القرار", null=True, blank=True)
    announcement_date = models.DateField("تاريخ الإشهار", null=True, blank=True)
    publication_date = models.DateField(
        "تاريخ النشر عن القبول",
        null=True,
        blank=True,
    )
    publication_number = models.CharField("عدد الجريدة", max_length=100, blank=True)
    registration_date = models.DateField("تاريخ التسجيل", null=True, blank=True)
    registration_number = models.CharField("رقم التسجيل", max_length=100, blank=True)
    rejection_reasons = models.TextField("أسباب الرفض", blank=True)
    appeal_date = models.DateField("تاريخ التظلم", null=True, blank=True)
    appeal_hearing_date = models.DateField("تاريخ جلسة التظلم", null=True, blank=True)

    filing_fee = models.DecimalField(
        "رسوم الإيداع", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    examination_fee = models.DecimalField(
        "رسوم الفحص", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    publication_fee = models.DecimalField(
        "رسوم النشر", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    registration_fee = models.DecimalField(
        "رسوم التسجيل", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    appeal_fee = models.DecimalField(
        "رسوم التظلم", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    additional_fee = models.DecimalField(
        "رسوم إضافية", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    @property
    def publication_deadline(self):
        if not self.publication_date:
            return None
        return self.publication_date + timedelta(days=60)

    @property
    def publication_expiry(self):
        return self.publication_deadline

    @property
    def protection_expiry(self):
        return add_years(self.filing_date, 10)

    @property
    def total_fees(self):
        fees = (
            self.filing_fee,
            self.examination_fee,
            self.publication_fee,
            self.registration_fee,
            self.appeal_fee,
            self.additional_fee,
        )
        return sum((fee or Decimal("0.00") for fee in fees), Decimal("0.00"))

    @property
    def days_until_expiry(self):
        expiry = self.protection_expiry
        if not expiry:
            return None
        return (expiry - timezone.localdate()).days

    @property
    def is_approaching_protection_expiry(self):
        days = self.days_until_expiry
        return days is not None and 0 <= days <= 30

    def clear_irrelevant_fields(self):
        if self.status == self.STATUS_UNDER_REVIEW:
            self.decision_date = None
            self.announcement_date = None
            self.publication_date = None
            self.publication_number = ""
            self.registration_date = None
            self.registration_number = ""
            self.rejection_reasons = ""
            self.appeal_date = None
            self.appeal_hearing_date = None
            self.publication_fee = Decimal("0.00")
            self.registration_fee = Decimal("0.00")
            self.appeal_fee = Decimal("0.00")
            return

        if self.status in {self.STATUS_ACCEPTED, self.STATUS_REGISTERED}:
            self.rejection_reasons = ""
            self.appeal_date = None
            self.appeal_hearing_date = None
            self.appeal_fee = Decimal("0.00")
            return

        if self.status == self.STATUS_REJECTED:
            self.announcement_date = None
            self.publication_date = None
            self.publication_number = ""
            self.registration_date = None
            self.registration_number = ""
            self.publication_fee = Decimal("0.00")
            self.registration_fee = Decimal("0.00")

    def clean(self):
        errors = {}

        if self.decision_date and self.filing_date and self.decision_date < self.filing_date:
            errors["decision_date"] = "تاريخ القرار يجب أن يكون بعد أو مساويًا لتاريخ الإيداع."

        if self.announcement_date and self.decision_date and self.announcement_date < self.decision_date:
            errors["announcement_date"] = "تاريخ الإشهار يجب أن يكون بعد تاريخ القرار."

        if self.publication_date and self.announcement_date and self.publication_date < self.announcement_date:
            errors["publication_date"] = "تاريخ النشر يجب أن يكون بعد تاريخ الإشهار."

        if self.registration_date and self.filing_date and self.registration_date < self.filing_date:
            errors["registration_date"] = "تاريخ التسجيل يجب أن يكون بعد تاريخ الإيداع."

        if self.appeal_hearing_date and self.appeal_date and self.appeal_hearing_date < self.appeal_date:
            errors["appeal_hearing_date"] = "تاريخ جلسة التظلم يجب أن يكون بعد تاريخ التظلم."

        if self.status in {self.STATUS_ACCEPTED, self.STATUS_REGISTERED}:
            for field_name in ("decision_date", "announcement_date", "publication_date"):
                if not getattr(self, field_name):
                    errors[field_name] = "هذا الحقل مطلوب لهذه المرحلة."
            if not self.publication_number:
                errors["publication_number"] = "عدد الجريدة مطلوب في حالات القبول والتسجيل."

        if self.status == self.STATUS_REGISTERED:
            if not self.registration_date:
                errors["registration_date"] = "تاريخ التسجيل مطلوب عند اختيار حالة تسجيل."
            if not self.registration_number:
                errors["registration_number"] = "رقم التسجيل مطلوب عند اختيار حالة تسجيل."

        if self.status == self.STATUS_REJECTED:
            if not self.decision_date:
                errors["decision_date"] = "تاريخ القرار مطلوب عند الرفض."
            if not self.rejection_reasons:
                errors["rejection_reasons"] = "أسباب الرفض مطلوبة عند الرفض."

        if errors:
            raise ValidationError(errors)


class Trademark(BaseIPModel):
    name = models.CharField("اسم العلامة التجارية", max_length=255, db_index=True)
    image = models.ImageField(
        "صورة العلامة",
        upload_to="trademarks/",
        blank=True,
        null=True,
    )
    number = models.CharField("رقم العلامة", max_length=100, db_index=True)
    categories = models.CharField("فئات العلامة", max_length=255, blank=True)

    class Meta(BaseIPModel.Meta):
        verbose_name = "علامة تجارية"
        verbose_name_plural = "العلامات التجارية"

    def __str__(self):
        return f"{self.name} ({self.number})"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("registry:trademarks:detail", kwargs={"pk": self.pk})


class IndustrialDesign(BaseIPModel):
    name = models.CharField("اسم النموذج الصناعي", max_length=255, db_index=True)
    description = models.TextField("وصف النموذج", blank=True)
    image = models.ImageField(
        "صورة النموذج",
        upload_to="designs/",
        blank=True,
        null=True,
    )
    number = models.CharField("رقم النموذج", max_length=100, db_index=True)

    class Meta(BaseIPModel.Meta):
        verbose_name = "نموذج صناعي"
        verbose_name_plural = "النماذج الصناعية"

    def __str__(self):
        return f"{self.name} ({self.number})"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("registry:designs:detail", kwargs={"pk": self.pk})


# Alias retained for code readability and future compatibility while preserving
# the current database/table structure.
IndustrialModel = IndustrialDesign


class SiteSettings(SingletonModel):
    site_title = models.CharField(
        "عنوان النظام",
        max_length=255,
        default="نظام إدارة العلامات والنماذج الصناعية",
    )
    site_subtitle = models.CharField(
        "وصف مختصر",
        max_length=255,
        default="إدارة محلية متكاملة للعلامات التجارية والنماذج الصناعية",
    )
    site_logo = models.ImageField(
        "شعار النظام",
        upload_to="logos/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "إعدادات النظام"
        verbose_name_plural = "إعدادات النظام"

    def __str__(self):
        return "إعدادات النظام"
