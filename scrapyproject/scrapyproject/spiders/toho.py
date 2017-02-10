# -*- coding: utf-8 -*-
import scrapy


class TohoSpider(scrapy.Spider):
    name = "toho"
    allowed_domains = ["hlo.tohotheater.jp"]
    start_urls = ['https://hlo.tohotheater.jp/net/schedule/076/TNPI2000J01.do']

    def parse(self, response):
        yield {
            'result': len(response.css('div.schedule-item'))
        }
