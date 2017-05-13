# -*- coding: utf-8 -*-
import unicodedata
import re
from scrapyproject.items import standardize_screen_name
from scrapyproject.cinemaspiders.cinema_spider import CinemaSpider
from scrapyproject.utils import extract_seat_number


class WalkerplusCinemaSpider(CinemaSpider):
    """
    cinema info spider for http://movie.walkerplus.com/
    """
    name = "walkerplus_cinema"
    allowed_domains = ["movie.walkerplus.com"]
    start_urls = ['http://movie.walkerplus.com/theater/']

    # settings for cinema_spider, sone are not used as we will override
    # screen data extract function
    county_xpath = '//div[@id="rootAreaList"]//a'
    cinema_xpath = '//div[@id="theaterList_wrap"]//li/a'
    cinema_site_xpath = '//a[text()="映画館公式サイト"]/@href'

    def is_county_crawl(self, county):
        """
        filter useless county
        """
        county_name = county.xpath('.//text()').extract_first()
        if county_name in ['札幌', '道央', '道北', '道南', '道東']:
            return False
        else:
            return True

    def adjust_cinema_url(self, url):
        """
        adjust cinema page's url if needed
        """
        return url.replace('schedule.html', '')

    def is_cinema_crawl(self, cinema_name):
        return True

    def parse_screen_data(self, response):
        """
        override as screen text on this site is a bit different
        """
        screen_raw_texts = response.xpath(
            '//th[text()="座席数"]/../td/text()').extract()
        formatted_raw_texts = []
        for raw_text in screen_raw_texts:
            raw_text = unicodedata.normalize('NFKC', raw_text)
            raw_text = raw_text.strip()
            if raw_text != "":
                formatted_raw_texts.append(raw_text)
        if len(formatted_raw_texts) > 1:
            # have detail screen data text
            all_raw_text = formatted_raw_texts[1]
        else:
            # only have global screen data text
            all_raw_text = formatted_raw_texts[0]
        screen = {}
        screen_count = 0
        total_seats = 0
        match = re.findall(r"\d*席* ?(.+?)・(\d+)", all_raw_text)
        # if no match found, use pattern for single screen
        if not match:
            match = re.findall(r"(\d+)", all_raw_text)
            if match:
                match[0] = ("スクリーン", match[0])
        # special case for "TOHOシネマズ八千代緑が丘"
        # "プレミアスクリーン80" missing "・"
        if response.meta['cinema_name'] == "TOHOシネマズ八千代緑が丘":
            extra_match = re.findall(r"プレミアスクリーン(\d+)", all_raw_text)
            if extra_match:
                match.append(("プレミアスクリーン", extra_match[0]))
        # special case for "新宿ピカデリー"
        if response.meta['cinema_name'] == "新宿ピカデリー":
            match.append(("プラチナ", "26"))
        # special case for "109シネマズ二子玉川"
        if response.meta['cinema_name'] == "109シネマズ二子玉川":
            match.append(("グランドEXE", "12"))
            for i in range(len(match)):
                if match[i][0] == "スクリーン7":
                    seat_count = extract_seat_number(match[i][1])
                    match[i] = (match[i][0], str(seat_count-12))
        # TODO special case for united cinema 3D screen
        # TODO special case for united cinema YEBISUGARDENCINEMA en/jp
        # TODO make special case only need to modify one place
        # TODO special case for korona 4DX screen
        # TODO special case for cinemasunshine BESTIA and 4DX screen
        # TODO special case for aeon d-box seat
        # TODO special case for aeon イオンシネマ岡山 screen1
        # TODO special case for フォーラム盛岡 screen 8 9
        for screen_name, seat_str in match:
            screen_name = standardize_screen_name(
                screen_name, response.meta['cinema_name'])
            # add cinema name into screen name to avoid conflict for
            # sub cinemas
            screen_name = response.meta['cinema_name'] + "#" + screen_name
            seat_count = extract_seat_number(seat_str)
            screen_count += 1
            total_seats += seat_count
            screen[screen_name] = str(seat_count)
        return screen, screen_count, total_seats
