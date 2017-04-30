"""
Base class for spiders crawling movie showings 
"""
import unicodedata
import arrow
import scrapy
from scrapyproject.utils import ShowingDatabaseMixin


class ShowingSpider(scrapy.Spider, ShowingDatabaseMixin):
    def __init__(self, *args, **kwargs):
        """
        Prepare common settings for showing spider.
        Only movie title are raw str, others are normailized
        """
        super(ShowingSpider, self).__init__(*args, **kwargs)
        if not hasattr(self, 'movie_list'):
            self.movie_list = ['君の名は。']
        if not isinstance(self.movie_list, list):
            self.movie_list = self.movie_list.split(',')
        # scrapy doesn't allow to pass name without value
        self.crawl_all_movies = (
            True if hasattr(self, 'crawl_all_movies') else False)
        if not hasattr(self, 'cinema_list'):
            self.cinema_list = ['TOHOシネマズ 新宿']
        if not isinstance(self.cinema_list, list):
            self.cinema_list = self.cinema_list.split(',')
        # should not remove space, but normalize only
        for idx, item in enumerate(self.cinema_list):
            self.cinema_list[idx] = unicodedata.normalize('NFKC', item)
        self.crawl_all_cinemas = (
            True if hasattr(self, 'crawl_all_cinemas') else False)
        # is spider crawl showing info only or as well as booking data
        self.crawl_booking_data = (
            True if hasattr(self, 'crawl_booking_data') else False)
        # date: default tomorrow(UTC+9 timezone)
        if not hasattr(self, 'date'):
            tomorrow = arrow.now('UTC+9').shift(days=+1)
            self.date = tomorrow.format('YYYYMMDD')

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
