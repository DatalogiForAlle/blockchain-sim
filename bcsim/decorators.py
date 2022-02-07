import functools
from django.shortcuts import redirect
from django.urls import reverse


def require_miner_id_is_in_session(func):
    """Make miner_id is in request.session before proceeding"""
    @functools.wraps(func)
    def wrapper_login_required(request, *args, **kwargs):
        if not 'miner_id' in request.session:
            return redirect(reverse('bcsim:home'))
        return func(request, *args, **kwargs)
    return wrapper_login_required
