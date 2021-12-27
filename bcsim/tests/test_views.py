"""
To run all tests in this file:
make test_views 

To run only one or some tests:
docker-compose -f docker-compose.dev.yml run web pytes -k <substring of test function names to run>
"""

from django.core.exceptions import ValidationError
from django.urls import reverse
from ..models import Blockchain, Block
from ..forms import BlockchainForm, BlockForm, JoinForm
from ..views import hash_context, next_payload
from .factories import BlockChainFactory, BlockFactory, BlockFactory, MinerFactory
import pytest
from pytest_django.asserts import assertTemplateUsed, assertContains, assertNotContains
from datetime import datetime

def test_participants_view(db, client):
    """
    Participants view exists at correct url and uses correct template.
    """
    miner = MinerFactory()
    session = client.session
    session['blockchain_id'] = miner.blockchain.id
    session['miner_id'] = miner.id
    session.save()


    response = client.get(reverse('bcsim:participants'))
    
    assert response.status_code == 200
    assertTemplateUsed(response, 'bcsim/participants.html')


def test_home_view_get_request(client):
    """
    Home view exists at correct url, uses correct template. Template also includes correct forms.
    """
    response = client.get(reverse('bcsim:home'))

    assert response.status_code == 200
    assertTemplateUsed(response, 'bcsim/home.html')
    assert isinstance(response.context['join_form'], JoinForm)
    assert isinstance(response.context['create_form'], BlockchainForm)


def test_home_view_post_request_join_submit_valid(db, client):
    """
    Submitting a post-request to join a block does the following,
    when a blockchain with the provided id exits
    1) Creates session data
    2) Redirects to 'mine'
    """
    # client joins a blockchain that exists
    data = {
        'blockchain_id': BlockChainFactory().id,
        'name': 'Bob',
        'join_bc': 'submit'
    }
    response = client.post(reverse('bcsim:home'), data=data)

    # correct session data is now createad
    assert 'xxx' not in client.session
    assert 'miner_id' in client.session
    assert 'blockchain_id' in client.session
    assert len(client.session['blockchain_id']) == 8
    assert client.session['miner_num'] == 0

    # after join-operations the client is redirected to the mining page
    assert response.status_code == 302
    assert (response['Location'] == reverse('bcsim:mine'))


def test_home_view_post_request_join_submit_invalid(db, client):
    """
    Submitting a valid post-request to join a block
    when a blockchain with the provided id does not exits

    """
    # client tries to join a blockchain that does not exist
    data = {
        'blockchain_id': 12345678,
        'name': 'Bob',
        'join_bc': 'submit'
    }

    response = client.post(reverse('bcsim:home'), data=data)

    # no session data is createad
    assert 'miner_id' not in client.session
    assert 'blockchain_id' not in client.session

    # client should be returned to home page
    assert response.status_code == 200
    assertTemplateUsed(response, 'bcsim/home.html')

    # The join form contains an appropriate error message
    join_form = response.context['join_form']
    assert 'Der findes ingen blokkæde med dette ID.' in str(join_form)


def test_home_view_post_request_create_submit_valid(db, client):
    """
    Sending a post request to create blockchain to home view should do the following
    1) Creates session data for client
    2) Create a new blockchain
    3) Redirect to mining page
    """
    data = {
        'creator_name': 'Bobby',
        'title': 'bc title',
        'create_bc': 'submit'
    }

    response = client.post(reverse('bcsim:home'), data=data)

    bcs = Blockchain.objects.all()

    # a blockchain with correct title has been created
    assert bcs.count() == 1
    bc = bcs.first()
    bc.title = 'bc title'

    # an initial block has been created
    assert Block.objects.all().count() == 1
    assert Block.objects.all().first().payload == 'Genesis'

    # correct session data is now createad
    assert 'xxx' not in client.session
    assert 'miner_id' in client.session
    assert 'miner_num' in client.session
    assert 'blockchain_id' in client.session
    assert len(client.session['blockchain_id']) == 8
    assert len(client.session['miner_id']) == 8
    assert client.session['blockchain_id'] == bc.id

    # after create-operations the client is redirected to the mining page
    assert response.status_code == 302
    assert (response['Location'] == reverse('bcsim:mine'))


def test_home_view_post_request_create_submit_invalid_no_provided_title(db, client):
    """
    Submitting the create new blockchain with no provided title should do the following
    1) Create no blockchain or session data
    2) Render home page (status code 200)
    """
    data = {
        'title': '',
        'create_bc': 'submit'
    }

    response = client.post(reverse('bcsim:home'), data=data)

    # No blockchain is created
    bcs = Blockchain.objects.all()
    assert bcs.count() == 0

    # no session data is createad
    assert 'miner_id' not in client.session
    assert 'blockchain_id' not in client.session
 
    # client should be returned to home page
    assert response.status_code == 200
    assertTemplateUsed(response, 'bcsim/home.html')


def test_mine_view_exists_and_returns_correct_template(client, db):
    """
    Mine view exists at proper url, returns 200 and seems to have correct content.
    """
    blockchain = BlockChainFactory()
    miner = MinerFactory(blockchain=blockchain)
    block = BlockFactory(blockchain=blockchain, miner=miner)

    session = client.session
    session['blockchain_id'] = block.blockchain.id
    session['miner_id'] = miner.id
    session.save()

    response = client.get(reverse('bcsim:mine'))

    assert response.status_code == 200
    assertTemplateUsed(response, 'bcsim/mine.html')
    assert response.context['miner'] == miner
    assert response.context['blockchain'] == block.blockchain
    assert response.context['blocks'].last() == block
    assert response.context['prev_hash'] == block.hash()


def test_mine_view_if_user_has_no_session(client, db):
    """
    If client has no session, he should be redirected to homepage.
    """
    response = client.get(reverse('bcsim:mine'))
    assert response.status_code == 302
    assert (response['Location'] == reverse('bcsim:home'))


def test_mine_view_calculate_hash_submit_when_proof_is_valid(client, db):
    """
    A logged in client fills out the mining form and presses the 'calculate hash' button.
    The input data gived a valid proof which is reflected in the returned data.
    """
    bc = BlockChainFactory()
    bc.id = "abcdfgh"
    bc.save()
    miner = MinerFactory(blockchain=bc)
    block = BlockFactory(blockchain=bc, miner=miner)
    session = client.session
    session['blockchain_id'] = bc.id
    session['miner_id'] = block.miner.id
    session.save()

    # The user fills out the block form and presses the 'Calculate hash button'
    data = {
        'nonce': 0,
        'calculate_hash': 'submit'
    }
    response = client.post(reverse('bcsim:mine'), data=data)

    # Response code and template content is checked
    assert response.status_code == 200
    assertTemplateUsed(response, 'bcsim/mine.html')
    assert response.context['miner'] == miner
    assert response.context['block_id'] == 1
    assert response.context['blockchain'] == bc
    assert response.context['blocks'].last() == block
    assert response.context['prev_hash'] == block.hash()
    # assert isinstance(response.context['form'], BlockForm)

    expected_cur_hash = hash_context(
        {'block_id': 1,
         'miner': miner,
         'prev_hash': block.hash(),
         'payload': next_payload(miner.blockchain.id, block.id),
         'nonce': 0}
    )

    assert expected_cur_hash == response.context['cur_hash']
    assert expected_cur_hash[0] in ['0','1','2']

    # Since the calculated hash starts with 0,1 or 2 we have a valid proof
    assert response.context['valid_proof'] == True

    # Since we have valid proof, the context should contain nonce and payload
    assert response.context['payload'] == next_payload(miner.blockchain.id, block.id)
    assert response.context['nonce'] == '0'

    # Since the proof is valid, the reponse should contain an 'Add block to chain' button and a 'refresh' button
    assert 'add_to_chain' in str(response.content)
    assert 'refresh' in str(response.content)

    # No new block has been created (there is still only 1 block in the chain)
    assert Block.objects.all().count() == 1

    # The user fills out the block form and presses the 'Calculate hash button'
    data = {
        'nonce': 'test nonce',
        'add_to_chain': 'submit'
    }
    response = client.post(reverse('bcsim:mine'), data=data)

    # ... this will add a new block to the blockchain
    assert Block.objects.all().count() == 2

    # the new block has the correct attributes
    new_b = Block.objects.get(blockchain=bc, block_id=1)
    assert(new_b.payload == next_payload(miner.blockchain.id, block.id))
    assert(new_b.miner_id == miner.id)
    assert(new_b.prev_hash == block.hash())


def test_mine_view_calculate_hash_submit_when_proof_is_not_valid(client, db):
    """
    A logged in client fills out the mining form and presses the 'calculate hash' button.
    The input data does not give valid proof which is reflected in the returned data.
    """
    miner = MinerFactory(blockchain = BlockChainFactory())
    block = BlockFactory(miner=miner, blockchain = miner.blockchain)

    session = client.session
    session['blockchain_id'] = block.blockchain.id
    session['miner_id'] = block.miner.id
    session['miner_num'] = block.miner.miner_num

    session.save()

    assert isinstance(block, Block)
    assert block.block_id == 0

    block_count = Block.objects.filter(blockchain=block.blockchain).count()
    assert block_count == 1

    # The user fills out the block form and presses the 'Calculate hash button'
    data = {
        'nonce': 1234567892,
        'calculate_hash': 'submit'
    }
    response = client.post(reverse('bcsim:mine'), data=data)

    # Response code and template content is checked
    assert response.status_code == 200
    assertTemplateUsed(response, 'bcsim/mine.html')
    assert response.context['miner'] == miner
    assert response.context['block_id'] == 1
    assert response.context['blockchain'] == block.blockchain
    assert response.context['blocks'].last() == block
    assert response.context['prev_hash'] == block.hash()
    assert isinstance(response.context['form'], BlockForm)


    expected_cur_hash = hash_context(
        {'block_id': 1,
         'miner': miner,
         'prev_hash': block.hash(),
         'payload': next_payload(miner.blockchain.id, block.id),
         'nonce': 1234567892})
    assert expected_cur_hash == response.context['cur_hash']

    # Since the calculated hash starts does not start with 0,1 or 2 the proof should not be valid
    assert response.context['valid_proof'] == False

    # Since the proof is valid, the reponse should not contain an 'Add block to chain' button.
    assert 'add_to_chain' not in str(response.content)
    assert 'kassér' not in str(response.content)

    # No new block has been created (there is still only 1 block in the chain)
    assert Block.objects.all().count() == 1


def test_logout_view(client, db):
    """ logout view redirects to home view """
    block = BlockFactory()
    session = client.session
    session['blockchain_id'] = block.blockchain.id
    session['miner_num'] = 3
    session.save()

    response = client.get(reverse('bcsim:logout'))

    assert response.status_code == 302
    assert (response['Location'] == reverse('bcsim:home'))
