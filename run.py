#! /bin/python3
"""
Scheduler for running spider periodly. We have to use subprocess.call as
scrapyd do not support run multiple spider in a single call, and we want to
use different log file each time we run spider.
"""

import time
import schedule
from subprocess import call


def movie_crawl_job():
    call(["scrapy", "crawl", "walkerplus_movie"])


def cinema_crawl_job():
    call(["scrapy", "crawl", "walkerplus_cinema"])


def showing_crawl_job():
    call(["scrapy", "crawlshowing"])


if __name__ == '__main__':
    print('schedule start')
    # crawl movie info every week
    schedule.every().monday.at('20:00').do(movie_crawl_job)
    schedule.every().monday.at('20:10').do(cinema_crawl_job)
    # crawl showing info UTC 20:00(Beijing 04:00) everyday
    schedule.every().day.at('20:00').do(showing_crawl_job)
    while True:
        schedule.run_pending()
        time.sleep(1)
