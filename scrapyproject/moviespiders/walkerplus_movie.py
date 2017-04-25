import unicodedata
import scrapy
from scrapyproject.items import MovieItem
from scrapyproject.utils import MovieDatabaseMixin


class WalkerplusMovieSpider(scrapy.Spider, MovieDatabaseMixin):
    """
    walkerplus site movie spider.
    """
    name = "walkerplus_movie"
    allowed_domains = ["movie.walkerplus.com"]
    start_urls = [
        'http://movie.walkerplus.com/list/',
    ]

    def __init__(self, *args, **kwargs):
        super(WalkerplusMovieSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        """
        crawl movie data page by page
        """
        movie_list = response.xpath('//div[@class="onScreenBoxContentMovie"]')
        for movie in movie_list:
            title = movie.xpath('./h3/a/text()').extract_first()
            item = MovieItem()
            item['title'] = unicodedata.normalize('NFKC', title)
            yield item
        next_page = response.xpath(
            '//li[@class="next"]/a/@href').extract_first()
        if next_page:
            url = response.urljoin(next_page)
            request = scrapy.Request(url, callback=self.parse)
            yield request
