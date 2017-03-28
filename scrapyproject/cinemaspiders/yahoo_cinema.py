# -*- coding: utf-8 -*-
from scrapyproject.cinemaspiders.cinema_spider import CinemaSpider


class YahooCinemaSpider(CinemaSpider):
    """
    cinema info spider for http://movies.yahoo.co.jp
    """
    name = "yahoo_cinema"
    allowed_domains = ["movies.yahoo.co.jp"]
    start_urls = ['http://movies.yahoo.co.jp/area/']

    # settings for cinema_spider
    county_xpath = '//div[@id="allarea"]//a'
    cinema_xpath = '//div[@id="theater"]//a'
    cinema_site_xpath = '//th[text()="公式サイト"]/..//a/text()'
    screen_text_xpath = '//th[text()="座席"]/..//li/text()'
    screen_pattern = r"^\[?(.*?)(\] )?客席数 (.+)$"
    screen_name_pattern = r"\1"
    seat_number_pattern = r"\3"

    def adjust_cinema_url(self, url):
        """
        adjust cinema page's url if needed
        """
        return url + "/info/"
