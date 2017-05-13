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
    call(["scrapy", "crawl", "--all_showing", "--movie_list=無限の住人"])
    #call(["scrapy", "crawl", "--all_showing", "--keep_old_data",
    #      "--crawl_all_cinemas", "--crawl_all_movies"])


if __name__ == '__main__':
    print('schedule start')
    # every time schedule script starts, crawl cinema and movie data first
    cinema_crawl_job()
    movie_crawl_job()
    print('initial job finished')
    # crawl movie and cinema info every week
    schedule.every().monday.at('19:00').do(movie_crawl_job)
    schedule.every().monday.at('20:00').do(cinema_crawl_job)
    # crawl showing info as utc 21:00(6:00 jpn) everyday
    schedule.every().day.at('21:00').do(showing_crawl_job)
    while True:
        schedule.run_pending()
        time.sleep(1)
