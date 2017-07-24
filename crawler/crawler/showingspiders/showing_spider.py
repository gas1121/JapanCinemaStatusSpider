"""
Base class for spiders crawling movie showings 
"""
import unicodedata
import arrow
import scrapy
from crawler.utils import ShowingDatabaseMixin


default_cinema = {
    "aeon": "イオンシネマ板橋",
    "toho_v2": "TOHOシネマズ 新宿",
    "united": "ユナイテッド・シネマとしまえん",
    "movix": "新宿ピカデリー",
    "kinezo": "新宿バルト9",
    "cinema109": "109シネマズ湘南",
    "korona": "青森コロナシネマワールド",
    "cinemasunshine": "シネマサンシャイン池袋",
    "forum": "フォーラム八戸",
}


class ShowingSpider(scrapy.Spider, ShowingDatabaseMixin):
    def __init__(self, *args, **kwargs):
        """
        Prepare common settings for showing spider.
        All strings are normailized
        """
        super(ShowingSpider, self).__init__(*args, **kwargs)
        # if movie list is empty, add default movie for spider
        if not self.movie_list:
            self.movie_list.append('君の名は。')
        # if cinema list is empty, add default cinema for spider
        if not self.cinema_list:
            self.cinema_list.append(default_cinema[self.name])
        # normalize cinema and movie name
        for idx, item in enumerate(self.movie_list):
            self.movie_list[idx] = unicodedata.normalize('NFKC', item)
        for idx, item in enumerate(self.cinema_list):
            self.cinema_list[idx] = unicodedata.normalize('NFKC', item)

    def is_cinema_crawl(self, cinema_names):
        """
        check if current cinema should be crawled
        """
        if self.crawl_all_cinemas:
            return True
        # replace full width text before compare
        for curr_name in cinema_names:
            used_name = unicodedata.normalize('NFKC', curr_name)
            if used_name in self.cinema_list:
                return True
        return False

    def is_movie_crawl(self, movie_names):
        """
        check if current movie should be crawled
        """
        # any(curr_title in title for curr_title in movie_list)
        if self.crawl_all_movies:
            return True
        for target_name in self.movie_list:
            if not target_name:
                continue
            for compare_name in movie_names:
                if target_name in compare_name:
                    return True
        return False

    def get_time_from_text(self, hours, minutes):
        """
        generate arrow object from given day and time text

        as time like 24:40 can not be directly parsed, we need shift time
        properly

        :param show_day: arrow object represent of 00:00 at show day.
        """
        time = arrow.get(self.date, 'YYYYMMDD').replace(tzinfo='UTC+9')
        time = time.shift(hours=hours, minutes=minutes)
        return time
