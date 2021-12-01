
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Blockchain, Block, Miner
from .forms import BlockchainForm, JoinForm, BlockForm
import secrets

# All session variables
MINER_VARS = ['miner_id', 'blockchain_id']
VALID_PROOF_VARS = ['valid_proof', 'valid_proof_payload', 'valid_proof_nonce',
                    'valid_proof_block_id']


def del_session_vars(session_vars, request):
    for var in session_vars:
        if var in request.session:
            del request.session[var]


@require_POST
def logout_view(request):
    """ Destroy session variables, and return to home view """
    blockchain_id = request.session['blockchain_id']

    # delete all session variables
    del_session_vars(MINER_VARS, request)
    del_session_vars(VALID_PROOF_VARS, request)

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

                blockchain = Blockchain.objects.get(
                    id=join_form.cleaned_data['blockchain_id']
                )
                new_miner = join_form.save(commit=False)
                new_miner.blockchain = blockchain
                new_miner.save()

                # set session variables for client
                request.session['miner_id'] = new_miner.id
                request.session['blockchain_id'] = request.POST['blockchain_id']

                messages.success(request, "Du deltagere nu i en blokkæde!")

                # redirect to mining page
                return redirect(reverse('bcsim:mine'))

        elif 'create_bc' in request.POST:
            create_form = BlockchainForm(request.POST)

            if create_form.is_valid():

                # create new blockchain
                new_blockchain = create_form.save()
                
                # create miner
                creator = Miner.objects.create(name=create_form.cleaned_data['creator_name'], blockchain=new_blockchain)
                request.session['miner_id'] = creator.id
                request.session['blockchain_id'] = new_blockchain.id

                # create initial block in chain
                Block.objects.create(
                    block_id=0,
                    blockchain=new_blockchain,
                    miner_id="0",
                    payload="Genesis",
                    nonce="0",
                    prev_hash="0",
                )
                messages.success(request, f"Du har startet en ny blokkæde!")
 
                # redirect to mining page
                return redirect(reverse('bcsim:mine'))

    
    context = {
        'create_form': create_form,
        'join_form': join_form
    }

    if 'blockchain_id' in request.session:
        context['blockchain_id'] = request.session['blockchain_id']

    return render(request, 'bcsim/home.html', context)


def hash_context(c):
    block = Block(
        block_id=c['block_id'],
        miner_id=c['miner_id'],
        prev_hash=c['prev_hash'],
        payload=c['payload'],
        nonce=c['nonce'])
    return block.hash()


def mine_view(request):
    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
        print("miner", miner.id)
    except:
        # if miner is not in session, return to home:
        return redirect(reverse('bcsim:home'))
    else:
        blockchain = miner.blockchain
        blocks = Block.objects.filter(
            blockchain=blockchain).order_by('-block_id')
        last_block = blocks.first()
        assert last_block.block_id == len(
            blocks) - 1, f'block-id {last_block.block_id} does not equal len(blocks) - 1 = {len(blocks)} -1'

        prev_hash = last_block.hash()
        block_id = len(blocks)
        context = {
            'blocks': blocks,
            'blockchain': blockchain,
            'block_id': block_id,
            'miner': miner,
            'prev_hash': prev_hash,

        }

        form = BlockForm()

        if request.method == "POST":

            if 'refresh' in request.POST:
                del_session_vars(VALID_PROOF_VARS, request)
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
                    return redirect(reverse('bcsim:mine'))

                new_block = Block(
                    block_id=block_id,
                    miner_id=miner_id,
                    prev_hash=prev_hash,
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
