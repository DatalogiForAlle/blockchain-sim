"""
To run only the tests in this file:
$ docker-compose run web pytest bcsim/tests/test_forms.py
"""

from ..models import Blockchain, Block
from ..forms import BlockchainForm, BlockForm, JoinForm
from django.core.exceptions import ValidationError
from .factories import BlockChainFactory, BlockFactory, MinerFactory
import pytest


def test_blockchain_form_can_create(db):
    """ Submitting a valid blockchain form creates a blockchain."""
    data = {'title': 'bc title'}
    form = BlockchainForm(data=data)

    assert form.is_valid()

    form.save()
    assert Blockchain.objects.filter(title='bc title').count() == 1


def test_blockchain_form_title_is_required(db):
    """ Blockchain form w/o title is invalid."""
    data = {'title': ''}
    form = BlockchainForm(data=data)

    assert not form.is_valid()


@pytest.fixture
def blockform_data():
    return {
        'payload': 'test payload',
        'nonce': '12345'
    }


def test_block_form_is_valid(db, blockform_data):
    """ Test valid data gives valid block """

    form = BlockForm(data=blockform_data)
    assert form.is_valid()


def test_block_form_nonce_has_to_be_integer_1(db, blockform_data):
    """ Form is invalid if nonce is not an integer """

    blockform_data['nonce'] = 'fdd324'
    form = BlockForm(data=blockform_data)

    assert not form.is_valid()
    assert 'nonce' in form.errors
    assert not 'payload' in form.errors


def test_block_form_nonce_has_to_be_integer_2(db, blockform_data):
    """ Form is invalid if nonce is not an integer """
    blockform_data['nonce'] = '1.45'
    form = BlockForm(data=blockform_data)

    assert not form.is_valid()
    assert 'nonce' in form.errors
    assert not 'payload' in form.errors


def test_join_form_with_valid_data_is_valid(db):
    """ Form is valid when there is a blockchain with provided id """
    data = {
        'blockchain_id': BlockChainFactory().id,
        'name': 'Alice'
    }
    form = JoinForm(data=data)

    assert form.is_valid()


def test_join_form_with_invalid_data_is_invalid(db):
    """ Form is invalid when there is no blockchain with provided id """
    bc_id_with_no_referent = 'abcdefgh'
    data = {
        'blockchain_id': bc_id_with_no_referent
    }
    form = JoinForm(data=data)

    assert not form.is_valid()
    assert 'Der findes ingen blokkæde med dette ID.' in form.errors['blockchain_id']

def test_join_form_name_is_required(db):
    data = {
        'blockchain_id': BlockChainFactory().id,
        'name': ''
    }
    form = JoinForm(data=data)

    assert not form.is_valid()
    assert 'name' in form.errors
    assert 'Dette felt er påkrævet' in form.errors['name']
   

def test_join_form_name_is_required(db):
    data = {
        'blockchain_id': '',
        'name': 'Bob'
    }
    form = JoinForm(data=data)

    assert not form.is_valid()
    assert 'blockchain_id' in form.errors


def test_name_has_to_be_unique_on_blockchain(db):
    """ Form is invalid if there is already a miner in the blockchai with the requested name """
    blockchain = BlockChainFactory()
    miner = MinerFactory(name="grethen", blockchain=blockchain)
    data = {'name': 'grethen', 'blockchain_id': blockchain.id}
    form = JoinForm(data=data)

    assert not form.is_valid()
    assert "Der er allerede en minearbejder med dette navn i blokkæden." in str(
        form)

def test_name_used_on_another_blockchain_is_not_a_problem(db):
    """ Form should not be invalid if there is a miner with the wanted name on another blockchain """
    bc1 = BlockChainFactory()
    bc2 = BlockChainFactory()
    MinerFactory(name="grethen", blockchain=bc1)
    data = {'name': 'grethen', 'blockchain_id': bc2.id}
    form = JoinForm(data=data)

    assert form.is_valid()
