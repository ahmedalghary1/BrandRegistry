from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.simple_tag
def querystring(request, **kwargs):
    query = request.GET.copy()
    for key, value in kwargs.items():
        if value in (None, "", False):
            query.pop(key, None)
        else:
            query[key] = value
    encoded = query.urlencode()
    return f"?{encoded}" if encoded else "?"


@register.filter
def currency(value):
    if value in (None, ""):
        return "0.00"
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    return f"{amount:,.2f}"


@register.filter
def decision_badge_class(value):
    mapping = {
        "under_review": "badge badge-warning",
        "accepted": "badge badge-info",
        "rejected": "badge badge-danger",
        "registered": "badge badge-success",
    }
    return mapping.get(value, "badge")
