"""
Base class for spiders crawling movie showings 
"""
import unicodedata
import arrow
import scrapy
from scrapyproject.utils.spider_helper import ShowingsDatabaseMixin


class ShowingSpider(scrapy.Spider, ShowingsDatabaseMixin):
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
        # date: default tomorrow
        if not hasattr(self, 'date'):
            tomorrow = arrow.now().shift(days=+1)
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
