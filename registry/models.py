from django.db import models
from django.utils import timezone
from datetime import timedelta
from solo.models import SingletonModel


class BaseIPModel(models.Model):
    """Base model for shared fields between trademarks and industrial designs."""

    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_UNDER_REVIEW, 'تحت الفحص'),
        (STATUS_ACCEPTED, 'مقبول'),
        (STATUS_REJECTED, 'مرفوض'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_UNDER_REVIEW,
        verbose_name='الحالة',
    )

    filing_date = models.DateField(verbose_name='تاريخ الإيداع')
    decision_date = models.DateField(
        null=True, blank=True, verbose_name='تاريخ القرار'
    )
    publication_date = models.DateField(
        null=True, blank=True, verbose_name='تاريخ النشر عن القبول'
    )
    publication_number = models.CharField(
        max_length=100, blank=True, verbose_name='عدد الجريدة'
    )
    registration_date = models.DateField(
        null=True, blank=True, verbose_name='تاريخ التسجيل'
    )
    registration_number = models.CharField(
        max_length=100, blank=True, verbose_name='رقم التسجيل'
    )
    rejection_reasons = models.TextField(
        blank=True, verbose_name='أسباب الرفض'
    )
    appeal_date = models.DateField(
        null=True, blank=True, verbose_name='تاريخ التظلم'
    )
    appeal_hearing_date = models.DateField(
        null=True, blank=True, verbose_name='تاريخ جلسة التظلم'
    )

    # Fees fields for each stage
    filing_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='رسوم الإيداع'
    )
    examination_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='رسوم الفحص'
    )
    publication_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='رسوم النشر'
    )
    registration_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='رسوم التسجيل'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def protection_expiry(self):
        """Protection expiry is 10 years after filing."""
        if self.filing_date:
            return self.filing_date + timedelta(days=365 * 10)
        return None

    @property
    def publication_expiry(self):
        """Publication expiry is 60 days after publication date."""
        if self.publication_date:
            return self.publication_date + timedelta(days=60)
        return None

    @property
    def is_approaching_protection_expiry(self):
        """Return True when protection expiry is within 30 days."""
        expiry = self.protection_expiry
        if not expiry:
            return False
        return 0 <= (expiry - timezone.localdate()).days <= 30


class Trademark(BaseIPModel):
    name = models.CharField(max_length=255, verbose_name='اسم العلامة التجارية')
    image = models.ImageField(
        upload_to='trademarks/', blank=True, null=True, verbose_name='صورة العلامة'
    )
    number = models.CharField(max_length=100, verbose_name='رقم العلامة')
    categories = models.CharField(
        max_length=255, blank=True, verbose_name='الفئات (مفصولة بفواصل)'
    )

    def __str__(self):
        return f"{self.name} ({self.number})"


class IndustrialDesign(BaseIPModel):
    name = models.CharField(max_length=255, verbose_name='اسم النموذج')
    description = models.TextField(blank=True, verbose_name='وصف النموذج')
    image = models.ImageField(
        upload_to='designs/', blank=True, null=True, verbose_name='صورة النموذج'
    )
    number = models.CharField(max_length=100, verbose_name='رقم النموذج')

    def __str__(self):
        return f"{self.name} ({self.number})"


class SiteSettings(SingletonModel):
    site_title = models.CharField('عنوان الموقع', max_length=255, default='الهيئة العامة للعلامات والنماذج الصناعية')
    site_subtitle = models.CharField('وصف الموقع', max_length=255, default='للعلامات والنماذج الصناعية')
    site_logo = models.ImageField('شعار الموقع', upload_to='logos/', null=True, blank=True)

    class Meta:
        verbose_name = 'إعدادات الموقع'
        verbose_name_plural = 'إعدادات الموقع'

    def __str__(self):
        return 'إعدادات الموقع'
