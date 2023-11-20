import decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from django_countries.fields import CountryField
import pycountry
from djmoney.contrib.exchange.models import convert_money

def get_currency(code):
        country = pycountry.countries.get(alpha_3=code)
        currency_code = pycountry.currencies.get(numeric=country.numeric)
        
        return currency_code.alpha_3

def get_referral_id():
    def gen():
        return str(uuid.uuid4())[:6]
    while True:
        ref=gen()
        if not Profile.objects.filter(referral_id=ref).exists():
            return ref


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile=Profile.objects.create(user=instance)
        profile.referral_id=get_referral_id()



@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Profile(models.Model):

    SU= User.objects.filter(is_superuser=True).last().pk
    user=models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone=models.CharField(max_length=20)
    country=CountryField(default='US') #alpha3
    referral_id=models.CharField(max_length=6, unique=True)
    referee=models.ForeignKey(User,on_delete=models.SET_DEFAULT, default=SU, related_name='referral', blank=True, null=True)
    total_deposit=MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=Money(0,'USD'))
    is_valid = models.BooleanField(default=False)
    balance=MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=Money(0,'USD'))
    redeem=models.IntegerField(default=0)


    def credit(self,amount):
        cred=Money(amount,get_currency(self.country.alpha3))
        self.balance+=cred
        self.total_deposit+=cred
        self.save()
        minv=Money(99,'KES')
        dep=convert_money(self.total_deposit, 'KES')
        if dep > minv:
            self.is_valid = True

        transaction=Transaction.objects.create(user=self.user,type='cred',amount=cred)
        transaction.save()
    def debit(self,amount):
        self.balance-=Money(amount,get_currency(self.country.alpha3))
        self.save()
        transaction=Transaction.objects.create(user=self.user,type='debi',amount=Money(amount,get_currency(self.country.alpha3)))
        transaction.save()


    def deposit(self,amount):
        depo=Money(amount,get_currency(self.country.alpha3))
        self.balance+=cred
        self.total_deposit+=cred
        self.save()
        transaction=Transaction.objects.create(user=self.user,type='depo',amount=depo)
        transaction.save()

    def withdraw(self,amount):
        self.balance-=Money(amount,get_currency(self.country.alpha3))
        self.save()
        transaction=Transaction.objects.create(user=self.user,type='with',amount=Money(amount,get_currency(self.country.alpha3)))
        transaction.save()

    def __str__(self):
        return str(self.user)
      

class Match(models.Model):
    class stageChoices(models.TextChoices):
        SCHEDULED = 'sche','scheduled'
        LIVE = 'li','live'
        FINISHED = 'fin','finished'
        POSTPONED = 'post','postponed'
        PENALTY = 'pen','after penalty'
        PENDING = 'pend','pending results'
        CANCELLED = 'canc','match cancelled'


    class resultChoices(models.TextChoices):
        PENDING = 'pend','pending'
        HOME = 'home','home win'
        DRAW = 'draw','match drawn'
        AWAY = 'away','away win'
        VOID = 'void','match void'

    class Meta:
        verbose_name_plural = 'Matches'

    match_id = models.CharField(max_length=100, primary_key=True)
    title = models.CharField(max_length=100)
    home = models.CharField(max_length=100)
    away = models.CharField(max_length=100)
    time = models.DateTimeField()
    stage = models.CharField(max_length=10, choices=stageChoices.choices, default=stageChoices.SCHEDULED)
    #TODO fix other outcomes
    home_odds = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    draw_odds = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    away_odds = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)    
    outcome = models.CharField(max_length=4, choices=resultChoices.choices, default=resultChoices.PENDING)
    created = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return(f'{self.home} vs {self.away} {self.time.strftime("%H:%M")} ')
    

class BetTicket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stake_amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    total_odds = models.DecimalField(max_digits=6, decimal_places=2)
    prize = models.DecimalField(max_digits=10, decimal_places=2)
    is_won = models.BooleanField(default=False)
    is_settled = models.BooleanField(default=False)


    class Meta:
        ordering = ['-created_at']


    
    def check_win(self):

        def settle_bet():
            if self.is_settled == False:
                #TODO pay
                selections=self.sselections.all()
                if all(selection.is_correct() for selection in selections):
                    print(f"currentbalance{self.user.profile.balance}")
                    self.user.profile.credit(self.prize)
                    print(f'paid {self.prize} to {self.user} for {self}')
                self.is_settled = True
                
        if self.is_won == False:    
            if self.sselections.filter(selection__in=['home', 'draw', 'away']).exists(): # type: ignore
                selections = self.sselections.all() # type: ignore
                all_correct = all(selection.is_correct() for selection in selections)
                if all_correct:
                    self.is_won = all_correct
                    settle_bet()
            else:
                self.is_won = False
            self.save()

    def __str__(self):
        return (f"bet {self.id}, potential win {self.prize}")

class BetTicketSelection(models.Model):
    class betChoices(models.TextChoices):
        HOME = 'home','home win'
        DRAW = 'draw','match drawn'
        AWAY = 'away','away win'

    bet_ticket = models.ForeignKey(BetTicket, on_delete=models.CASCADE, related_name='sselections')
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    selection = models.CharField(max_length=4, choices=betChoices.choices, default=None)  # e.g., 'team1', 'team2', 'draw'
    odds = models.DecimalField(max_digits=4, decimal_places=2)

    def is_correct(self):
        return self.selection == self.match.outcome

    def __str__(self):
        return (f"bet on {self.match} for {self.selection}")

class Transaction(models.Model):
    class typeChoices(models.TextChoices):
        DEPOSIT='depo','deposit'
        WITHDRAW='with','withdraw'
        DEBIT='debi','debit'
        CREDIT='cred','credit'
    SU= User.objects.filter(is_superuser=True).last().pk
    user=models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=SU)
    type=models.CharField(max_length=10, choices=typeChoices.choices, default=None)
    amount=MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    created=models.DateTimeField(auto_now_add=True)