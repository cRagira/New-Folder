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
from babel.numbers import get_territory_currencies

ref_value=Money(50, 'KES')
def get_currency(code):
    currency = get_territory_currencies(code)[0]
    return currency

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
    country=CountryField(default='KE') #alpha3
    referral_id=models.CharField(max_length=6)
    referee=models.ForeignKey(User,on_delete=models.SET_DEFAULT, default=SU, related_name='referral', blank=True, null=True)
    total_deposit=MoneyField(max_digits=14, decimal_places=2, default_currency='WLD', default=Money(0,'WLD'))
    is_valid = models.BooleanField(default=False)
    balance=MoneyField(max_digits=14, decimal_places=2, default_currency='WLD', default=Money(0,'WLD'))
    bonus=MoneyField(max_digits=14, decimal_places=2, default_currency='WLD', default=Money(0,'WLD'))
    redeem=models.IntegerField(default=0)
    image=models.ImageField(blank=True, upload_to='uploads/dp/',null=True, default='default.png')
    address=models.CharField(max_length=256, blank=True, null=True)

    def get_balance(self):
        balance= convert_money(self.balance,self.user_currency())
        return balance.amount.quantize(decimal.Decimal('.01'))

    def credit(self,amount):
        cred=Money(amount,'WLD')
        self.balance+=cred
        self.total_deposit+=cred
        self.save()
        minv=Money(.5,'WLD')
        if cred > minv:
            self.is_valid = True

        transaction=Transaction.objects.create(user=self.user,type='cred',amount=cred)
        transaction.save()
    def debit(self,amount):
        self.balance-=Money(amount,'WLD')
        self.save()
        transaction=Transaction.objects.create(user=self.user,type='debi',amount=Money(amount,'WLD'))
        transaction.save()


    def deposit(self,amount):
        depo=Money(amount,'WLD')
        self.balance+=depo
        if self.total_deposit==Money(0,'WLD') and depo>Money(2,'WLD'):
            self.bonus=depo*.25
        self.total_deposit+=depo
        self.save()
        transaction=Transaction.objects.create(user=self.user,type='depo',amount=depo)
        transaction.save()

    def withdraw(self,amount):
        if self.balance>=Money(amount,'WLD'):
            self.balance-=Money(amount,'WLD')
            self.save()
            transaction=Transaction.objects.create(user=self.user,type='with',amount=Money(amount,'WLD'))
            #TODO trx hash
            transaction.save()
        else:
            raise ValueError('Insufficient balance')

    def user_currency(self):
        currency=get_currency(self.country.code)
        return currency
    
    def unredeemed_refs(self):
        ref=Profile.objects.filter(referee=self.user)
        num=ref.filter(is_valid=True)
        return num.count()*convert_money(ref_value, 'WLD')
    
    def has_withdrawn(self):
        transactions=Transaction.objects.filter(user=self.user)
        withdraws=transactions.filter(type='with')
        if withdraws.count()>0:
            return True
        else:
            return False

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
        ordering = ['-created']


    match_id = models.CharField(max_length=100, primary_key=True)
    title = models.CharField(max_length=100)
    home = models.CharField(max_length=100)
    away = models.CharField(max_length=100)
    time = models.DateTimeField()
    stage = models.CharField(max_length=10, choices=stageChoices.choices, default=stageChoices.SCHEDULED)
    #TODO fix other outcomes
    home_odds = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    draw_odds = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    away_odds = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)    
    outcome = models.CharField(max_length=4, choices=resultChoices.choices, default=resultChoices.PENDING)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    
    def __str__(self):
        return(f'{self.home} vs {self.away} {self.time.strftime("%H:%M")} ')
    

class BetTicket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stake_amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    total_odds = models.DecimalField(max_digits=10, decimal_places=2)
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
                selections = self.sselections.all() 
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
    amount=MoneyField(max_digits=10, decimal_places=2, default_currency='WLD')
    created=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']


    def __str__(self):
        return (self.type + " " + str(self.amount) +" " + str(self.created.strftime('%Y-%m-%d - %H:%M')))
    

class EtherTransaction(models.Model):
    hash=models.CharField(max_length=256)
    from_addr=models.CharField(max_length=256)
    to=models.CharField(max_length=256)
    value=models.FloatField()
    redeemed=models.BooleanField(default=False)
    timeStamp=models.IntegerField()
    txreceipt_status=models.CharField(max_length=256, blank=True, null=True)
    