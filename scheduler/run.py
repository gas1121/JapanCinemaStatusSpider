#! /bin/python3
"""
Scheduler for running spider periodly. We have to use subprocess.call as
scrapyd do not support run multiple spider in a single call, and we want to
use different log file each time we run spider.
"""
import time
import schedule
from kafka_monitor import KafkaMonitor
from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper

from scheduler.utils import create_crawl_job, change_spider_config

showing_job_list = [
    {"url": "http://www.aeoncinema.com/theater/", "spiderid": "aeon"},
    {"url": "https://hlo.tohotheater.jp/responsive/json/theater_list.json", "spiderid": "toho_v2"},
    {"url": "http://www.unitedcinemas.jp/index.html", "spiderid": "united"},
    {"url": "http://www.smt-cinema.com/theater/", "spiderid": "movix"},
    {"url": "http://kinezo.jp/pc/", "spiderid": "kinezo"},
    {"url": "http://109cinemas.net/", "spiderid": "cinema109"},
    {"url": "http://www.korona.co.jp/cinema/", "spiderid": "korona"},
    {"url": "http://www.cinemasunshine.co.jp/theater/", "spiderid": "cinemasunshine"},
    {"url": "http://forum-movie.net/theater-list", "spiderid": "forum"},
]


def cinema_crawl_job():
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.setup()
    kafka_monitor.logger.info("begin cinema crawl job")
    kafka_monitor.feed(create_crawl_job(
        url="http://movie.walkerplus.com/theater/",
        spiderid="walkerplus_cinema"))
    kafka_monitor.close()


def movie_crawl_job():
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.setup()
    kafka_monitor.logger.info("begin movie crawl job")
    kafka_monitor.feed(create_crawl_job(
        url="http://movie.walkerplus.com/list/", spiderid="walkerplus_movie"))
    kafka_monitor.close()


def showing_crawl_job():
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.setup()
    kafka_monitor.logger.info("begin showing crawl job")
    # change spider config with zookeeper
    change_spider_config(use_sample=False, crawl_booking_data=False)
    for job in showing_job_list:
        kafka_monitor.feed(create_crawl_job(
            url=job["url"], spiderid=job["spiderid"]))
    kafka_monitor.close()


def showing_booking_crawl_job():
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.setup()
    kafka_monitor.logger.info("begin showing booking crawl job")
    # change spider config with zookeeper
    change_spider_config(use_sample=False, crawl_booking_data=True)
    for job in showing_job_list:
        kafka_monitor.feed(create_crawl_job(
            url=job["url"], spiderid=job["spiderid"]))
    kafka_monitor.close()


def showing_booking_sample_crawl_job():
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.setup()
    kafka_monitor.logger.info("begin showing booking sample crawl job")
    # change spider config with zookeeper
    change_spider_config(use_sample=True, crawl_booking_data=True)
    for job in showing_job_list:
        kafka_monitor.feed(create_crawl_job(
            url=job["url"], spiderid=job["spiderid"]))
    kafka_monitor.close()


if __name__ == '__main__':
    # TODO clean database when needed here instead of in spider
    settings = SettingsWrapper().load(local='localsettings.py')
    logger = LogFactory.get_instance(
        json=settings['LOG_JSON'], stdout=settings['LOG_STDOUT'],
        level=settings['LOG_LEVEL'], name=settings['LOGGER_NAME'],
        dir=settings['LOG_DIR'], file=settings['LOG_FILE'],
        bytes=settings['LOG_MAX_BYTES'], backups=settings['LOG_BACKUPS'])
    logger.info("scheduler started")
    # every time schedule script starts, crawl cinema and movie data first
    cinema_crawl_job()
    movie_crawl_job()
    logger.info("initial job finished")
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
