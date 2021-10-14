from django.shortcuts import render

from math import floor
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from .models import Blockchain, Block
from .forms import CreateBlockchainForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext as _




@require_GET
def home_view(request):
    
    form = CreateBlockchainForm()
    #    initial={'market_id': request.GET['market_id']})

    # If the client is following an invitation link to a blockchain
    if 'blockchain_id' in request.GET:
        pass
    #    # Fill out the market_id field in the form
    #    form = TraderForm(
    #        initial={'market_id': request.GET['market_id']})

    # If the client is just visiting the home-page base url
    else:
        pass
        # The form should be empty
        #form = TraderForm()
    #if request.method == 'POST':
    #    form = TraderForm(
    #            initial={'market_id': request.GET['market_id']})


    return render(request, 'bcsim/home.html', {'CreateBlockchainForm':form})
