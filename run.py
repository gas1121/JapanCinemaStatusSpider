#! /bin/python3

import time
import schedule
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def crawl_job():
    process = CrawlerProcess(get_project_settings())
    process.crawl('toho_v2')
    process.start()
    return schedule.CancelJob


if __name__ == '__main__':
    schedule.every().day.at('11:43').do(crawl_job)
    while True:
        schedule.run_pending()
        time.sleep(1)
