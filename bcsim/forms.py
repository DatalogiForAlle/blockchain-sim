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


class JoinBlockchainForm(forms.Form):
    # perhaps make this a modelform instead?

    blockchain_id = forms.CharField(label='Blockchain ID', max_length=16)

    def clean_blockchain_id(self):
        """ Additional validation of the form's blockchain_id field """
        blockchain_id = self.cleaned_data['blockchain_id'].lower()
        print("bcid", blockchain_id)
        if not Blockchain.objects.filter(id=blockchain_id).exists():
            print("does not exist")

            raise forms.ValidationError('There is no blockchain with this ID')
        else:
            print("does exist")

        return blockchain_id


class BlockForm(forms.ModelForm):

    blockchain_id = forms.CharField(label='Blockchain ID', max_length=16)

    class Meta:
        model = Block

        fields = [
            'block_num',
            'miner_id',
            'created_at',
            'payload',
            'nonce',
            'prev_hash'

        ]
