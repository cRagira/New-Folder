import pprint
import requests
import datetime
import django
import os

from .models import EtherTransaction
API_KEY='X39WS2Z5EFKSA7MT4642PEAF4CXK6KM9TG'
BASE_URL="https://api.etherscan.io/api"
address='0x338Cf2ec12E5473FC6D9eE0806289Dd109921F74'
ETHER_VALUE= 10**18


def fetch_transactions():
    def make_api_url(module,action,address,**kwargs):
        url=BASE_URL+f'?module={module}&action={action}&address={address}&apikey={API_KEY}'
        for key, value in kwargs.items():
            url+=f'&{key}={value}'

        return url

    transaction_url=make_api_url('account','txlist',address,startblock=0,endblock=99999999, page=1, offset=10000, sort='desc')
    response=requests.get(transaction_url)
    data=response.json()['result']
    internaltrx_url=make_api_url('account','txlistinternal',address,startblock=0,endblock=99999999, page=1, offset=10000, sort='desc')
    response2=requests.get(internaltrx_url)
    data2=response2.json()['result']
    data.extend(data2)
    data.sort(key=lambda x: int(x['timeStamp']))

    for tx in data:
        pprint.pprint(tx)
        print('---------')
        t=int(datetime.datetime.now().timestamp())
        hash=tx['hash']
        from_addr=tx['from']
        to=tx['to']
        value=int(tx['value'])/ETHER_VALUE
        timeStamp=int(tx['timeStamp'])


        if int(tx['timeStamp'])<(int(datetime.datetime.now().timestamp()) - 600):
            print('yeahhh')
            EtherTransaction.objects.get_or_create(hash=hash,from_addr=from_addr,to=to,value=value,timeStamp=timeStamp)

    print('fetching trx')

