import time

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.http import HttpResponse

from .models import Blockchain, Block, Miner, Token, Transaction
from .forms import (BlockchainForm, JoinForm, BlockForm,
                    LoginForm, TokenPriceForm)
from .decorators import require_miner_id_is_in_session


def del_session_vars(session_vars, request):
    for var in session_vars:
        if var in request.session:
            del request.session[var]


@require_POST
@require_miner_id_is_in_session
def buy_token_view(request):

    miner_id = request.session['miner_id']
    miner = get_object_or_404(Miner, pk=miner_id)

    token_id = int(request.POST['token_id'])
    token = get_object_or_404(
        Token, pk=token_id)

    if miner.has_trade_in_process_as_buyer():
        mgs = (
            f"Du har allerede et køb i køen."
        )
        messages.info(request, mgs)

        return redirect(reverse('bcsim:market'))


    if not miner.can_buy_token(token):
        mgs = (
            f"Du kan ikke købe dette token"
        )
        messages.info(request, mgs)

        return redirect(reverse('bcsim:market'))

    seller_id = request.POST['seller_id']
    seller = get_object_or_404(Miner, pk=seller_id)

    Transaction.objects.create(
        blockchain=miner.blockchain,
        buyer=miner,
        seller=seller,
        token=token,
        amount=token.price,
        processed=False)
    
    if seller == miner.blockchain.get_bank():
        miner.blockchain.add_token_to_bank()

    token.transaction_in_process = True
    token.save() 

    return redirect(reverse('bcsim:market'))


@require_miner_id_is_in_session
def market_view(request):
    miner_id = request.session['miner_id']
    miner = get_object_or_404(Miner, pk=miner_id)

    tokens = Token.objects.filter(
        blockchain=miner.blockchain).order_by('-price')
    token_price_forms = {str(token.id): TokenPriceForm() for token in tokens}

    if request.method == 'POST':
        token_price_form = TokenPriceForm(request.POST)
        token_id = int(request.POST['token_id'])
        token = get_object_or_404(
            Token, pk=token_id)
        token_price_forms[str(token.id)] = token_price_form
        if token_price_form.is_valid():
            if token.price:
                # Price is already set, so we redirect
                return redirect(reverse('bcsim:market'))
            elif token.owner != miner:
                # Only the owner of a token should be able to set the price
                return redirect(reverse('bcsim:market'))

            token_price = token_price_form.cleaned_data['price']
            token.price = token_price
            token.save()
            return redirect(reverse('bcsim:market'))

    context = {
        'tokens': tokens,
        'miner': miner,
        'blockchain': miner.blockchain,
        'forms': token_price_forms
    }

    return render(request, 'bcsim/market.html', context)


@require_GET
@require_miner_id_is_in_session
def invite_view(request):
    miner_id = request.session['miner_id']
    miner = get_object_or_404(Miner, pk=miner_id)

    context = {'blockchain': miner.blockchain, 'miner': miner}
    return render(request, 'bcsim/invite.html', context)


@require_GET
@require_miner_id_is_in_session
def participants_view(request):
    miner_id = request.session['miner_id']
    miner = get_object_or_404(Miner, pk=miner_id)
    miners = Miner.objects.filter(
        blockchain=miner.blockchain)
    
    context = {'miners': miners,
               'blockchain': miner.blockchain, 'client': miner}
    return render(request, 'bcsim/participants.html', context)


@require_GET
@require_miner_id_is_in_session
def logout_view(request):
    """ Destroy session variables, and return to home view """
    blockchain_id = request.session['blockchain_id']
    miner_id = request.session['miner_id']

    # delete all session variables
    all_session_vars = ['miner_id', 'blockchain_id']
    del_session_vars(all_session_vars, request)

    mgs = (
        f"Du forlod blockchainen med ID={blockchain_id}. "
        f"Dit minearbejder-ID var {miner_id}."
    )
    messages.info(request, mgs)

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
                new_miner.save()

                # Create initial transactions for miner
                if blockchain.has_tokens():
                    blockchain.create_initial_transactions(new_miner)

                # Set session variables for client
                request.session['miner_id'] = new_miner.id
                request.session['blockchain_id'] = request.POST[
                    'blockchain_id']

                messages.success(request, "Du deltager nu i en blockchain!")

                # redirect to mining page
                return redirect(reverse('bcsim:mine'))

        elif 'create_bc' in request.POST:
            expand = 'first'

            create_form = BlockchainForm(request.POST)

            if create_form.is_valid():

                # create new blockchain
                new_blockchain = create_form.save()

                # create creator (miner)
                creator = Miner.objects.create(
                    name=create_form.cleaned_data['creator_name'],
                    blockchain=new_blockchain,
                    is_creator=True)
                request.session['miner_id'] = creator.id
                request.session['blockchain_id'] = new_blockchain.id

                if new_blockchain.has_tokens():
                    # create NTF-bank (miner)
                    nft_bank = Miner.objects.create(
                        name='NFT-bank',
                        blockchain=new_blockchain,
                        miner_num=Miner.objects.filter(
                            blockchain=new_blockchain).count(),
                        is_creator=False)

                    # Add initial tokens to NFT-bank
                    new_blockchain.add_token_to_bank(number_of_tokens_to_add=Blockchain.NUM_TOKENS_FOR_SALE_IN_BANK)
  
                # create initial block in chain
                Block.objects.create(
                    block_num=0,
                    blockchain=new_blockchain,
                    miner=creator,
                    nonce="0",
                    prev_hash="0"
                )
                messages.success(request, f"Du har startet en ny blockchain!")

                # Create initial transactions for creator
                if new_blockchain.has_tokens():
                    new_blockchain.create_initial_transactions(creator)
 
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
@require_miner_id_is_in_session
def toggle_pause_view(request):
    miner_id = request.session['miner_id']
    miner = get_object_or_404(Miner, pk=miner_id)

    if not miner.is_creator:
        return redirect(reverse('bcsim:home'))

    miner.blockchain.toggle_pause()
    return redirect(reverse('bcsim:mine'))


@require_miner_id_is_in_session
def mine_view(request):
    miner_id = request.session['miner_id']
    miner = get_object_or_404(Miner, pk=miner_id)

    blockchain = miner.blockchain
    blocks = Block.objects.filter(
        blockchain=blockchain).order_by('-block_num')
    last_block = blocks.first()
    current_block_num = len(blocks)
    form = BlockForm()
    hash = None

    if blockchain.has_tokens():
        unprocessed_transactions = Transaction.objects.filter(
            blockchain=blockchain, processed=False)
        if unprocessed_transactions.count() == 0:
            next_transaction = None
        else:
            next_transaction = unprocessed_transactions.first()
    else:
        unprocessed_transactions = None
        next_transaction = None

    potential_next_block = Block(
        block_num=current_block_num,
        blockchain=blockchain,
        miner=miner,
        prev_hash=last_block.hash(),
        nonce=None,
        transaction=next_transaction
    )

    if request.method == "POST":

        if blockchain.is_paused:
            return redirect(reverse('bcsim:mine'))

        if blockchain.has_tokens():
            if next_transaction is None:
                messages.error(
                    request, f"Der er ingen transaktioner at mine!")
                return redirect(reverse('bcsim:mine'))

        form = BlockForm(request.POST)

        if form.is_valid():
            if miner.missed_last_block():
                messages.error(
                    request,
                    f"En anden minearbejder tilføjede blok #{miner.number_of_last_block_seen} før dig!")
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
                        request,
                        f"Fejl: Nonce {nonce} ikke gyldigt proof-of-work for blok #{current_block_num}")
                else:
                    if not blockchain.has_tokens():
                        potential_next_block.save()
                        miner.add_miner_reward()
                        messages.success(
                            request, f"Du har tilføjet blok #{current_block_num} til blockchainen!")

                    elif blockchain.has_tokens():
                        transaction_is_valid, error_message = next_transaction.process(
                            miner)
                        if transaction_is_valid:
                            unprocessed_transactions = Transaction.objects.filter(
                                blockchain=blockchain, processed=False)
                            potential_next_block.save()

                            messages.success(
                                request, f"Du har tilføjet blok #{current_block_num} til blockchainen!")
                        else:
                            messages.info(
                                request, f"Transaktionen er ugyldig!: {error_message}")

                    return redirect(reverse('bcsim:mine'))

    context = {
        'blocks': blocks,
        'blockchain': blockchain,
        'miner': miner,
        'form': form,
        'cur_hash': hash,
        'next_block': potential_next_block,
        'unprocessed_transactions': unprocessed_transactions
    }

    if miner.number_of_last_block_seen < current_block_num:
        miner.number_of_last_block_seen = current_block_num
        miner.save()

    return render(request, 'bcsim/mine.html', context)


@require_GET
def block_list_view_htmx(request):

    try:
        blockchain_id = request.session['blockchain_id']
        blockchain = Blockchain.objects.get(pk=blockchain_id)
    except BaseException:
        return HttpResponse("Error: Client does not belong to blockchain")
    else:
        blocks = Block.objects.filter(
            blockchain=blockchain).order_by('-block_num')
        return render(request, 'bcsim/block_list.html',
                      {'blocks': blocks, 'blockchain': blockchain})
