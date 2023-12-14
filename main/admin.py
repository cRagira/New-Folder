from django.contrib import admin
from .models import BetTicket, BetTicketSelection, Match, Profile, Transaction, EtherTransaction
# Register your models here.
admin.site.register(BetTicket)
admin.site.register(BetTicketSelection)
admin.site.register(Transaction)
admin.site.register(EtherTransaction)
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__','stage','home_odds','draw_odds','away_odds','home_score','away_score','time')

admin.site.register(Profile)