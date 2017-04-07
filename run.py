#! /bin/python3

import time
import schedule
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings


def crawl_job():
    settings = get_project_settings()
    configure_logging(settings=settings)
    runner = CrawlerRunner(settings)

    runner.crawl('toho_v2', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('movix', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('aeon', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('united', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('kinezo', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('site109', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('cinemasunshine', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('forum', keep_old_data=True, crawl_all_cinemas=True)
    runner.crawl('korona', keep_old_data=True, crawl_all_cinemas=True)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()


if __name__ == '__main__':
    print('schedule start')
    schedule.every().day.at('12:00').do(crawl_job)
    while True:
        schedule.run_pending()
        time.sleep(1)
