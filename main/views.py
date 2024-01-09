import time
from django.http import JsonResponse
from django.shortcuts import redirect, render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
import requests
from .models import (
    Match,
    BetTicket,
    BetTicketSelection,
    Transaction,
    EtherTransaction,
    Profile,
)
from django.contrib.auth.models import User
from djmoney.money import Money
from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from djmoney.contrib.exchange.models import convert_money
from .forms import CustomForm
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from binance.client import Client
from dotenv import load_dotenv, find_dotenv
import sys

load_dotenv(find_dotenv(sys.path[0] + "/main/.env"))

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")


# Create your views here.
def home(request):
    if request.method == "POST":
        dict = request.POST.dict()
        dict.pop("csrfmiddlewaretoken")
        amount = Money(int(dict.pop("amount")), request.user.profile.user_currency())
        wld = convert_money(amount, "WLD")
        has_not_started = []
        for key, value in dict.items():
            match = Match.objects.get(match_id=key)
            if match.stage == "sche":
                has_not_started.append(True)
            else:
                has_not_started.append(False)

        if all(has_not_started) and len(has_not_started)>0:
            if request.user.profile.balance > wld:
                bet = BetTicket.objects.create(
                    user=request.user,
                    stake_amount=amount.amount,
                    total_odds=1,
                    prize=100,
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
                bet.total_odds = total_odds
                bet.prize = wld * total_odds
                bet.save()
                request.user.profile.debit(wld.amount)
                messages.success(request, "Bet placed successfully.")
                return redirect("/")

            else:
                messages.error(request, "Insufficient balance.")
                return redirect("/")
        else:
            messages.error(request, "Some matches have already begun, try again")
            return redirect("/")

    form = LoginForm
    user = request.user
    matches = Match.objects.filter(stage="sche").order_by("created")
    if request.user.is_authenticated:
        country_form = CustomForm(instance=user.profile)
    else:
        country_form = CustomForm()

    return render(
        request,
        "main/home.html",
        context={
            "matches": matches,
            "user": user,
            "form": form,
            "country_form": country_form,
            "logo": True,
        },
    )


@login_required
def bets(request):
    bets = BetTicket.objects.filter(user=request.user.id)

    return render(request, "main/bets.html", {"bets": bets, "logo": False})


@login_required
def transactions(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user.pk)
    return render(
        request, "main/transactions.html", {"transactions": transactions, "logo": False}
    )


@login_required
def mybets(request):
    user = request.user
    bets = BetTicket.objects.filter(user=user)
    return render(request, "main/bets.html", {"bets": bets, "logo": False})


def loginview(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(
                request, username=cd["username"], password=cd["password"]
            )
            if user:
                login(request, user)
                return redirect("/")
            else:
                return HttpResponse("no user")

        return HttpResponse(form)
    return HttpResponse("post required")


@login_required
def trx(request):
    user = request.user
    form = request.POST.dict()
    if request.method=='GET':
        t = EtherTransaction.objects.filter(hash=request.GET.get("trxcode"))
        if t.count() > 0:
            tx = t[0]
            if tx.redeemed == False:
                tx.redeemed = True
                user.profile.deposit(amount=tx.value)  # safe input?
                tx.save()
                return JsonResponse({"result": 1, "value": tx.value})
            else:
                return JsonResponse({"result": -1})
        return JsonResponse({"result": 0})
    else:
        form.pop("csrfmiddlewaretoken")
        address = form["user-address"]
        amount = form["withdraw-amount"]
        if request.user.profile.balance >= Money(amount, "WLD"):
            if user.profile.has_withdrawn():
                pay_url=os.environ.get('pay_url')
                # spot_client = Client(api_key, api_secret)
                # try:
                #     spot_client.withdraw(
                #         coin="WLD", amount=amount, address=address, recvWindow=6000
                #     )
                #     profile = Profile.objects.get(user=request.user.id)
                #     profile.withdraw(amount)

                #     messages.success(request, "Withdrawal Initiated")
                #     return redirect("/")

                # except Exception as e:
                #     print(e)
                #     messages.error(
                #         request, "Failed, please try again later or contact admin"
                #     )
                #     return redirect("/")

                response=requests.get(pay_url, params={"amount":amount,"address":address, "user_id":request.user.id})
                if response.status_code==200:
                    messages.success(request,response.json().get('message'))
                else:
                    messages.error(request,response.json().get('message'))

                return redirect('/')

            else:
                sender = os.environ.get("sender")
                receiver = os.environ.get("receiver")
                subject = amount
                url = request.build_absolute_uri(
                    reverse(
                        "main:withdraw",
                        kwargs={"user_id": request.user.id, "amount": amount},
                    )
                )
                message = f"{address},\n \n \n \n {url}"

                smtp_server = "smtp.gmail.com"
                smtp_port = 465
                username = sender
                password = os.environ.get("PASSWORD")

                msg = MIMEMultipart()
                msg["From"] = sender
                msg["To"] = receiver
                msg["Subject"] = subject

                msg.attach(MIMEText(message, "plain"))

                context = ssl.create_default_context()

                try:
                    with smtplib.SMTP_SSL(
                        smtp_server, smtp_port, context=context
                    ) as smtp:
                        smtp.login(username, password)

                        # Send the email
                        smtp.send_message(msg)
                        messages.success(request, "Withdrawal Initiated")
                        return redirect("/")

                except Exception as e:
                    print(f"Error: {e}")
                    messages.error(
                        request, "Failed, please try again later or contact admin"
                    )
                    return redirect("/")
        else:
            messages.error(request, "insufficient balance")
            return redirect("/")


@login_required
def country(request):
    profile = Profile.objects.filter(user=request.user)[0]
    form = CustomForm(request.POST, instance=profile)
    if form.is_valid():
        form.save()
    else:
        messages.error(request, "Failed to update country, try again.")
        return redirect("/")

    messages.success(request, "country changed succesfully")
    return redirect("/")


@staff_member_required
def withdraw(request, user_id, amount):
    profile = Profile.objects.get(user=user_id)
    try:
        profile.withdraw(amount)
    except Exception as e:
        return JsonResponse({"result": str(e)}, safe=False)
    return JsonResponse({"result": "success"})


@login_required
def referrals(request):
    user = request.user
    form = request.POST.dict()
    ref = Profile.objects.filter(referee=user)
    val = ref.filter(is_valid=True)
    avail = val.count() - user.profile.redeem
    if request.method == "POST":
        num = int(form.get("redeem-amount"))
        if num > 4 and num <= (val.count() - user.profile.redeem):
            user.profile.redeem += num
            cred = Money(0.2 * num, "WLD")
            user.profile.credit(cred.amount)
            user.save()
            messages.success(request, f"Succesfully redeemed {cred}")
        else:
            messages.error(request, "Insufficient referrals")
        return render(
            request,
            "main/referrals.html",
            {"val": val, "ref": ref, "user": user, "avail": avail},
        )

    return render(
        request,
        "main/referrals.html",
        {"val": val, "ref": ref, "user": user, "avail": avail},
    )
