#! /bin/python3

import time
import schedule
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings


def crawl_job():
    @defer.inlineCallbacks
    def crawl(runner):
        yield runner.crawl('toho_v2')
        yield runner.crawl('movix', keep_old_data=True)
        yield runner.crawl('aeon', keep_old_data=True)
        yield runner.crawl('united', keep_old_data=True)
        yield runner.crawl('kinezo', keep_old_data=True)
        yield runner.crawl('site109', keep_old_data=True)
        yield runner.crawl('cinemasunshine', keep_old_data=True)
        yield runner.crawl('forum', keep_old_data=True)
        yield runner.crawl('korona', keep_old_data=True)
        reactor.stop()
    configure_logging()
    runner = CrawlerRunner(get_project_settings())
    crawl(runner)
    reactor.run()
    return schedule.CancelJob


if __name__ == '__main__':
    schedule.every().day.at('13:00').do(crawl_job)
    while True:
        schedule.run_pending()
        time.sleep(1)
