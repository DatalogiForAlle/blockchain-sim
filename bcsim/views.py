
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Blockchain, Block, Miner
from .forms import BlockchainForm, JoinForm, BlockForm, LoginForm
import secrets

# All session variables
MINER_VARS = ['miner_id', 'miner_num', 'blockchain_id']
VALID_PROOF_VARS = ['valid_proof', 'valid_proof_payload', 'valid_proof_nonce',
                    'valid_proof_block_id']



def next_payload(blockchain_id, block_id):


    first_names = ('John', 'Andy', 'Joe', 'Sandy', 'Sally',
               'Alice', 'Joanna', 'Serena', 'Oliver', 'Steven')
    
    last_names = ('Johnson', 'Smith', 'Williams', 'Brown',
              'Silbersmith', 'Garcia', 'Miller', 'Davis', 'Jones', 'Lopez')
        
    random.seed(blockchain_id + str(block_id))

    sender = f"{random.choice(first_names)} {random.choice(last_names)}"
    recipient = f"{random.choice(first_names)} {random.choice(last_names)}"

    amount = random.randint(1, 100)

    return f"{amount} diku-dollars fra {sender} til {recipient}"

def del_session_vars(session_vars, request):
    for var in session_vars:
        if var in request.session:
            del request.session[var]


@require_GET
def invite_view(request):
    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
    except:
        # if client does not have a session, return to home:
        return redirect(reverse('bcsim:home'))
    else:
        context = {'blockchain': miner.blockchain, 'miner': miner}
        return render(request, 'bcsim/invite.html', context)


@require_GET
def participants_view(request):
    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
    except:
        # if client does not have a session, return to home:
        return redirect(reverse('bcsim:home'))
    else:
        miners = Miner.objects.filter(blockchain=miner.blockchain).order_by('-balance')
        context = {'miners': miners, 'blockchain': miner.blockchain, 'client':miner}
        return render(request, 'bcsim/participants.html', context)

    
@require_GET
def logout_view(request):
    """ Destroy session variables, and return to home view """
    blockchain_id = request.session['blockchain_id']
    miner_id = request.session['miner_id']

    # delete all session variables
    del_session_vars(MINER_VARS, request)
    del_session_vars(VALID_PROOF_VARS, request)

    messages.info(
        request, f"Du forlod blokkæden med ID {blockchain_id}. Dit minearbejder-ID var {miner_id}.")

    return redirect(reverse('bcsim:home'))


def home_view(request):
    join_form = JoinForm()

    create_form = BlockchainForm()

    login_form = LoginForm()

    expand = 'none'

    if request.method == 'GET':

        initial = {}
        if 'blockchain_id' in request.GET:
            initial['blockchain_id'] = request.GET['blockchain_id']
        if 'miner_id' in request.GET:
            initial['miner_id'] = request.GET['miner_id']
        join_form = JoinForm(initial=initial)
        login_form = LoginForm(initial=initial)

    if request.method == "POST":

        if 'join_bc' in request.POST:
            
            expand = 'second'

            join_form = JoinForm(request.POST)

            if join_form.is_valid():

                blockchain = Blockchain.objects.get(
                    id=join_form.cleaned_data['blockchain_id']
                )
                new_miner = join_form.save(commit=False)
                new_miner.blockchain = blockchain
                new_miner.miner_num = Miner.objects.filter(blockchain=blockchain).count()
                new_miner.save()

                # set session variables for client
                request.session['miner_id'] = new_miner.id
                request.session['miner_num'] = new_miner.miner_num
                request.session['blockchain_id'] = request.POST['blockchain_id']

                messages.success(request, "Du deltager nu i en blokkæde!")

                # redirect to mining page
                return redirect(reverse('bcsim:mine'))
            


        elif 'create_bc' in request.POST:
            expand = 'first'

            create_form = BlockchainForm(request.POST)

            if create_form.is_valid():

                # create new blockchain
                new_blockchain = create_form.save()

                # create miner
                creator = Miner.objects.create(name=create_form.cleaned_data['creator_name'], blockchain=new_blockchain, miner_num=0, creator=True)
                request.session['miner_id'] = creator.id
                request.session['miner_num'] = creator.miner_num
                request.session['blockchain_id'] = new_blockchain.id

                # create initial block in chain
                Block.objects.create(
                    block_id=0,
                    blockchain=new_blockchain,
                    miner = creator,
                    payload="Genesis",
                    nonce="0",
                    prev_hash="0",
                )
                messages.success(request, f"Du har startet en ny blokkæde!")
 
                # redirect to mining page
                return redirect(reverse('bcsim:mine'))
        
        elif 'login' in request.POST:
            expand = 'third'

            login_form = LoginForm(request.POST)

            if login_form.is_valid():
                blockchain = Blockchain.objects.get(
                    id=login_form.cleaned_data['blockchain_id']
                )
                miner = Miner.objects.get(
                    id=login_form.cleaned_data['miner_id']
                )

                # set session variables for client
                request.session['miner_id'] = miner.id
                request.session['miner_num'] = miner.miner_num
                request.session['blockchain_id'] = request.POST['blockchain_id']

                messages.success(request, "Du deltager nu i en blokkæde!")

                # redirect to mining page
                return redirect(reverse('bcsim:mine'))
    
    
    context = {
        'create_form': create_form,
        'join_form': join_form,
        'login_form': login_form
    }

    if 'miner_id' in request.session:
        miner = Miner.objects.get(id=request.session['miner_id'])
        context['miner'] = miner

    context['expand'] = expand

    if 'miner_id' in request.GET:
       context['expand'] = 'third'

    elif 'blockchain_id' in request.GET:
       context['expand'] = 'second'

    return render(request, 'bcsim/home.html', context)


def hash_context(context):
    block = Block(
        block_id=context['block_id'],
        miner=context['miner'],
        prev_hash=context['prev_hash'],
        payload=context['payload'],
        nonce=context['nonce']
    )
    return block.hash()


def mine_view(request):
    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
    except:
        # if client does not have a session, return to home:
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
        payload = next_payload(blockchain.id, block_id)
        context = {
            'blocks': blocks,
            'blockchain': blockchain,
            'block_id': block_id,
            'miner': miner,
            'prev_hash': prev_hash,
            'payload': payload
        }

        form = BlockForm()

        if request.method == "POST":

            if 'refresh' in request.POST:
                del_session_vars(VALID_PROOF_VARS, request)
                return redirect(reverse('bcsim:mine'))

            if 'calculate_hash' in request.POST:

                form = BlockForm(request.POST)

                if form.is_valid():
                    print("DIFFICULTY", blockchain.difficulty)
                    print("LEVEL.MEDIUM", Blockchain.Level.MEDIUM)

                    nonce = form.cleaned_data['nonce']
                    context['nonce'] = nonce

                    cur_hash = hash_context(context)
                    context['cur_hash'] = cur_hash

                    easy_valid = blockchain.difficulty = Blockchain.Level.NEM and cur_hash[0] in list("012")
                    print("easy_valid", easy_valid)

                    medium_valid = blockchain.difficulty = Blockchain.Level.MEDIUM and cur_hash[0] == "0"
                    print("medium_valid", medium_valid)

                    hard_valid = blockchain.difficulty = Blockchain.Level.SVÆR and cur_hash[0:2] == "00"
                    print("har_valid", hard_valid)
                    valid_proof = easy_valid or medium_valid or hard_valid
                    
                    if valid_proof:

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
                    blockchain=blockchain,
                    miner=miner,
                    prev_hash=prev_hash,
                    payload=request.session['valid_proof_payload'],
                    nonce=request.session['valid_proof_nonce'],
                )
                print("DIFFICULTY", blockchain.difficulty)
                print("LEVEL.NEM", Blockchain.Level.NEM)

                if blockchain.difficulty == Blockchain.Level.NEM:
                    assert new_block.hash()[0] in list(
                        "012"), f"Invalid    block caught before saving to database: {new_block.hash()}"
                if blockchain.difficulty == Blockchain.Level.MEDIUM:
                    print("HEJ", new_block.hash()[0])
                    assert new_block.hash()[0] == "0", f"Invalid block caught before saving to database: {new_block.hash()}"
                if blockchain.difficulty == Blockchain.Level.SVÆR:
                    assert new_block.hash()[0:2][
                        0] == "00", f"Invalid block caught before saving to database: {new_block.hash()}"

                assert new_block.prev_hash == last_block.hash(
                ), f"Prev_hash of new block does not match hash of last block. Error caught before saving to db."

                new_block.save()

                # miner reward
                miner.balance += 100
                miner.save()

                messages.success(
                    request, "Du har tilføjet en blok til kæden!")

                del_session_vars(VALID_PROOF_VARS, request)

                return redirect(reverse('bcsim:mine'))

        context['form'] = form

        return render(request, 'bcsim/mine.html', context)


@require_GET
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
