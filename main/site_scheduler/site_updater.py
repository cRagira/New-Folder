from apscheduler.schedulers.background import BackgroundScheduler
from main.scrapper import fetch_matches


def start():
    print('started')
    scheduler = BackgroundScheduler()
    # scheduler.add_job(fetch_matches, "interval", minutes=5, id="matches_001", replace_existing=True)
    scheduler.start()