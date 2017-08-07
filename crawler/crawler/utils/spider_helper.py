import sys

from kazoo.handlers.threading import KazooTimeoutError
from scutils.zookeeper_watcher import ZookeeperWatcher
from crawling.spiders.redis_spider import RedisSpider


class ScrapyClusterSpider(RedisSpider):
    """
    base spider for integrating into scrapy cluster
    """
    def __init__(self, *args, **kwargs):
        self.assign_path = self.settings.get('JCSS_ZOOKEEPER_PATH')
        try:
            self.zoo_watcher = ZookeeperWatcher(
                                hosts=self.settings.get('ZOOKEEPER_HOSTS'),
                                filepath=self.assign_path + self.name,
                                config_handler=self.change_config,
                                error_handler=self.error_config,
                                pointer=False, ensure=True, valid_init=True)
        except KazooTimeoutError:
            self.logger.error(
                "{}: Could not connect to Zookeeper".format(self.name))
            sys.exit(1)

    def change_config(self, config_string):
        # TODO
        """
        if config_string and len(config_string) > 0:
            loaded_config = yaml.safe_load(config_string)
            self.logger.info("Zookeeper config changed", extra=loaded_config)
            self.load_domain_config(loaded_config)
            self.update_domain_queues()
        elif config_string is None or len(config_string) == 0:
            self.error_config("Zookeeper config wiped")

        self.create_queues()
        """
        pass

    def error_config(self, message):
        # TODO
        """
        extras = {}
        extras['message'] = message
        extras['revert_window'] = self.window
        extras['revert_hits'] = self.hits
        extras['spiderid'] = self.spider.name
        self.logger.info("Lost config from Zookeeper", extra=extras)
        # lost connection to zookeeper, reverting back to defaults
        for key in self.domain_config:
            final_key = "{name}:{domain}:queue".format(
                    name=self.spider.name,
                    domain=key)
            self.queue_dict[final_key][0].window = self.window
            self.queue_dict[final_key][0].limit = self.hits

        self.domain_config = {}
        """
        pass

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
