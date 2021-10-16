import pytest


@pytest.fixture
def logged_in_user(db, client):

    session = client.session
    session['blockchain_id'] = '12345678'
    session['miner_id'] = '123456'
    session.save()
    return client
