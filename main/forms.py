from django import forms
from .models import BetTicketSelection, BetTicket


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