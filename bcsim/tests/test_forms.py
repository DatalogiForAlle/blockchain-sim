"""
To run only the tests in this file:
$ docker-compose run web pytest bcsim/tests/test_forms.py
"""

from ..models import Blockchain, Block
from ..forms import BlockchainForm, BlockForm, JoinForm
from django.core.exceptions import ValidationError
from .factories import BCFactory, BFactory
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


def test_block_form_without_payload_is_invalid(db, blockform_data):
    """ Form is invalid if no payload """

    blockform_data['payload'] = ''
    form = BlockForm(data=blockform_data)

    assert not form.is_valid()
    assert 'payload' in form.errors
    assert not 'nonce' in form.errors


def test_block_form_without_nonce_is_invalid(db, blockform_data):
    """ Form is invalid if no nonce """

    blockform_data['nonce'] = ''
    form = BlockForm(data=blockform_data)

    assert not form.is_valid()
    assert 'nonce' in form.errors
    assert not 'payload' in form.errors


def test_join_form_with_valid_data_is_valid(db):
    """ Form is valid when there is a blockchain with provided id """
    data = {
        'blockchain_id': BCFactory().id
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
