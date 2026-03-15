from django import forms

from .models import IndustrialDesign, SiteSettings, Trademark


class TrademarkForm(forms.ModelForm):
    class Meta:
        model = Trademark
        fields = [
            'name',
            'image',
            'number',
            'filing_date',
            'categories',
            'status',
            'decision_date',
            'publication_date',
            'publication_number',
            'registration_date',
            'registration_number',
            'rejection_reasons',
            'appeal_date',
            'appeal_hearing_date',
            'filing_fee',
            'examination_fee',
            'publication_fee',
            'registration_fee',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل اسم العلامة التجارية'
            }),
            'number': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل رقم العلامة'
            }),
            'filing_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'categories': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'مثال: 9، 11، 17'
            }),
            'status': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'image': forms.FileInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90'
            }),
            'decision_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'publication_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'publication_number': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل عدد الجريدة'
            }),
            'registration_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل رقم التسجيل'
            }),
            'rejection_reasons': forms.Textarea(attrs={
                'rows': 3,
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل أسباب الرفض إن وجدت'
            }),
            'appeal_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'appeal_hearing_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }


class IndustrialDesignForm(forms.ModelForm):
    class Meta:
        model = IndustrialDesign
        fields = [
            'name',
            'description',
            'image',
            'number',
            'filing_date',
            'status',
            'decision_date',
            'publication_date',
            'publication_number',
            'registration_date',
            'registration_number',
            'rejection_reasons',
            'appeal_date',
            'appeal_hearing_date',
            'filing_fee',
            'examination_fee',
            'publication_fee',
            'registration_fee',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل اسم النموذج الصناعي'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل وصف النموذج الصناعي'
            }),
            'number': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل رقم النموذج'
            }),
            'filing_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'status': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'image': forms.FileInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90'
            }),
            'decision_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'publication_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'publication_number': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل عدد الجريدة'
            }),
            'registration_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل رقم التسجيل'
            }),
            'rejection_reasons': forms.Textarea(attrs={
                'rows': 3,
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'أدخل أسباب الرفض إن وجدت'
            }),
            'appeal_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'appeal_hearing_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border border-gray-300 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['site_title', 'site_subtitle', 'site_logo']
