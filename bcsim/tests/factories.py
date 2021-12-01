import factory
from datetime import datetime
from ..models import Blockchain, Block, Miner


class BlockChainFactory(factory.django.DjangoModelFactory):
    """ Blockchain factory """
    class Meta:
        model = Blockchain
    title = 'Blockchain test title'


class BlockFactory(factory.django.DjangoModelFactory):
    """ Creates a genesis block by default """
    class Meta:

        model = Block

    block_id = 0
    blockchain = factory.SubFactory(BlockChainFactory)
    miner_id = '0'
    payload = 'Genesis'
    nonce = '0'
    prev_hash = '0'

class MinerFactory(factory.django.DjangoModelFactory):
    """ Miner factory """
    class Meta:
        model = Miner
    name = 'Bob'
    blockchain = factory.SubFactory(BlockChainFactory)
