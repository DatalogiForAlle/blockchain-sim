import factory
from datetime import datetime
from ..models import Blockchain, Block, Miner


class BlockChainFactory(factory.django.DjangoModelFactory):
    """ Blockchain factory """
    class Meta:
        model = Blockchain
    title = 'Blockchain test title'
    creator_name = 'skaber'
    difficulty = 2


class MinerFactory(factory.django.DjangoModelFactory):
    """ Miner factory """
    class Meta:
        model = Miner
    name = 'Bob'
    miner_num = 0
    blockchain = factory.SubFactory(BlockChainFactory)


class BlockFactory(factory.django.DjangoModelFactory):
    """ Creates a genesis block by default """
    class Meta:
        model = Block
    block_num = 0
    blockchain = factory.SubFactory(BlockChainFactory)
    miner = factory.SubFactory(MinerFactory)
    nonce = '0'
    prev_hash = '0'
