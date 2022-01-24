
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Blockchain, Block, Miner
from .forms import BlockchainForm, JoinForm, BlockForm, LoginForm
from django.contrib import messages
import time

def next_payload(blockchain_id, current_block_num):

    first_names = ('John', 'Andy', 'Joe', 'Sandy', 'Sally',
               'Alice', 'Joanna', 'Serena', 'Oliver', 'Steven')
    
    last_names = ('Johnson', 'Smith', 'Williams', 'Brown',
              'Silbersmith', 'Garcia', 'Miller', 'Davis', 'Jones', 'Lopez')
        
    random.seed(blockchain_id + str(current_block_num))

    sender = f"{random.choice(first_names)} {random.choice(last_names)}"
    recipient = f"{random.choice(first_names)} {random.choice(last_names)}"

    amount = random.randint(1, 100)

    return f"{amount} DIKU-coins fra {sender} til {recipient}"

def del_session_vars(session_vars, request):
    for var in session_vars:
        if var in request.session:
            del request.session[var]

def market(request):
    context = {'svg': 'svg as string'}
    return render(request, 'bcsim/market.html', context)

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
    all_session_vars = ['miner_id', 'miner_num', 'blockchain_id'] + ['last_block_num_shown_to_client']
    del_session_vars(all_session_vars,request) 

    messages.info(
        request, f"Du forlod blockchainen med ID={blockchain_id}. Dit minearbejder-ID var {miner_id}.")

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

                messages.success(request, "Du deltager nu i en blockchain!")

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
                    block_num=0,
                    blockchain=new_blockchain,
                    miner = creator,
                    payload="Genesis",
                    nonce="0",
                    prev_hash="0",
                )
                messages.success(request, f"Du har startet en ny blockchain!")
 
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

                messages.success(request, "Du deltager nu i en blockchain!")

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


def mine_view(request):

    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
    except:
        # if client does not have a session, return to home:
        return redirect(reverse('bcsim:home'))
    else:
        blockchain = miner.blockchain
        blocks = Block.objects.filter(
            blockchain=blockchain).order_by('-block_num')
        last_block = blocks.first()        
        prev_hash = last_block.hash()
        current_block_num = len(blocks)
        payload = next_payload(blockchain.id, current_block_num)
        context = {
            'blocks': blocks,
            'blockchain': blockchain,
            'block_num': current_block_num,
            'miner': miner,
            'prev_hash': prev_hash,
            'payload': payload
        }
        form = BlockForm()

        if request.method == "POST":

            if 'pause_blockchain' in request.POST:
                blockchain.paused = True
                blockchain.save()
                return redirect(reverse('bcsim:mine'))

            if 'un_pause_blockchain' in request.POST:
                blockchain.paused = False
                blockchain.save()
                return redirect(reverse('bcsim:mine'))
            
            if not blockchain.paused:
                    
                last_block_num_shown_to_client = request.session['last_block_num_shown_to_client']
                form = BlockForm(request.POST)
                if form.is_valid():     
                    
                    # Check if a new block has been added to chain since the valid hash was created
                    if current_block_num != last_block_num_shown_to_client:
                        messages.error(
                            request, f"En anden minearbejder tilføjede blok #{last_block_num_shown_to_client} før dig!")
                        return redirect(reverse('bcsim:mine'))
                    
                    nonce = form.cleaned_data['nonce']

                    new_block = Block(
                        block_num=current_block_num,
                        blockchain=blockchain,
                        miner=miner,
                        prev_hash=prev_hash,
                        payload=payload,
                        nonce=nonce,
                    )

                    context['nonce'] = nonce

                    hash, hash_is_valid = new_block.hash_is_valid()
                    context['cur_hash'] = hash

                    if 'add_to_chain' in request.POST:

                        if not hash_is_valid:    
                            messages.error(
                                request, f"Fejl: Nonce {nonce} ikke gyldigt proof-of-work for blok #{current_block_num}")
                        else:

                            time.sleep(2)
                            
                            new_block.save()    

                            # miner reward
                            miner.balance += 100
                            miner.save()

                            messages.success(
                                request, f"Du har tilføjet blok #{current_block_num} til blockchainen!")

                            del_session_vars(
                                ['last_block_num_shown_to_client'], request)

                            return redirect(reverse('bcsim:mine'))

        context['form'] = form

        request.session['last_block_num_shown_to_client'] = current_block_num
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
        blockchain=blockchain).order_by('-block_num')

    return render(request, 'bcsim/block_list.html', {'blocks': blocks})
