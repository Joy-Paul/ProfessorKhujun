# main_app/forms.py
from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

class UniversitySelectionForm(forms.Form):
    country = CountryField(blank_label="-- Select Country --").formfield(
        widget=CountrySelectWidget(attrs={
            'id': 'country-select',
            'class': 'w-full p-2.5 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'
        })
    )
    university_name = forms.ChoiceField(
        choices=[('', '-- Select Country First --')],
        widget=forms.Select(attrs={
            'id': 'university-select',
            'class': 'w-full p-2.5 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
            'disabled': 'disabled'
        })
    )