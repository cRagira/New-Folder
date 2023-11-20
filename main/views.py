from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Match, BetTicket,BetTicketSelection, get_currency
from djmoney.money import Money
import json


# Create your views here.
def home(request):
    if request.method == 'POST':
        dict = request.POST.dict()
        dict.pop('csrfmiddlewaretoken')
        amount = int(dict.pop('amount'))
        if request.user.profile.balance > Money(amount,get_currency(request.user.profile.country.alpha3)):
            bet = BetTicket.objects.create(user=request.user, stake_amount=amount, total_odds=1, prize=100)
            total_odds = 1

            for key,value in dict.items():
                match = Match.objects.get(match_id=key)
                print(value)
                if value == 'home':
                    odds = match.home_odds
                elif value == 'draw':
                    odds = match.draw_odds
                elif value == 'away':
                    odds = match.away_odds
                
                total_odds*=odds

                pick = BetTicketSelection.objects.create(bet_ticket=bet,match=match,selection=value,odds=odds)
            print(total_odds)
            bet.total_odds=total_odds
            bet.prize=amount*total_odds
            bet.save()
            request.user.profile.debit(amount)

        else:
            print('balance insuffivient')

    matches = Match.objects.filter(stage='sche')
    
    return render(request, "main/home.html" ,context={"matches":matches})


@login_required
def bets(request):
    bets = BetTicket.objects.filter(user=request.user.id)

    return render(request,'main/bets.html',{'bets':bets})


@login_required
def bet_detail(request, id):
    bet = BetTicket.objects.get(id=id)

    return render(request, "main/bet_detail.html",{'bet':bet})


from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
@require_POST
def fetch_matches(request):
    matches = (json.loads(request.body))
    for match in matches:
        instance = Match.objects.filter(match_id=match['match_id']).first()
        if instance:
            instance.stage=match['stage']
            instance.home_odds=match['home_odds']
            instance.draw_odds=match['draw_odds']
            instance.away_odds=match['away_odds']
            instance.home_score=match['home_score']
            instance.away_score=match['away_score']
            instance.save()
        
        else:
            Match.objects.create(match_id=match['match_id'],title=match['title'],home=match['home'],away=match['away'],time=match['time'],stage=match['stage'],home_odds=match['home_odds'],draw_odds=match['draw_odds'],away_odds=match['away_odds'],home_score=match['home_score'],away_score=match['away_score'])
    return HttpResponse('fetched')
