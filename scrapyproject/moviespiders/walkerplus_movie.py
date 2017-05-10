import scrapy
from scrapyproject.items import MovieLoader
from scrapyproject.utils import MovieDatabaseMixin


class WalkerplusMovieSpider(scrapy.Spider, MovieDatabaseMixin):
    """
    walkerplus site movie spider.
    also crawl cinema count on this week.
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
            url = movie.xpath('./dl/dd/a/@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_area)
            request.meta['title'] = title
            yield request
        next_page = response.xpath(
            '//li[@class="next"]/a/@href').extract_first()
        if next_page:
            url = response.urljoin(next_page)
            request = scrapy.Request(url, callback=self.parse)
            yield request

    def parse_area(self, response):
        area_list = response.xpath('//ul[@class="optionGroup"]//a')
        for area in area_list:
            url = area.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_sub_area)
            request.meta['title'] = response.meta['title']
            yield request

    def parse_sub_area(self, response):
        city_list = response.xpath('//ul[@class="optionGroup"]//a')
        for city in city_list:
            url = city.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_city)
            request.meta['title'] = response.meta['title']
            yield request

    def parse_city(self, response):
        movie_loader = MovieLoader(response=response)
        movie_loader.add_value('title', response.meta['title'])
        cinema_name_list = response.xpath(
            '//div[@class="movieList"]/h3/a/text()').extract()
        cinema_count = len(set(cinema_name_list))
        # cinema count is merged in pipeline
        movie_loader.add_value('current_cinema_count', cinema_count)
        yield movie_loader.load_item()
