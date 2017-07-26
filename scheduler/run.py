#! /bin/python3
"""
Scheduler for running spider periodly. We have to use subprocess.call as
scrapyd do not support run multiple spider in a single call, and we want to
use different log file each time we run spider.
"""

import json
import time
import schedule
from kafka import KafkaProducer
from kazoo.client import KazooClient


def create_crawl_job(url, spiderid, appid="testapp", crawlid="abc123"):
    data = {}
    data["url"] = url
    data["appid"] = appid
    data["crawlid"] = crawlid
    data["spiderid"] = spiderid
    return json.dumps(data)


if __name__ == '__main__':
    # TODO
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.feed(create_crawl_job(url="", spiderid=""))
    # TODO rewrite schedule script as we now use scrapy cluster
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
        time.sleep(5)
