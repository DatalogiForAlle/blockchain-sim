
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Blockchain, Block
from .forms import BlockchainForm, JoinForm, BlockForm
import secrets
import hashlib
from datetime import datetime

# All session variables
MINER_VARS = ['miner_id', 'blockchain_id']
TIMESTAMP_VARS = ['created_at', 'timestamp']
VALID_PROOF_VARS = ['valid_proof', 'valid_proof_payload', 'valid_proof_nonce',
                    'valid_proof_block_id', 'valid_proof_timestamp']


def del_session_vars(session_vars, request):
    for var in session_vars:
        if var in request.session:
            del request.session[var]


@require_POST
def logout_view(request):
    """ Destroy session variables, and return to home view """
    blockchain_id = request.session['blockchain_id']

    # delete all session variables
    del_session_vars(MINER_VARS)
    del_session_vars(TIMESTAMP_VARS)
    del_session_vars(VALID_PROOF_VARS)

    messages.info(
        request, f"Du forlod blokkæden med ID {blockchain_id}.")

    return redirect(reverse('bcsim:home'))


def home_view(request):
    join_form = JoinForm()
    create_form = BlockchainForm()

    if request.method == "POST":

        if 'join_bc' in request.POST:
            join_form = JoinForm(request.POST)

            if join_form.is_valid():

                # set session variables for client
                request.session['miner_id'] = secrets.token_hex(3)
                request.session['blockchain_id'] = request.POST['blockchain_id']

                messages.success(request, "Du deltagere nu i en blokkæde!")

                # redirect to mining page
                return redirect(reverse('bcsim:mine'))

        elif 'create_bc' in request.POST:
            create_form = BlockchainForm(request.POST)

            if create_form.is_valid():

                # create new blockchain
                new_blockchain = create_form.save()

                # set session variables for client
                miner_id = secrets.token_hex(3)
                request.session['miner_id'] = miner_id
                request.session['blockchain_id'] = new_blockchain.id

                # create initial block in chain
                Block.objects.create(
                    block_id=0,
                    blockchain=new_blockchain,
                    miner_id="0",
                    payload="Genesis",
                    nonce="0",
                    prev_hash="0",
                    created_at=datetime.now()
                )
                messages.success(request, "Du har startet en ny blokkæde!")

                # redirect to mining page
                return redirect(reverse('bcsim:mine'))

    context = {
        'create_form': create_form,
        'join_form': join_form
    }

    return render(request, 'bcsim/home.html', context)


def hash_context(c):
    block = Block(
        block_id=c['block_id'],
        miner_id=c['miner_id'],
        prev_hash=c['prev_hash'],
        created_at=c['created_at'],
        payload=c['payload'],
        nonce=c['nonce'])
    return block.hash()


def mine_view(request):

    if not 'blockchain_id' in request.session:
        return redirect(reverse('bcsim:home'))

    blockchain_id = request.session['blockchain_id']

    if not Blockchain.objects.filter(id=blockchain_id).exists():
        return redirect(reverse('bcsim:logout'))
    else:
        blockchain = Blockchain.objects.get(id=blockchain_id)

    miner_id = request.session['miner_id']
    blocks = Block.objects.filter(
        blockchain=blockchain).order_by('-block_id')
    last_block = blocks.first()
    assert last_block.block_id == len(
        blocks) - 1, f'block-id {last_block.block_id} does not equal len(blocks) - 1 = {len(blocks)} -1'

    prev_hash = last_block.hash()
    block_id = len(blocks)

    if not 'timestamp' in request.session:
        created_at = datetime.now()
        timestamp = datetime.timestamp(created_at)
        request.session['created_at'] = created_at
        request.session['timestamp'] = timestamp

    else:
        created_at = request.session['created_at']
        timestamp = request.session['timestamp']

    context = {
        'blocks': blocks,
        'blockchain_id': blockchain_id,
        'blockchain_title': blockchain.title,

        'block_id': block_id,
        'miner_id': miner_id,
        'created_at': created_at,
        'prev_hash': prev_hash,
    }

    form = BlockForm()

    if request.method == "POST":

        if 'refresh' in request.POST:
            del_session_vars(VALID_PROOF_VARS, request)
            del_session_vars(TIMESTAMP_VARS, request)
            return redirect(reverse('bcsim:mine'))

        if 'calculate_hash' in request.POST:

            form = BlockForm(request.POST)

            if form.is_valid():
                payload = form.cleaned_data['payload']
                nonce = form.cleaned_data['nonce']

                context['payload'] = form.cleaned_data['payload']
                context['nonce'] = form.cleaned_data['nonce']

                cur_hash = hash_context(context)

                context['cur_hash'] = cur_hash

                if cur_hash[0] in list("012"):
                    context['valid_proof'] = True
                    request.session['valid_proof'] = True
                    request.session['valid_proof_block_id'] = block_id
                    request.session['valid_proof_timestamp'] = timestamp
                    request.session['valid_proof_payload'] = payload
                    request.session['valid_proof_nonce'] = nonce

                else:
                    context['valid_proof'] = False

        if 'add_to_chain' in request.POST and request.session['valid_proof']:

            # Check if a new block has been added to chain since the valid hash was created
            if block_id != request.session['valid_proof_block_id']:
                messages.error(
                    request, f"En anden minearbejder tilføjede blok #{request.session['valid_proof_block_id']} før dig!")
                del_session_vars(VALID_PROOF_VARS, request)
                del_session_vars(TIMESTAMP_VARS, request)
                return redirect(reverse('bcsim:mine'))

            new_block = Block(
                block_id=block_id,
                miner_id=miner_id,
                prev_hash=prev_hash,
                created_at=datetime.fromtimestamp(
                    request.session['valid_proof_timestamp']),
                payload=request.session['valid_proof_payload'],
                nonce=request.session['valid_proof_nonce'],
                blockchain_id=blockchain_id
            )

            assert new_block.hash()[0] in list(
                "012"), f"Invalid block caught before saving to database: {new_block.hash()}"
            assert new_block.prev_hash == last_block.hash(
            ), f"Prev_hash of new block does not match hash of last block. Error caught before saving to db."

            new_block.save()

            messages.success(
                request, "Du har tilføjet en blok til kæden!")

            del_session_vars(VALID_PROOF_VARS, request)
            del_session_vars(TIMESTAMP_VARS, request)

            return redirect(reverse('bcsim:mine'))

    context['form'] = form

    return render(request, 'bcsim/mine.html', context)


@ require_GET
def block_list_view_htmx(request):
    if not 'blockchain_id' in request.session:
        return redirect(reverse('bcsim:home'))

    blockchain_id = request.session['blockchain_id']

    if not Blockchain.objects.filter(id=blockchain_id).exists():
        return redirect(reverse('bcsim:logout'))
    else:
        blockchain = Blockchain.objects.get(id=blockchain_id)

    blocks = Block.objects.filter(
        blockchain=blockchain).order_by('-block_id')

    return render(request, 'bcsim/block_list.html', {'blocks': blocks})
