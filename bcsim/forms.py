"""
When working with forms: 
1) Ensure that GET requests (and other ‘safe’ methods, as defined by RFC 7231#section-4.2.1) are side effect free.)
2) In any template that uses a POST form, use the csrf_token tag inside the <form> element if the form is for an internal URL, e.g.:
    <form method="post">{% csrf_token %}</form>

Read more: https://docs.djangoproject.com/en/3.2/ref/csrf/
"""
from django import forms
from .models import Blockchain, Block, Miner


class BlockchainForm(forms.ModelForm):
    """ Form used to create a blockchain """
    class Meta:
        model = Blockchain
        fields = ['title', 'creator_name', 'type', 'difficulty']
        labels = {
            'title': 'Hvad skal vi kalde din blockchain?', 
            'creator_name': 'Dit navn/holdnavn',
            'type': 'Type',
            'difficulty': 'Sværhedsgrad',
            }
        help_texts = {
            'creator_name': 'Du deltager automatisk som minearbejder i din egen blockchain. Det er dit minearbejdernavn/holdnavn, du vælger her',
            'title': 'Titlen, du vælger her, vil fremgå som overskrift på din blockchain',
            'type':
                'Hvilken slags blockchain ønsker du at skabe?<br>' +
                ' - Uden token-marked: Transaktionerne er mellem tilfældige fiktive personer<br>' +
                ' - Med token-marked: Transaktioner opstår, når minearbejdere køber og sælger tokens af hinanden<br>',
            'difficulty': 
                'Hvor svært skal det være at føje blokke til din blockchain?<br>' +
                ' - Nem: Gyldige hashes starter med 0 eller 1 (ca. 12 % af alle hashes gyldige)<br>' +
                ' - Middel: Gyldige hashes starter med 0 (ca. 6% af alle hashes er gyldige)<br>' +
                ' - Svær: Gyldige hashes starter med 00 (ca. 0,4% af alle hashes er gyldige)' 
            }

class JoinForm(forms.ModelForm):
    """ Form used to join a blockchain """
    blockchain_id = forms.CharField(max_length=8, label="Blockchain ID",
                                help_text="Indtast ID'et på den blockchain, du vil deltage i")

    class Meta:
        model = Miner
        fields = ['name']
        labels = {
            'name': 'Dit navn/holdnavn',
        }
        help_texts = {
            'name': 'Navnet, du vælger her, vil være synligt for de andre deltagere i blockchainen',
        }

    def clean_blockchain_id(self):
        """ Additional validation of the form's blockchain_id field """
        blockchain_id = self.cleaned_data['blockchain_id'].lower()
        if not Blockchain.objects.filter(id=blockchain_id).exists():
            raise forms.ValidationError(
                'Der findes ingen blockchain med dette ID.')
        return blockchain_id

    def clean(self):
        """
        Additional validation of form data:
        Validate that there are no other users on the blockchain with the chosen username
        """
        cleaned_data = super().clean()
        cleaned_name = cleaned_data.get("name")
        cleaned_blockchain_id = cleaned_data.get('blockchain_id')
        if cleaned_name and cleaned_blockchain_id:
            blockchain = Blockchain.objects.get(id=cleaned_blockchain_id)
            if Miner.objects.filter(name=cleaned_name, blockchain=blockchain).exists():
                raise forms.ValidationError(
                    'Der er allerede en minearbejder med dette navn i blockchainen. Vælg et andet navn.')
        return cleaned_data



class BlockForm(forms.ModelForm):
    """ Form used to create a block """
    class Meta:
        model = Block
        fields = ['nonce']
        labels = {
            'nonce': 'Nonce:',
        }
        

    def clean_nonce(self):
        """ Nonce has to be a non-zero positive 32 bit integer """
        nonce = self.cleaned_data['nonce']
        if nonce is None:
            raise forms.ValidationError(
            'Du skal angive Nonce')

        else:
            if not 0 <= nonce <= 2**32 - 1:
                raise forms.ValidationError(
                    'Nonce skal være et ikke-negativt heltal på max 4294967295 (32-bit)')
        return nonce


class LoginForm(forms.Form):
    """ Form to login to existing block as existing user """

    blockchain_id = forms.CharField(max_length=8, label="Blockchain ID",
                                    help_text="Indtast blockchainens ID")
    
    miner_id = forms.CharField(max_length=8, label="Minearbejder-ID",
                               help_text="Indtast dit minearbejder-ID")

    def clean_blockchain_id(self):
        """ Additional validation of the form's blockchain_id field """
        blockchain_id = self.cleaned_data['blockchain_id'].lower()
        if not Blockchain.objects.filter(id=blockchain_id).exists():
            raise forms.ValidationError(
                'Der findes ingen blockchain med dette ID.')
        return blockchain_id

    def clean_miner_id(self):
        """ Additional validation of the form's min_id field """
        miner_id = self.cleaned_data['miner_id'].lower()
        if not Miner.objects.filter(id=miner_id).exists():
            raise forms.ValidationError(
                'Der findes ingen minearbejder med dette ID.')
        return miner_id


class TokenPriceForm(forms.Form):
    price = forms.IntegerField()
    
    def clean_price(self):
        max_price = 10**6
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError(
                'Prisen kan ikke være negativ.')
        elif price > max_price:
            raise forms.ValidationError(
                f'Prisen kan ikke være større end {max_price}')

        return price
