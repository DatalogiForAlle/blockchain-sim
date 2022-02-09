import functools
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from .models import Miner

def require_miner_id_is_in_session(func):
    """
    Make sure  miner_id is in request.session before proceeding
    """
    @functools.wraps(func)
    def wrapper_login_required(request, *args, **kwargs):
        if not 'miner_id' in request.session:
            return redirect(reverse('bcsim:home'))
        return func(request, *args, **kwargs)
    return wrapper_login_required


def require_blockchain_has_token_market(func):
    """
    Make sure blockchain is of type "token market" before proceeding
    """
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        miner_id = request.session['miner_id']
        miner = get_object_or_404(Miner, pk=miner_id)
        blockchain = miner.blockchain
        if not blockchain.has_tokens():
            return redirect(reverse('bcsim:home'))
        return func(request, *args, **kwargs)
    return wrapper
