from django import forms
from .models import Blockchain, Block
#from django.core.exceptions import ValidationError


class CreateBlockchainForm(forms.ModelForm):
    class Meta:
        model = Blockchain

        fields = ['title']

        labels = {
            'title': 'Hvad skal vi kalde din blockchain?',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Min smukke nye blockchain'}),
            #CharField(widget=forms.Textarea),
            #'initial_balance': forms.NumberInput(attrs={'step': 0.01, 'onchange': "setTwoNumberDecimal(this)"}),
            #'min_cost': forms.NumberInput(attrs={'step': 0.01, 'onchange': "setTwoNumberDecimal(this)"}),
            #'max_cost': forms.NumberInput(attrs={'step': 0.01, 'onchange': "setTwoNumberDecimal(this)"})
        }

