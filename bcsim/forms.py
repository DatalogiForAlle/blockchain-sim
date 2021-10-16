"""
When working with forms: 
1) Ensure that GET requests (and other ‘safe’ methods, as defined by RFC 7231#section-4.2.1) are side effect free.)
2) In any template that uses a POST form, use the csrf_token tag inside the <form> element if the form is for an internal URL, e.g.:
    <form method="post">{% csrf_token %}</form>

Read more: https://docs.djangoproject.com/en/3.2/ref/csrf/
"""
from django import forms
from .models import Blockchain, Block


class BlockchainForm(forms.ModelForm):
    """ Form used to create a blockchain """
    class Meta:
        model = Blockchain
        fields = ['title']
        labels = {'title': 'Hvad skal vi kalde din blokkæde?', }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': "Eksempel på et godt navn til en blokkæde"}),
        }


class JoinForm(forms.Form):
    """ Form used to join a blockchain """
    blockchain_id = forms.CharField(label="Angiv blokkædens ID")

    def clean_blockchain_id(self):
        """ Additional validation of the form's blockchain_id field """
        blockchain_id = self.cleaned_data['blockchain_id'].lower()
        if not Blockchain.objects.filter(id=blockchain_id).exists():
            raise forms.ValidationError(
                'Der findes ingen blokkæde med dette ID.')
        return blockchain_id


class BlockForm(forms.ModelForm):
    """ Form used to create a block """
    class Meta:
        model = Block
        fields = ['payload', 'nonce']
        widgets = {
            'payload': forms.TextInput(attrs={'class': 'form-control form-inline'}),
        }
