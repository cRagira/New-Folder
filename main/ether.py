import pprint
import requests
import datetime
import django
import os
from dotenv import load_dotenv
load_dotenv()

from .models import EtherTransaction
API_KEY=os.environ.get('OPTIMISM_KEY')
BASE_URL="https://api-optimistic.etherscan.io/api"
address=os.environ.get('BINANCE_ADDR')
ETHER_VALUE= 10**18
print('fetching trx')


def fetch_transactions():
    def make_api_url(module,action,address,**kwargs):
        url=BASE_URL+f'?module={module}&action={action}&address={address}&apikey={API_KEY}'
        for key, value in kwargs.items():
            url+=f'&{key}={value}'

        return url

    data=[]
    actions=['txlist','txlistinternal','tokentx','tokennfttx','token1155tx']
    for action in actions:
        transaction_url=make_api_url('account',action,address,startblock=0,endblock=99999999, page=1, offset=10000, sort='desc')
        response=requests.get(transaction_url)
        transactions=response.json()['result']
        data.extend(transactions)

    data.sort(key=lambda x: int(x['timeStamp']))
    

    for tx in data:
        t=int(datetime.datetime.now().timestamp())
        hash=tx['hash']
        from_addr=tx['from']
        to=tx['to']
        value=int(tx['value'])/ETHER_VALUE
        timeStamp=int(tx['timeStamp'])

        if value>0 and to==address:#received
            if int(tx['timeStamp'])>(int(datetime.datetime.now().timestamp()) - 1000):
            # if t:
                EtherTransaction.objects.get_or_create(hash=hash,from_addr=from_addr,to=to,value=value,timeStamp=timeStamp)
            # print(f'hash={hash},from_addr={from_addr},to={to},value={value},timeStamp={timeStamp}')


