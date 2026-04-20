from pathlib import Path

from django.db.models import DecimalField, ExpressionWrapper, F, Value
from django.db.models.functions import Coalesce
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:  # pragma: no cover - graceful fallback when packages are absent.
    arabic_reshaper = None
    get_display = None


def shape_arabic(text):
    if text in (None, ""):
        return ""
    value = str(text)
    if arabic_reshaper and get_display:
        return get_display(arabic_reshaper.reshape(value))
    return value


def register_arabic_font():
    font_name = "Helvetica"
    bold_name = "Helvetica-Bold"
    candidate_pairs = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("C:/Windows/Fonts/tahoma.ttf"),
            Path("C:/Windows/Fonts/tahomabd.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]

    for regular_path, bold_path in candidate_pairs:
        if regular_path.exists():
            if "ArabicRegular" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ArabicRegular", str(regular_path)))
            font_name = "ArabicRegular"
        if bold_path.exists():
            if "ArabicBold" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ArabicBold", str(bold_path)))
            bold_name = "ArabicBold"
        if font_name != "Helvetica":
            break

    return font_name, bold_name


def with_total_fees(queryset):
    total_expression = (
        Coalesce(F("filing_fee"), Value(0))
        + Coalesce(F("examination_fee"), Value(0))
        + Coalesce(F("publication_fee"), Value(0))
        + Coalesce(F("registration_fee"), Value(0))
        + Coalesce(F("renewal_fee"), Value(0))
        + Coalesce(F("appeal_fee"), Value(0))
        + Coalesce(F("additional_fee"), Value(0))
    )
    return queryset.annotate(
        total_fees_db=ExpressionWrapper(
            total_expression,
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )
