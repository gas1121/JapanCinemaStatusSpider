from crawling.spiders.redis_spider import RedisSpider


class ScrapyClusterSpider(RedisSpider):
    """
    base spider for integrating into scrapy cluster
    """
    def parse(self, response):
        """
        enter point for response processing
        """
        self._logger.debug("crawled url {}".format(response.request.url))
        result_list = []
        if "curr_step" not in response.meta:
            print("before")
            self.parse_first_page(response, result_list)
            print("after")
        else:
            curr_step = response.meta["curr_step"]
            next_func = getattr(self, curr_step)
            next_func(response, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_first_page(self, response, result_list):
        raise NotImplementedError(
            "parse_first_page() is required as first called parse function")

    def set_next_func(self, request, func):
        """
        set next parse function to call when response returns
        """
        request.meta["curr_step"] = func.__name__


class CinemaDatabaseMixin:
    """
    mixin to make spider use database's cinema table
    """
    use_cinema_database = True


class ShowingDatabaseMixin:
    """
    mixin to make spider use database's showing table
    """
    use_showing_database = True


class MovieDatabaseMixin:
    """
    mixin to make spider use database's movie table
    """
    use_movie_database = True


def use_cinema_database(spider):
    return hasattr(spider, "use_cinema_database")


def use_showing_database(spider):
    return hasattr(spider, "use_showing_database")


def use_movie_database(spider):
    return hasattr(spider, "use_movie_database")
