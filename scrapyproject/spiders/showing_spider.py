"""
Base class for spiders crawling movie showings 
"""
import unicodedata
import arrow
import scrapy
from scrapyproject.utils.spider_helper import ShowingsDatabaseMixin


class ShowingSpider(scrapy.Spider, ShowingsDatabaseMixin):
    def set_config(self, config):
        """
        Prepare common settings for showing spider.
        Only movie title are raw str, others are normailized
        """
        config['movie_list'] = getattr(self, 'movie_list', ['君の名は。'])
        if not isinstance(config['movie_list'], list):
            config['movie_list'] = config['movie_list'].split(',')
        # scrapy doesn't allow to pass name without value
        config['crawl_all_movies'] = (
            True if hasattr(self, 'crawl_all_movies') else False)
        config['crawl_all_cinemas'] = (
            True if hasattr(self, 'crawl_all_cinemas') else False)
        config['cinema_list'] = getattr(self, 'cinema_list',
                                        ['TOHOシネマズ 新宿'])
        if not isinstance(config['cinema_list'], list):
            config['cinema_list'] = config['cinema_list'].split(',')
        # should not remove space, but normalize only
        for idx, item in enumerate(config['cinema_list']):
            config['cinema_list'][idx] = unicodedata.normalize('NFKC', item)
        # date: default tomorrow
        tomorrow = arrow.now().shift(days=+1)
        config['date'] = getattr(self, 'date', tomorrow.format('YYYYMMDD'))

    def is_cinema_crawl(self, cinema_names, config):
        """
        check if current cinema should be crawled
        """
        if config['crawl_all_cinemas']:
            return True
        # replace full width text before compare
        for curr_name in cinema_names:
            used_name = unicodedata.normalize('NFKC', curr_name)
            if used_name in config['cinema_list']:
                return True
        return False
