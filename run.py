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
        yield runner.crawl('toho_v2', cinema_list="ＴＯＨＯシネマズ光の森",
                           keep_old_data=True)
        reactor.stop()
    configure_logging()
    runner = CrawlerRunner(get_project_settings())
    crawl(runner)
    reactor.run()
    return schedule.CancelJob


if __name__ == '__main__':
    def test():
        print("test")
    # schedule.every().day.at('11:54').do(crawl_job)
    schedule.every().minutes.do(crawl_job)
    schedule.every().minutes.do(test)
    while True:
        schedule.run_pending()
        time.sleep(1)
