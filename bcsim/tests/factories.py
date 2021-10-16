import factory

from ..models import Blockchain, Block


class BCFactory(factory.django.DjangoModelFactory):
    """ Blockchain factory """
    class Meta:
        model = Blockchain
    title = 'Factory title'


class BFactory(factory.django.DjangoModelFactory):
    """ Block factory """
    class Meta:

        model = Block

    block_id = factory.Sequence(lambda n: n)

    blockchain = factory.SubFactory(BCFactory)

    miner_id = 'd98d53'

    payload = 'Genesis'

    nonce = '123456789'

    prev_hash = '8ec6b4b08629031e0ff9464ba22bea7a9b997436e80bf56d169ce942c5d5546f'
