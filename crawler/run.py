#! /bin/python3
"""
Scheduler for running spider periodly. We have to use subprocess.call as
scrapyd do not support run multiple spider in a single call, and we want to
use different log file each time we run spider.
"""

import shutil
import time
import schedule
from subprocess import call


def movie_crawl_job():
    try:
        call(["scrapy", "crawl", "walkerplus_movie", "-s", "JOBDIR=job/movie"])
    finally:
        shutil.rmtree('job/movie', ignore_errors=True)


def cinema_crawl_job():
    try:
        call(["scrapy", "crawl", "walkerplus_cinema", "-s",
              "JOBDIR=job/cinema"])
    finally:
        shutil.rmtree('job/cinema', ignore_errors=True)


def showing_crawl_job():
    try:
        call(["scrapy", "crawl", "--all_showing", "--keep_old_data",
              "--crawl_all_cinemas", "--crawl_all_movies", ])
    finally:
        shutil.rmtree('job/showing', ignore_errors=True)


def showing_booking_crawl_job():
    try:
        call(["scrapy", "crawl", "--all_showing", "--keep_old_data",
              "--crawl_booking_data", "--crawl_all_cinemas",
              "--crawl_all_movies", ])
    finally:
        shutil.rmtree('job/showing_booking', ignore_errors=True)


def showing_booking_sample_crawl_job():
    # TODO pass cinema list by arguments
    try:
        call(["scrapy", "crawl", "--all_showing", "--keep_old_data",
              "--crawl_booking_data", "--crawl_all_movies",
              "--sample_cinema"])
    finally:
        shutil.rmtree('job/showing_booking', ignore_errors=True)


if __name__ == '__main__':
    print('schedule start')
    # every time schedule script starts, crawl cinema and movie data first
    cinema_crawl_job()
    movie_crawl_job()
    print('initial job finished')
    # crawl movie and cinema info every week
    schedule.every().monday.at('19:00').do(movie_crawl_job)
    schedule.every().monday.at('20:00').do(cinema_crawl_job)
    # crawl showing data at utc 21:00(6:00 jpn) everyday
    schedule.every().day.at('21:00').do(showing_crawl_job)
    # crawl showing booking data at utc 11:00(20:00 jpn) every friday and
    # saturday for weekend information
    schedule.every().friday.at('11:00').do(showing_booking_sample_crawl_job)
    schedule.every().friday.at('22:00').do(showing_booking_crawl_job)
    schedule.every().saturday.at('11:00').do(showing_booking_sample_crawl_job)
    schedule.every().saturday.at('22:00').do(showing_booking_crawl_job)
    while True:
        schedule.run_pending()
        time.sleep(1)
