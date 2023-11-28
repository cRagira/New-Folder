from django.urls import path
from . import views


app_name="main"
urlpatterns = [
    path('',views.home, name='home'),
    path('bets/',views.bets, name='mybets'),
    path('bets/<int:id>', views.bet_detail, name='bet-detail'),
    path('fetch/',views.fetch_matches, name='fetch-matches'),
    path('transact/',views.transact, name='transact'),
    path('transactions/',views.transactions, name='transactions'),
    
    #path('api/<str:pk>', views.MatchDetail.as_view(), name='Match-detail-api')
]