import sys
import json

from kazoo.handlers.threading import KazooTimeoutError
from scrapy import signals
from scutils.zookeeper_watcher import ZookeeperWatcher
from crawling.spiders.redis_spider import RedisSpider


class ScrapyClusterSpider(RedisSpider):
    """
    base spider for integrating into scrapy cluster
    """
    def __init__(self, zookeeper_hosts, jcss_zookeeper_path, *args, **kwargs):
        super(ScrapyClusterSpider, self).__init__(*args, **kwargs)
        # settings is not usable in __init__ and can only be passed
        # by parameter
        self.assign_path = jcss_zookeeper_path
        self.loaded_config = {}
        try:
            self.zoo_watcher = ZookeeperWatcher(
                                hosts=zookeeper_hosts,
                                filepath=self.assign_path + self.name,
                                config_handler=self.change_config,
                                error_handler=self.error_config,
                                pointer=False, ensure=True, valid_init=True)
        except KazooTimeoutError:
            self.logger.error(
                "{}: Could not connect to Zookeeper".format(self.name))
            sys.exit(1)

    def change_config(self, config_string):
        if config_string and len(config_string) > 0:
            self.loaded_config = json.loads(config_string)
            self.logger.info(
                "{}: config changed".format(self.name),
                extra=self.loaded_config)
        elif config_string is None or len(config_string) == 0:
            self.error_config("{}: config wiped".format(self.name))

    def error_config(self, message):
        extras = {}
        extras['message'] = message
        extras['spiderid'] = self.name
        self.logger.info(
            "{}: lost config from Zookeeper".format(self.name), extra=extras)
        # lost connection to zookeeper, reverting back to defaults
        self.loaded_config = {}
        self.loaded_config['use_sample'] = False
        self.loaded_config['crawl_booking_data'] = False
        self.loaded_config['use_proxy'] = False
        self.loaded_config['require_js'] = False
        self.loaded_config['crawl_all_cinemas'] = False
        self.loaded_config['crawl_all_movies'] = False
        self.loaded_config['movie_list'] = []
        self.loaded_config['cinema_list'] = []
        self.loaded_config['date'] = '20170101'

    def parse(self, response):
        """
        enter point for response processing
        """
        self._logger.debug("crawled url {}".format(response.request.url))
        result_list = []
        if "curr_step" not in response.meta:
            self.parse_first_page(response, result_list)
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

    def closed(self, reason):
        # TODO not called in online test, don't know if called when using
        self._logger.debug("{} closed ".format(self.name), reason)
        self.zoo_watcher.close()
