from crawler.utils import sc_log_setup


class DebugSingleOutputMiddleware(object):
    """
    Middleware to limit spider to produce one request when parse page
    so we can run spider on test environment
    """
    def __init__(self, settings):
        self.setup(settings)

    def setup(self, settings):
        '''
        Does the actual setup of the middleware
        '''
        # set up the default sc logger
        self.logger = sc_log_setup(settings)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_spider_output(self, response, result, spider):
        '''
        only pick first item or request from spider's output
        '''
        self.logger.debug("{} processing".format(self.__class__.__name__))
        yield next(result)
