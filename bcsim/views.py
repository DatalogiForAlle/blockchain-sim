
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Blockchain, Block, Miner, Token
from .forms import BlockchainForm, JoinForm, BlockForm, LoginForm
from django.contrib import messages
import time
from .animal_avatar.animal_avatar import Avatar


def del_session_vars(session_vars, request):
    for var in session_vars:
        if var in request.session:
            del request.session[var]

def market(request):
    
    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
    except:
        return redirect(reverse('bcsim:home'))
    else:
        
        tokens = []
        
        for token in Token.objects.filter():
            avatar = Avatar(token.seed)
            svg = avatar.create_avatar()
            tokens.append({'owner':token.owner, 'svg':svg, 'seed':token.seed, 'price':token.price})

        context = {
            'tokens': tokens,
            'miner': miner
        }

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
    all_session_vars = ['miner_id', 'blockchain_id'] 
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
                creator = Miner.objects.create(name=create_form.cleaned_data['creator_name'], blockchain=new_blockchain, miner_num=0, is_creator=True)
                request.session['miner_id'] = creator.id
                request.session['blockchain_id'] = new_blockchain.id

                # create initial block in chain
                Block.objects.create(
                    block_num=0,
                    blockchain=new_blockchain,
                    miner = creator,
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
        context['blockchain'] = miner.blockchain

    context['expand'] = expand

    if 'miner_id' in request.GET:
       context['expand'] = 'third'

    elif 'blockchain_id' in request.GET:
       context['expand'] = 'second'

    return render(request, 'bcsim/home.html', context)

@require_POST
def toggle_pause(request):
    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
    except:
        return redirect(reverse('bcsim:home'))

    if not miner.is_creator:
        return redirect(reverse('bcsim:home'))

    miner.blockchain.toggle_pause()
    return redirect(reverse('bcsim:mine'))


def mine_view(request):
    try:
        miner = Miner.objects.get(id=request.session['miner_id'])
    except:
        return redirect(reverse('bcsim:home'))
    else:
        blockchain = miner.blockchain
        blocks = Block.objects.filter(
            blockchain=blockchain).order_by('-block_num')
        last_block = blocks.first()        
        current_block_num = len(blocks)
        form = BlockForm()
        hash = None

        potential_next_block = Block(
            block_num=current_block_num,
            blockchain=blockchain,
            miner=miner,
            prev_hash=last_block.hash(),
            nonce=None
        )


        if request.method == "POST":
            
            if blockchain.is_paused:
                return redirect(reverse('bcsim:mine'))
                   
            form = BlockForm(request.POST)
            if form.is_valid():     
                
                if miner.missed_last_block():
                    messages.error(
                        request, f"En anden minearbejder tilføjede blok #{miner.number_of_last_block_seen} før dig!")
                    return redirect(reverse('bcsim:mine'))
                nonce = form.cleaned_data['nonce']
                potential_next_block.nonce = nonce

                hash, hash_is_valid = potential_next_block.hash_is_valid()

                if 'add_to_chain' in request.POST:
                    
                    # We want miners to check hashes before trying to add blocks to chain.
                    # Therefore we make a little time delay here
                    time_delay_in_seconds = 2
                    time.sleep(time_delay_in_seconds)
                    
                    if not hash_is_valid:    
                        messages.error(
                            request, f"Fejl: Nonce {nonce} ikke gyldigt proof-of-work for blok #{current_block_num}")
                    else:    
                        potential_next_block.save()    
                        miner.add_miner_reward()
                        messages.success(
                            request, f"Du har tilføjet blok #{current_block_num} til blockchainen!")

                        return redirect(reverse('bcsim:mine'))

        context = {
            'blocks': blocks,
            'blockchain': blockchain,
            'miner': miner,
            'form':form,
            'cur_hash': hash,
            'next_block': potential_next_block
        }
        
        if miner.number_of_last_block_seen < current_block_num:
            miner.number_of_last_block_seen = current_block_num
            miner.save()

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
