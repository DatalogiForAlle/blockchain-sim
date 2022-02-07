"""
Model tests.

To run only the tests in this file:
make test_models

To run only one or some tests:
docker-compose -f docker-compose.dev.yml run web pytes -k <substring of test function names to run>
"""

from ..models import Blockchain
import pytest


def test_blockchain_model_id_creation(db):
    """ 
    Blockchain id gets generated when creating new blockchain
    """
    bc = Blockchain.objects.create(title='bc title')

    assert len(bc.id) == 8
    assert type(bc.id) == str


def test_blockchain_model_id_creation(db):
    """ Blockchain-dd does not change when updating an existing blockchain """

    bc = Blockchain.objects.create(title='bc title')
    old_id = bc.id

    bc.title = "new title"
    bc.save()

    assert bc.title == 'new title'
    assert bc.id == old_id


def test_blockchain_model_easy_hash_is_valid_method(db):
    """ Hashes beginning with 0 or 1 are valid in EASY mode """
    bc = Blockchain.objects.create(
        title='bc title', difficulty=Blockchain.Level.EASY)
    assert bc.hash_is_valid("0werger9")
    assert bc.hash_is_valid("13erger9")
    assert not bc.hash_is_valid("20werger9")


def test_blockchain_model_medium_hash_is_valid_method(db):
    """ Hashes beginning with 0 are valid in MEDIUM mode """
    bc = Blockchain.objects.create(
        title='bc title', difficulty=Blockchain.Level.MEDIUM)
    assert bc.hash_is_valid("0werger9")
    assert not bc.hash_is_valid("13erger9")
    assert not bc.hash_is_valid("20werger9")


def test_blockchain_model_hard_hash_is_valid_method(db):
    """ Hashes beginning with 00 are valid in MEDIUM mode """
    bc = Blockchain.objects.create(
        title='bc title', difficulty=Blockchain.Level.DIFFICULT)
    assert not bc.hash_is_valid("0werger9")
    assert not bc.hash_is_valid("13erger9")
    assert bc.hash_is_valid("00werger9")
