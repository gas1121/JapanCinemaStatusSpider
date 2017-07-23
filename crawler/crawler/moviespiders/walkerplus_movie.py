from crawling.spiders.redis_spider import RedisSpider
from scrapyproject.items import MovieLoader
from scrapyproject.utils import MovieDatabaseMixin


class WalkerplusMovieSpider(RedisSpider, MovieDatabaseMixin):
    """
    walkerplus site movie spider.
    also crawl cinema count on this week.
    """
    name = "walkerplus_movie"
    #allowed_domains = ["movie.walkerplus.com"]
    #start_urls = [
    #    'http://movie.walkerplus.com/list/',
    #]

    def __init__(self, *args, **kwargs):
        super(WalkerplusMovieSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        """
        enter point for response process
        """
        self._logger.debug("crawled url {}".format(response.request.url))
        result_list = []
        if "curr_step" not in response.meta:
            self.parse_datapage(response, result_list)
        else:
            curr_step = response.meta["curr_step"]
            if curr_step == "datapage":
                self.parse_datapage(response, result_list)
            elif curr_step == "area":
                self.parse_area(response, result_list)
            elif curr_step == "sub_area":
                self.parse_sub_area(response, result_list)
            else:
                self.parse_city(response, result_list)
        for result in result_list:
            yield result

    def parse_datapage(self, response, result_list):
        """
        crawl movie data page by page
        """
        self._logger.debug("{}: parse_datapage in '{}'".format(
            self.name, response.url))
        movie_list = response.xpath('//div[@class="onScreenBoxContentMovie"]')
        for movie in movie_list:
            title = movie.xpath('./h3/a/text()').extract_first()
            url = movie.xpath('./dl/dd/a/@href').extract_first()
            request = response.follow(url, callback=self.parse)
            request.meta['curr_step'] = "area"
            request.meta['title'] = title
            result_list.append(request)
            return
        next_page = response.xpath(
            '//li[@class="next"]/a/@href').extract_first()
        if next_page:
            request = response.follow(next_page, callback=self.parse)
            request.meta['curr_step'] = "datapage"
            result_list.append(request)

    def parse_area(self, response, result_list):
        self._logger.debug("{}: parse_area in '{}'".format(
            self.name, response.url))
        area_list = response.xpath('//ul[@class="optionGroup"]//a')
        for area in area_list:
            url = area.xpath('./@href').extract_first()
            request = response.follow(url, callback=self.parse)
            request.meta['curr_step'] = "sub_area"
            request.meta['title'] = response.meta['title']
            result_list.append(request)
            return

    def parse_sub_area(self, response, result_list):
        self._logger.debug("{}: parse_sub_area in '{}'".format(
            self.name, response.url))
        city_list = response.xpath('//ul[@class="optionGroup"]//a')
        for city in city_list:
            url = city.xpath('./@href').extract_first()
            request = response.follow(url, callback=self.parse)
            request.meta['curr_step'] = "city"
            request.meta['title'] = response.meta['title']
            result_list.append(request)
            return

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
