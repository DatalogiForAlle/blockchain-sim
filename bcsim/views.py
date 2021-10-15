
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Blockchain, Block
from .forms import CreateBlockchainForm, JoinBlockchainForm, BlockForm
import secrets
import hashlib
import datetime


def home_view(request):

    if request.method == "POST":
        join_form = JoinBlockchainForm(request.POST)
        if join_form.is_valid():
            blockchain = get_object_or_404(
                Blockchain, id=request.POST['blockchain_id'])
            request.session['miner_id'] = secrets.token_hex(3)
            request.session['blockchain_id'] = blockchain.id
            messages.success(request, "You joined this blockchain!")
            return redirect(reverse('bcsim:mine'))

    elif request.method == "GET":

        join_form = JoinBlockchainForm()
        if 'miner_id' in request.session:
            return redirect(reverse('bcsim:mine'))

    context = {
        'create_form': CreateBlockchainForm(),
        'join_form': join_form
    }

    return render(request, 'bcsim/home.html', context)


@require_POST
def create_view(request):
    # better: create block in db and redirect to join.

    form = CreateBlockchainForm(request.POST)
    if form.is_valid():
        # create blockchain
        new_blockchain = form.save()

        # set session variables for client
        request.session['miner_id'] = secrets.token_hex(3)
        request.session['blockchain_id'] = new_blockchain.id

        # create initial block in chain
        Block.objects.create(
            block_num=0,
            blockchain=new_blockchain,
            miner_id="0",
            payload="Genesis",
            nonce="0",
            prev_hash="0",
            created_at=datetime.datetime.now()
        )
        messages.success(request, "You created a new blockchain!")
        return redirect(reverse('bcsim:mine'))


def hash_block(id, miner_id, created, payload, nonce, prev_hash):
    s = f"{id}{miner_id}{created}{payload}{prev_hash}{nonce}"
    return hashlib.sha256(s.encode()).hexdigest()


def mine_view(request):
    if not 'blockchain_id' in request.session:
        return redirect(reverse('bcsim:home'))

    blockchain = get_object_or_404(
        Blockchain, id=request.session['blockchain_id'])

    blocks = Block.objects.filter(
        blockchain=blockchain).order_by('-block_num')

    last_block = blocks.first()
    prev_hash = hash_block(
        last_block.block_num,
        last_block.miner_id,
        last_block.created_at,
        last_block.payload,
        last_block.nonce,
        last_block.prev_hash
    )

    mine_form = BlockForm(initial={
        'block_num': len(blocks),
        'miner_id': request.session['miner_id'],
        'blockchain_id': blockchain.id,
        'prev_hash': prev_hash,
        'created_at': datetime.datetime.now()
    })

    context = {
        'blockchain': blockchain,
        'blocks': blocks,
        'mine_form': mine_form,
    }

    if request.method == "POST":
        """ Block mining attempt """
        mine_form = BlockForm(request.POST)
        if mine_form.is_valid():
            current_hash = hash_block(
                mine_form.cleaned_data['block_num'],
                mine_form.cleaned_data['miner_id'],
                mine_form.cleaned_data['created_at'],
                mine_form.cleaned_data['payload'],
                mine_form.cleaned_data['prev_hash'],
                mine_form.cleaned_data['nonce'],
            )

        if 'calculate_hash' in request.POST:
            if current_hash[0] in list("012"):
                valid_proof = True
            else:
                valid_proof = False

            context['valid_proof'] = valid_proof
            context['current_hash'] = current_hash

        #new_block = form.save(commit=False)

        if 'add_to_chain' in request.POST:
            new_block = mine_form.save(commit=False)
            new_block.blockchain = blockchain
            new_block.save()
            messages.success(
                request, "You created a new blockchain!")
            return redirect(reverse('bcsim:mine'))

    context['mine_form'] = mine_form
    return render(request, 'bcsim/mine.html', context)


@require_GET
def logout_view(request):
    blockchain_id = request.session['blockchain_id']

    del request.session['miner_id']
    del request.session['blockchain_id']

    messages.success(request, f"Du forlod blokkæden med id {blockchain_id}")

    return redirect(reverse('bcsim:home'))
