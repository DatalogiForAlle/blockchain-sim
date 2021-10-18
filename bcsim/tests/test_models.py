"""
Model tests.

To run only the tests in this file:
docker-compose run web pytest bcsim/tests/test_models.py
"""

from ..models import Blockchain
import pytest


def test_blockchain_model_id_creation(db):
    """ 
    Blockchain id gets generated when creating new blockchain
    Id does not change when updating a blockchain
    """
    bc = Blockchain.objects.create(title='bc title')

    assert len(bc.id) == 8
    assert type(bc.id) == str

    old_id = bc.id
    bc.title = "new title"
    bc.save()
    bc.refresh_from_db()

    assert bc.title == 'new title'
    assert bc.id == old_id
