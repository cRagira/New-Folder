from django import forms
from .models import BetTicketSelection


class betForm(forms.ModelForm):
    class Meta:
        model = BetTicketSelection
        fields = ['']
