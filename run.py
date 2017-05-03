#! /bin/python3

import time
import schedule
import requests
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings


def movie_crawl_job():
    settings = get_project_settings()
    configure_logging(settings=settings)
    runner = CrawlerRunner(settings)
    runner.crawl('walkerplus_movie')
    #d = runner.join()
    #d.addBoth(lambda _: reactor.stop())
    reactor.run()


def cinema_crawl_job():
    settings = get_project_settings()
    configure_logging(settings=settings)
    runner = CrawlerRunner(settings)
    runner.crawl('walkerplus_cinema')
    #d = runner.join()
    #d.addBoth(lambda _: reactor.stop())
    reactor.run()


def showing_crawl_job():
    settings = get_project_settings()
    configure_logging(settings=settings)
    runner = CrawlerRunner(settings)

    runner.crawl('toho_v2', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('movix', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('aeon', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('united', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('kinezo', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('site109', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('cinemasunshine', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('forum', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    runner.crawl('korona', keep_old_data=True, crawl_all_cinemas=True,
                 crawl_all_movies=True)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()


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
