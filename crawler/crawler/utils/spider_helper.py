import sys
import json
import uuid

from kazoo.handlers.threading import KazooTimeoutError
from scutils.zookeeper_watcher import ZookeeperWatcher
from crawling.spiders.redis_spider import RedisSpider
from scrapy.utils.project import get_project_settings


class ScrapyClusterSpider(RedisSpider):
    """
    base spider for integrating into scrapy cluster
    """
    def __init__(self, *args, **kwargs):
        super(ScrapyClusterSpider, self).__init__(*args, **kwargs)
        settings = get_project_settings()
        self.set_default_config()
        # create a unique uuid for each spider
        self.uuid = str(uuid.uuid4())
        # set up zookeeper watcher for spider config
        zookeeper_hosts = settings.get('ZOOKEEPER_HOSTS')
        self.assign_path = settings.get('JCSS_ZOOKEEPER_PATH')
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
        self.set_default_config()

    def set_default_config(self):
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
        self._logger.debug("{} closed: {}".format(self.name, reason))
        self.zoo_watcher.close()
