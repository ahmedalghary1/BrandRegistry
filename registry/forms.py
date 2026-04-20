from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import IndustrialDesign, SiteSettings, Trademark


TEXT_INPUT_CLASS = "form-control"
TEXTAREA_CLASS = "form-control"
SELECT_CLASS = "form-select"
DATE_CLASS = "form-control"
NUMBER_CLASS = "form-control"
FILE_CLASS = "form-control"
CHECKBOX_CLASS = "form-check-input"


def build_date_widget():
    return forms.DateInput(attrs={"type": "date", "class": DATE_CLASS})


def build_money_widget():
    return forms.NumberInput(
        attrs={
            "class": NUMBER_CLASS,
            "step": "0.01",
            "min": "0",
            "placeholder": "0.00",
        }
    )


class BaseRecordForm(forms.ModelForm):
    basic_fields = ()
    accepted_fields = ()
    rejected_fields = ()
    fee_fields = ()

    class Meta:
        fields = [
            "name",
            "image",
            "number",
            "filing_date",
            "status",
            "decision_date",
            "announcement_date",
            "publication_date",
            "publication_number",
            "registration_date",
            "registration_number",
            "renewal_count",
            "last_renewal_date",
            "rejection_reasons",
            "appeal_date",
            "appeal_hearing_date",
            "filing_fee",
            "examination_fee",
            "publication_fee",
            "registration_fee",
            "renewal_fee",
            "appeal_fee",
            "additional_fee",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "image": forms.ClearableFileInput(attrs={"class": FILE_CLASS, "accept": "image/*"}),
            "number": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "filing_date": build_date_widget(),
            "status": forms.Select(attrs={"class": SELECT_CLASS}),
            "decision_date": build_date_widget(),
            "announcement_date": build_date_widget(),
            "publication_date": build_date_widget(),
            "publication_number": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "registration_date": build_date_widget(),
            "registration_number": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "renewal_count": forms.NumberInput(
                attrs={"class": NUMBER_CLASS, "min": "0", "step": "1", "placeholder": "0"}
            ),
            "last_renewal_date": build_date_widget(),
            "rejection_reasons": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4}),
            "appeal_date": build_date_widget(),
            "appeal_hearing_date": build_date_widget(),
            "filing_fee": build_money_widget(),
            "examination_fee": build_money_widget(),
            "publication_fee": build_money_widget(),
            "registration_fee": build_money_widget(),
            "renewal_fee": build_money_widget(),
            "appeal_fee": build_money_widget(),
            "additional_fee": build_money_widget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        optional_fields = (
            set(self.accepted_fields)
            | set(self.rejected_fields)
            | set(self.fee_fields)
            | {"image", "renewal_count", "last_renewal_date"}
        )
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        placeholders = {
            "name": self.get_name_placeholder(),
            "number": self.get_number_placeholder(),
            "publication_number": "مثال: 125",
            "registration_number": "مثال: TM-2026-18",
            "renewal_count": "0",
        }
        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.setdefault("placeholder", placeholder)

        self.fields["rejection_reasons"].widget.attrs.setdefault(
            "placeholder",
            "اكتب أسباب الرفض وملخص القرار.",
        )

        for field_name in self.fee_fields:
            self.fields[field_name].initial = self.initial.get(field_name, Decimal("0.00"))

        self.fields["status"].help_text = "يتم إظهار الحقول المناسبة لكل مرحلة تلقائيًا."
        self.configure_dynamic_widgets()

    def configure_dynamic_widgets(self):
        role_fields = {
            "status": "status-field",
            "filing_date": "filing-date",
            "publication_date": "publication-date",
            "image": "image-input",
        }
        required_map = {
            "decision_date": "accepted,registered,rejected",
            "announcement_date": "accepted,registered",
            "publication_date": "accepted,registered",
            "publication_number": "accepted,registered",
            "registration_date": "registered",
            "registration_number": "registered",
            "rejection_reasons": "rejected",
        }

        for field_name, role in role_fields.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["data-role"] = role

        for field_name, required_for in required_map.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["data-required-for"] = required_for

        for field_name in self.fee_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["data-fee-field"] = "true"
                self.fields[field_name].widget.attrs.setdefault("inputmode", "decimal")

    def get_name_placeholder(self):
        return "أدخل الاسم"

    def get_number_placeholder(self):
        return "أدخل الرقم"

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and image.size > 5 * 1024 * 1024:
            raise ValidationError("الحد الأقصى لحجم الصورة هو 5 ميجابايت.")
        return image

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        for field_name in self.fee_fields:
            if cleaned_data.get(field_name) in (None, ""):
                cleaned_data[field_name] = Decimal("0.00")

        if cleaned_data.get("renewal_count") in (None, ""):
            cleaned_data["renewal_count"] = 0

        for field_name in self.Meta.fields:
            if field_name in cleaned_data:
                setattr(self.instance, field_name, cleaned_data[field_name])

        self.instance.clear_irrelevant_fields()

        for field_name in self.Meta.fields:
            if hasattr(self.instance, field_name):
                cleaned_data[field_name] = getattr(self.instance, field_name)

        return cleaned_data


class TrademarkForm(BaseRecordForm):
    basic_fields = ("name", "image", "number", "filing_date", "categories", "status")
    accepted_fields = (
        "decision_date",
        "announcement_date",
        "publication_date",
        "publication_number",
        "registration_date",
        "registration_number",
    )
    rejected_fields = (
        "decision_date",
        "rejection_reasons",
        "appeal_date",
        "appeal_hearing_date",
    )
    fee_fields = (
        "filing_fee",
        "examination_fee",
        "publication_fee",
        "registration_fee",
        "renewal_fee",
        "appeal_fee",
        "additional_fee",
    )

    class Meta(BaseRecordForm.Meta):
        model = Trademark
        fields = BaseRecordForm.Meta.fields[:5] + ["categories"] + BaseRecordForm.Meta.fields[5:]
        widgets = {
            **BaseRecordForm.Meta.widgets,
            "categories": forms.TextInput(
                attrs={
                    "class": TEXT_INPUT_CLASS,
                    "placeholder": "مثال: 9، 11، 17",
                }
            ),
        }

    def get_name_placeholder(self):
        return "اسم العلامة التجارية"

    def get_number_placeholder(self):
        return "رقم العلامة"


class IndustrialDesignForm(BaseRecordForm):
    basic_fields = ("name", "description", "image", "number", "filing_date", "status")
    accepted_fields = (
        "decision_date",
        "announcement_date",
        "publication_date",
        "publication_number",
        "registration_date",
        "registration_number",
    )
    rejected_fields = (
        "decision_date",
        "rejection_reasons",
        "appeal_date",
        "appeal_hearing_date",
    )
    fee_fields = TrademarkForm.fee_fields

    class Meta(BaseRecordForm.Meta):
        model = IndustrialDesign
        fields = BaseRecordForm.Meta.fields[:1] + ["description"] + BaseRecordForm.Meta.fields[1:]
        widgets = {
            **BaseRecordForm.Meta.widgets,
            "description": forms.Textarea(
                attrs={
                    "class": TEXTAREA_CLASS,
                    "rows": 4,
                    "placeholder": "وصف مختصر للشكل أو التصميم أو الاستخدام.",
                }
            ),
        }

    def get_name_placeholder(self):
        return "اسم النموذج الصناعي"

    def get_number_placeholder(self):
        return "رقم النموذج"


class RecordFilterForm(forms.Form):
    search_name = forms.CharField(
        label="الاسم",
        required=False,
        widget=forms.TextInput(
            attrs={"class": TEXT_INPUT_CLASS, "placeholder": "ابحث بالاسم"}
        ),
    )
    search_number = forms.CharField(
        label="الرقم",
        required=False,
        widget=forms.TextInput(
            attrs={"class": TEXT_INPUT_CLASS, "placeholder": "ابحث بالرقم"}
        ),
    )
    status = forms.ChoiceField(
        label="القرار",
        required=False,
        choices=[("", "كل الحالات")] + Trademark.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    filing_date_from = forms.DateField(
        label="من تاريخ إيداع",
        required=False,
        widget=build_date_widget(),
    )
    filing_date_to = forms.DateField(
        label="إلى تاريخ إيداع",
        required=False,
        widget=build_date_widget(),
    )
    expiring_only = forms.BooleanField(
        label="قرب انتهاء الحماية خلال 30 يومًا",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
    )
    fees_min = forms.DecimalField(
        label="الحد الأدنى للرسوم",
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=12,
        widget=build_money_widget(),
    )
    fees_max = forms.DecimalField(
        label="الحد الأعلى للرسوم",
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=12,
        widget=build_money_widget(),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("filing_date_from")
        date_to = cleaned_data.get("filing_date_to")
        fees_min = cleaned_data.get("fees_min")
        fees_max = cleaned_data.get("fees_max")

        if date_from and date_to and date_from > date_to:
            self.add_error("filing_date_to", "تاريخ النهاية يجب أن يكون بعد تاريخ البداية.")

        if fees_min is not None and fees_max is not None and fees_min > fees_max:
            self.add_error("fees_max", "الحد الأعلى يجب أن يكون أكبر من الحد الأدنى.")

        return cleaned_data


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["site_title", "site_subtitle", "site_logo"]
        widgets = {
            "site_title": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "site_subtitle": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "site_logo": forms.ClearableFileInput(
                attrs={"class": FILE_CLASS, "accept": "image/*"}
            ),
        }
