from django import forms
from .models import BetTicketSelection, BetTicket, Profile


class ticketSelectionForm(forms.ModelForm):
    class Meta:
        model = BetTicketSelection
        fields = ['match','selection','odds',]

class ticketForm(forms.ModelForm):
    class Meta:
        model=BetTicket
        fields=['user','stake_amount','total_odds',]

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

from django_countries.fields import CountryField

from django_countries.widgets import CountrySelectWidget

class CustomForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("country",)
        widgets = {"country": CountrySelectWidget()}