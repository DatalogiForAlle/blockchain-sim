
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Blockchain, Block
from .forms import BlockchainForm, JoinForm, BlockForm
import secrets
import hashlib
#import datetime


def home_view(request):
    join_form = JoinForm()
    create_form = BlockchainForm()

    if request.method == "GET":
        if 'blockchain_id' in request.session:
            return redirect(reverse('bcsim:mine'))

    elif request.method == "POST":

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
                    miner_id=miner_id,
                    payload="Genesis",
                    nonce="0",
                    prev_hash="0",
                    # created_at=datetime.datetime.now()
                )
                messages.success(request, "Du har startet en ny blokkæde!")

                # redirect to mining page
                return redirect(reverse('bcsim:mine'))

    context = {
        'create_form': create_form,
        'join_form': join_form
    }

    return render(request, 'bcsim/home.html', context)


def hash_block(block):
    b = block
    if type(b) == dict:
        s = f"{b['block_id']}{b['miner_id']}{b['prev_hash']}{b['payload']}{b['nonce']}"
    else:
        s = f"{b.block_id}{b.miner_id}{b.prev_hash}{b.payload}{b.nonce}"
    return hashlib.sha256(s.encode()).hexdigest()


def mine_view(request):

    if not 'blockchain_id' in request.session:
        return redirect(reverse('bcsim:home'))

    blockchain_id = request.session['blockchain_id']

    if not Blockchain.objects.filter(id=blockchain_id).exists():
        print("HEY")
        return redirect(reverse('bcsim:logout'))
    else:
        blockchain = Blockchain.objects.get(id=blockchain_id)

    miner_id = request.session['miner_id']
    blocks = Block.objects.filter(
        blockchain=blockchain).order_by('-block_id')
    last_block = blocks.first()
    prev_hash = hash_block(last_block)
    block_id = len(blocks)

    form = BlockForm()

    context = {
        'block_id': block_id,
        'miner_id': miner_id,
        'prev_hash': prev_hash,
        'blocks': blocks,
        'blockchain_id': blockchain_id,
        'blockchain_title': blockchain.title,
    }

    if request.method == "POST":

        if 'calculate_hash' in request.POST:
            form = BlockForm(request.POST)
            if form.is_valid():
                context['payload'] = form.cleaned_data['payload']
                context['nonce'] = form.cleaned_data['nonce']

                cur_hash = hash_block(context)

                if cur_hash[0] in list("012"):
                    valid_proof = True
                    request.session['valid_proof'] = True
                    request.session['payload'] = request.POST['payload']
                    request.session['nonce'] = request.POST['nonce']
                    request.session['prev_hash'] = prev_hash
                    request.session['block_id'] = block_id

                else:
                    valid_proof = False
                    request.session['valid_proof'] = False

                context['cur_hash'] = cur_hash
                context['valid_proof'] = valid_proof

        if 'add_to_chain' in request.POST and request.session['valid_proof']:
            Block.objects.create(
                block_id=request.session['block_id'],
                miner_id=miner_id,
                prev_hash=request.session['prev_hash'],
                payload=request.session['payload'],
                nonce=request.session['nonce'],
                blockchain_id=blockchain_id
            )
            messages.success(
                request, "Du har tilføjet en blok til kæden!")
            return redirect(reverse('bcsim:mine'))

    context['form'] = form

    return render(request, 'bcsim/mine.html', context)


@require_POST
def logout_view(request):
    blockchain_id = request.session['blockchain_id']

    for var in ['blockchain_id', 'miner_id', 'valid_proof', 'nonce', 'payload']:
        if var in request.session:
            del request.session[var]

    messages.success(
        request, f"Du forlod blokkæden med ID'et {blockchain_id}.")

    return redirect(reverse('bcsim:home'))
