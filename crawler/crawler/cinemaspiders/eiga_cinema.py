# -*- coding: utf-8 -*-
import requests
from crawler.cinemaspiders.cinema_spider import CinemaSpider
from scrapyproject.utils import do_proxy_request


class EigaCinemaSpider(CinemaSpider):
    """
    cinema info spider for http://eiga.com
    """
    name = "eiga_cinema"
    allowed_domains = ["eiga.com"]
    #start_urls = ['http://eiga.com/theater/']

    # settings for cinema_spider
    county_xpath = '//dl[@id="list_b"]//a'
    cinema_xpath = '//div[@id="pref_theaters"]//a'
    cinema_site_xpath = '//span[@id="official"]/a/@href'
    screen_text_xpath = '//th[text()="音響・設備"]/../..//td/text()'
    screen_pattern = r"^(.+)  (.+)座席 (.*)$"
    screen_name_pattern = r"\1"
    seat_number_pattern = r"\2"

    def adjust_cinema_site(self, response, site):
        """
        adjust cinema official site's url if needed
        """
        site = response.urljoin(site)
        if self.use_proxy:
            r = do_proxy_request(site, allow_redirects=False)
        else:
            r = requests.get(site, allow_redirects=False)
        return r.headers['Location']
