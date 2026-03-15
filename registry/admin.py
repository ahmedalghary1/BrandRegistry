from django.contrib import admin

from .models import Trademark, IndustrialDesign


@admin.register(Trademark)
class TrademarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'status', 'filing_date', 'protection_expiry')
    list_filter = ('status',)
    search_fields = ('name', 'number', 'categories')


@admin.register(IndustrialDesign)
class IndustrialDesignAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'status', 'filing_date', 'protection_expiry')
    list_filter = ('status',)
    search_fields = ('name', 'number')
