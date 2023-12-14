import datetime
import pprint
import time
from django.http import JsonResponse
from django.shortcuts import redirect, render, HttpResponse
from django.contrib.auth.decorators import login_required
import requests
from .models import Match, BetTicket, BetTicketSelection, get_currency, Transaction, EtherTransaction
from djmoney.money import Money
import json
from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
import logging
import os
from binance.spot import Spot as Client
from binance.lib.utils import config_logging
from dotenv import load_dotenv
load_dotenv()
api_key=os.environ.get('API_KEY')
api_secret=os.environ.get('API_SECRET')

BINANCE_URL='https://api.binance.com/sapi/v1/capital/withdraw/apply'


# Create your views here.
def home(request):
    if request.method == "POST":
        dict = request.POST.dict()
        print(dict)
        dict.pop("csrfmiddlewaretoken")
        amount = int(dict.pop("amount"))
        if request.user.profile.balance > Money(
            amount, 'WLD'
        ):
            bet = BetTicket.objects.create(
                user=request.user, stake_amount=amount, total_odds=1, prize=100
            )
            total_odds = 1

            for key, value in dict.items():
                match = Match.objects.get(match_id=key)
                if value == "home":
                    odds = match.home_odds
                elif value == "draw":
                    odds = match.draw_odds
                elif value == "away":
                    odds = match.away_odds

                total_odds *= odds

                pick = BetTicketSelection.objects.create(
                    bet_ticket=bet, match=match, selection=value, odds=odds
                )
            print(total_odds)
            bet.total_odds = total_odds
            bet.prize = amount * total_odds
            bet.save()
            request.user.profile.debit(amount)
            messages.success(request, 'Bet placed successfully.')
            return redirect('/')

        else:
            print('insuff')
            messages.error(request, 'Insufficient balance.')
            return redirect('/')

    form=LoginForm
    user = request.user
    matches = Match.objects.filter(stage="sche")

    return render(request, "main/home.html", context={"matches": matches, "user": user, "form":form})


@login_required
def bets(request):
    bets = BetTicket.objects.filter(user=request.user.id)

    return render(request, "main/bets.html", {"bets": bets})


@login_required
def bet_detail(request, id):
    bet = BetTicket.objects.get(id=id)

    return render(request, "main/bet_detail.html", {"bet": bet})


from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def fetch_matches(request):
    matches = json.loads(request.body)
    for match in matches:
        instance = Match.objects.filter(match_id=match["match_id"]).first()
        if instance:
            instance.stage = match["stage"]
            instance.home_odds = match["home_odds"]
            instance.draw_odds = match["draw_odds"]
            instance.away_odds = match["away_odds"]
            instance.home_score = match["home_score"]
            instance.away_score = match["away_score"]
            instance.save()

        else:
            Match.objects.create(
                match_id=match["match_id"],
                title=match["title"],
                home=match["home"],
                away=match["away"],
                time=match["time"],
                stage=match["stage"],
                home_odds=match["home_odds"],
                draw_odds=match["draw_odds"],
                away_odds=match["away_odds"],
                home_score=match["home_score"],
                away_score=match["away_score"],
            )
    return HttpResponse("fetched")


def transactions(request):
    user=request.user
    transactions=Transaction.objects.filter(user=user.pk)
    return render(request, 'main/transactions.html', {"transactions":transactions})

def mybets(request):
    user=request.user
    bets=BetTicket.objects.filter(user=user)
    return render(request, 'main/bets.html', {"bets":bets})

def loginview(request):
    if request.method=='POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request,username=cd['username'],password=cd['password'])
            if user:
                login(request, user)
                return redirect('/')
            else:
                return HttpResponse('no user')
            
        return HttpResponse(form)
    return HttpResponse('post required')
    

def trx(request):
    user=request.user
    form=request.POST.dict()
    print(form)
    form.pop('csrfmiddlewaretoken')
    count=0
    if form.get('trxcode'):
        while count<5:
            t=EtherTransaction.objects.filter(hash=form['trxcode'])
            count+=1
            time.sleep(5+count)
            if t.count()==0:
                continue
            else:
                tx=t[0]
                if tx.redeemed==False:
                    tx.redeemed=True
                    user.profile.deposit(amount=tx.value) #safe input?
                    tx.save()
                    return JsonResponse({'result':1,'value':tx.value})
                else:
                    return JsonResponse({'result':2})
        return JsonResponse({'result':0})
    else:
        address=form['user-address']
        amount=form['withdraw-amount']
        print(api_key,api_secret)
        if user.profile.has_withdrawn():
            config_logging(logging, logging.DEBUG)
            spot_client = Client(api_key, api_secret, show_header=True)
            response =logging.info(spot_client.withdraw(coin="WLD", amount=amount, address=address))
            print(response)
        else:
            #send message
            pass


