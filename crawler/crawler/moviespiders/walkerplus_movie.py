from crawler.items import MovieLoader
from crawler.utils import ScrapyClusterSpider


class WalkerplusMovieSpider(ScrapyClusterSpider):
    """
    walkerplus site movie spider.
    also crawl cinema count on this week.
    """
    name = "walkerplus_movie"
    allowed_domains = ["movie.walkerplus.com"]
    """
    start_urls = [
        'http://movie.walkerplus.com/list/',
    ]
    """

    def __init__(self, *args, **kwargs):
        super(WalkerplusMovieSpider, self).__init__(*args, **kwargs)

    def parse_first_page(self, response, result_list):
        """
        crawl movie data page by page
        """
        self._logger.debug("{}: parse_first_page in '{}'".format(
            self.name, response.url))
        movie_list = response.xpath('//div[@class="onScreenBoxContentMovie"]')
        for movie in movie_list:
            title = movie.xpath('./h3/a/text()').extract_first()
            url = movie.xpath('./dl/dd/a/@href').extract_first()
            request = response.follow(url, callback=self.parse)
            self.set_next_func(request, self.parse_area)
            request.meta['title'] = title
            result_list.append(request)
        next_page = response.xpath(
            '//li[@class="next"]/a/@href').extract_first()
        if next_page:
            request = response.follow(next_page, callback=self.parse)
            self.set_next_func(request, self.parse_first_page)
            result_list.append(request)

    def parse_area(self, response, result_list):
        self._logger.debug("{}: parse_area in '{}'".format(
            self.name, response.url))
        area_list = response.xpath('//ul[@class="optionGroup"]//a')
        for area in area_list:
            url = area.xpath('./@href').extract_first()
            request = response.follow(url, callback=self.parse)
            self.set_next_func(request, self.parse_sub_area)
            request.meta['title'] = response.meta['title']
            result_list.append(request)

    def parse_sub_area(self, response, result_list):
        self._logger.debug("{}: parse_sub_area in '{}'".format(
            self.name, response.url))
        city_list = response.xpath('//ul[@class="optionGroup"]//a')
        for city in city_list:
            url = city.xpath('./@href').extract_first()
            request = response.follow(url, callback=self.parse)
            self.set_next_func(request, self.parse_city)
            request.meta['title'] = response.meta['title']
            result_list.append(request)

    def parse_city(self, response, result_list):
        self._logger.debug("{}: parse_city in '{}'".format(
            self.name, response.url))
        movie_loader = MovieLoader(response=response)
        movie_loader.add_value('title', response.meta['title'])
        cinema_name_list = response.xpath(
            '//div[@class="movieList"]/h3/a/text()').extract()
        cinema_count = len(set(cinema_name_list))
        # cinema count is merged in pipeline
        movie_loader.add_value('current_cinema_count', cinema_count)
        self._logger.debug("{}: scraped item '{}'".format(
            self.name, movie_loader.load_item()))
        result_list.append(movie_loader.load_item())
