from apscheduler.schedulers.background import BackgroundScheduler
from main.scrapper import fetch_matches
from main.ether import fetch_transactions


def start():
    print('started')
    scheduler = BackgroundScheduler(job_defaults={'max_instances': 2})
    scheduler.add_job(fetch_transactions, "interval", minutes=1, id="trx_001", replace_existing=True)
    scheduler.add_job(fetch_matches, "interval", minutes=5, id="matches_001", replace_existing=True)
    scheduler.start()