from django.urls import path
from . import views


app_name="main"
urlpatterns = [
    path('',views.home, name='home'),
    path('bets/',views.bets, name='mybets'),
    path('transactions/',views.transactions, name='transactions'),
    path('login/', views.loginview, name='login'),
    path('trx/',views.trx,name='trx'),
    path('country/',views.country, name='country'),
    path('withdraw/<str:user_id>/<str:amount>/',views.withdraw, name='withdraw'),
    ]