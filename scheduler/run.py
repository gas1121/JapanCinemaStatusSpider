#! /bin/python3
"""
Scheduler for running spider periodly. We have to use subprocess.call as
scrapyd do not support run multiple spider in a single call, and we want to
use different log file each time we run spider.
"""
import time
import schedule
import tldextract
from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper

from scheduler.utils import (create_crawl_job, create_domain_throttle_job,
                             send_job_to_kafka, change_spider_config)


spider_setting = {
    "walkerplus_cinema": {
        "url": "http://movie.walkerplus.com/theater/",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "walkerplus_movie": {
        "url": "http://movie.walkerplus.com/list/",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "aeon": {
        "url": "http://www.aeoncinema.com/theater/",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "toho_v2": {
        "url": "https://hlo.tohotheater.jp/responsive/json/theater_list.json",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "united": {
        "url": "http://www.unitedcinemas.jp/index.html",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "movix": {
        "url": "http://www.smt-cinema.com/theater/",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "kinezo": {
        "url": "http://kinezo.jp/pc/",
        "throttle": {
            "hits": 60,
            "window": 60,
            "scale": 1.0,
        },
    },
    "cinema109": {
        "url": "http://109cinemas.net/",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "korona": {
        "url": "http://www.korona.co.jp/cinema/",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "cinemasunshine": {
        "url": "http://www.cinemasunshine.co.jp/theater/",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
    "forum": {
        "url": "http://forum-movie.net/theater-list",
        "throttle": {
            "hits": 90,
            "window": 60,
            "scale": 1.0,
        },
    },
}


# top level domain extractor
extractor = tldextract.TLDExtract()


def cinema_crawl_job(logger, settings):
    logger.info("begin cinema crawl job")
    # clear cinema data in database first
    clear_topic = settings['JCSS_DATA_PROCESSOR_TOPIC']
    clear_job = {
        'action': 'clear',
        'target': 'cinema',
    }
    send_job_to_kafka(clear_topic, clear_job)
    # TODO maybe clean related key in redis is needed
    # cinema spider do not need read config

    # send crawl job
    crawl_topic = settings['KAFKA_INCOMING_TOPIC']
    crawl_job = create_crawl_job(
        url="http://movie.walkerplus.com/theater/",
        spiderid="walkerplus_cinema")
    send_job_to_kafka(crawl_topic, crawl_job)


def movie_crawl_job(logger, settings):
    logger.info("begin movie crawl job")
    # clear movie data first
    clear_topic = settings['JCSS_DATA_PROCESSOR_TOPIC']
    clear_job = {
        'action': 'clear',
        'target': 'movie',
    }
    send_job_to_kafka(clear_topic, clear_job)
    # TODO maybe clean related key in redis is needed
    # cinema spider do not need read config

    crawl_topic = settings['KAFKA_INCOMING_TOPIC']
    crawl_job = create_crawl_job(
        url="http://movie.walkerplus.com/list/", spiderid="walkerplus_movie")
    send_job_to_kafka(crawl_topic, crawl_job)


def showing_crawl_job(logger, settings):
    logger.info("begin showing crawl job")
    # TODO maybe clean related key in redis is needed

    crawl_topic = settings['KAFKA_INCOMING_TOPIC']
    for spider_id in spider_setting:
        # config spider properly
        change_spider_config(
            spider_id, settings, use_sample=False, crawl_booking_data=False,
            crawl_all_cinemas=True, crawl_all_movies=True)
        url = spider_setting[spider_id]['url']
        crawl_job = create_crawl_job(url=url, spiderid=spider_id)
        send_job_to_kafka(crawl_topic, crawl_job)


def showing_booking_crawl_job(logger, settings):
    logger.info("begin showing booking crawl job")
    # TODO maybe clean related key in redis is needed

    crawl_topic = settings['KAFKA_INCOMING_TOPIC']
    for spider_id in spider_setting:
        # config spider properly
        change_spider_config(
            spider_id, settings, use_sample=False, crawl_booking_data=True,
            crawl_all_cinemas=True, crawl_all_movies=True)
        url = spider_setting[spider_id]['url']
        crawl_job = create_crawl_job(url=url, spiderid=spider_id)
        send_job_to_kafka(crawl_topic, crawl_job)


def showing_booking_sample_crawl_job(logger, settings):
    logger.info("begin showing booking sample crawl job")
    # TODO maybe clean related key in redis is needed

    crawl_topic = settings['KAFKA_INCOMING_TOPIC']
    for spider_id in spider_setting:
        # config spider properly
        change_spider_config(
            spider_id, settings, use_sample=True, crawl_booking_data=True,
            crawl_all_cinemas=False, crawl_all_movies=True)
        url = spider_setting[spider_id]['url']
        crawl_job = create_crawl_job(url=url, spiderid=spider_id)
        send_job_to_kafka(crawl_topic, crawl_job)


def set_throttle_job(logger, settings):
    logger.info("begin to set site throttle")
    for spider_id in spider_setting:
        url = spider_setting[spider_id]["url"]
        ex_res = extractor(url)
        top_level_domain = "{}.{}".format(ex_res.domain, ex_res.suffix)
        hits = spider_setting[spider_id]["throttle"]["hits"]
        window = spider_setting[spider_id]["throttle"]["window"]
        scale = spider_setting[spider_id]["throttle"]["scale"]
        throttle_job = create_domain_throttle_job(
            domain=top_level_domain, hits=hits, window=window, scale=scale)
        send_job_to_kafka(settings['KAFKA_INCOMING_TOPIC'], throttle_job)


def debug_crawl_job(spiders=[], settings=None, crawl_booking_data=True,
                    crawl_all_cinemas=False, crawl_all_movies=False,
                    movie_list=[], cinema_list=[], date=None):
    """start a crawl job for debug perpose
    """
    settings = settings or SettingsWrapper().load(local='localsettings.py')
    crawl_topic = settings['KAFKA_INCOMING_TOPIC']
    for spider_id in spiders:
        if spider_id not in spider_setting.keys():
            continue
        # config spider properly
        change_spider_config(spider_id, settings, use_sample=False,
                             crawl_booking_data=crawl_booking_data,
                             crawl_all_cinemas=crawl_all_cinemas,
                             crawl_all_movies=crawl_all_movies,
                             movie_list=movie_list, cinema_list=cinema_list,
                             date=date)
        url = spider_setting[spider_id]['url']
        crawl_job = create_crawl_job(url=url, spiderid=spider_id)
        send_job_to_kafka(crawl_topic, crawl_job)


if __name__ == '__main__':
    settings = SettingsWrapper().load(local='localsettings.py')

    logger = LogFactory.get_instance(
        json=settings['LOG_JSON'], stdout=settings['LOG_STDOUT'],
        level=settings['LOG_LEVEL'], name=settings['LOGGER_NAME'],
        dir=settings['LOG_DIR'], file=settings['LOG_FILE'],
        bytes=settings['LOG_MAX_BYTES'], backups=settings['LOG_BACKUPS'])
    logger.info("scheduler started")

    # set per site throttle to make crawl faster
    set_throttle_job(logger, settings)

    # if JCSS_CLEAR_SHOWING_AT_INIT is True, clear showing data
    if settings['JCSS_CLEAR_SHOWING_AT_INIT']:
        clear_topic = settings['JCSS_DATA_PROCESSOR_TOPIC']
        clear_job = {
            'action': 'clear',
            'target': 'showing',
        }
        send_job_to_kafka(clear_topic, clear_job)

    # every time schedule script starts, crawl cinema and movie data first
    cinema_crawl_job(logger, settings)
    movie_crawl_job(logger, settings)
    logger.info("initial job finished")

    # crawl movie and cinema info every week
    schedule.every().monday.at('19:00').do(movie_crawl_job, logger, settings)
    schedule.every().monday.at('20:00').do(cinema_crawl_job, logger, settings)
    # crawl showing data at utc 21:00(6:00 jpn) everyday
    schedule.every().day.at('21:00').do(showing_crawl_job, logger, settings)
    # crawl showing booking data at utc 11:00(20:00 jpn) every friday and
    # saturday for weekend information
    schedule.every().friday.at('11:00').do(
        showing_booking_sample_crawl_job, logger, settings)
    schedule.every().friday.at('22:00').do(
        showing_booking_crawl_job, logger, settings)
    schedule.every().saturday.at('11:00').do(
        showing_booking_sample_crawl_job, logger, settings)
    schedule.every().saturday.at('22:00').do(
        showing_booking_crawl_job, logger, settings)
    while True:
        schedule.run_pending()
        time.sleep(5)
