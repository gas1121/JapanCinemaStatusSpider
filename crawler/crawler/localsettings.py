# THIS FILE SHOULD STAY IN SYNC WITH /crawler/crawling/settings.py

from __future__ import absolute_import
# This file houses all default settings for the Crawler
# to override please use a custom localsettings.py file
import os
def str2bool(v):
    return str(v).lower() in ('true', '1') if type(v) == str else bool(v)

# Scrapy Cluster Settings
# ~~~~~~~~~~~~~~~~~~~~~~~

# Specify the host and port to use when connecting to Redis.
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Kafka server information
KAFKA_HOSTS = [x.strip() for x in os.getenv('KAFKA_HOSTS', 'kafka:9092').split(',')]
KAFKA_TOPIC_PREFIX = os.getenv('KAFKA_TOPIC_PREFIX', 'demo')
KAFKA_APPID_TOPICS = str2bool(os.getenv('KAFKA_APPID_TOPICS', False))
# base64 encode the html body to avoid json dump errors due to malformed text
KAFKA_BASE_64_ENCODE = str2bool(os.getenv('KAFKA_BASE_64_ENCODE', False))
KAFKA_PRODUCER_BATCH_LINGER_MS = 25  # 25 ms before flush
KAFKA_PRODUCER_BUFFER_BYTES = 4 * 1024 * 1024  # 4MB before blocking

ZOOKEEPER_ASSIGN_PATH = '/scrapy-cluster/crawler/'
ZOOKEEPER_ID = 'all'
ZOOKEEPER_HOSTS = os.getenv('ZOOKEEPER_HOSTS', 'zookeeper:2181')

PUBLIC_IP_URL = 'http://ip.42.pl/raw'
IP_ADDR_REGEX = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'

# Don't cleanup redis queues, allows to pause/resume crawls.
SCHEDULER_PERSIST = True

# seconds to wait between seeing new queues, cannot be faster than spider_idle time of 5
SCHEDULER_QUEUE_REFRESH = 10

# throttled queue defaults per domain, x hits in a y second window
QUEUE_HITS = int(os.getenv('QUEUE_HITS', 60))
QUEUE_WINDOW = int(os.getenv('QUEUE_WINDOW', 70))

# we want the queue to produce a consistent pop flow
QUEUE_MODERATED = str2bool(os.getenv('QUEUE_MODERATED', True))

# how long we want the duplicate timeout queues to stick around in seconds
DUPEFILTER_TIMEOUT = int(os.getenv('DUPEFILTER_TIMEOUT', 600))

# how often to refresh the ip address of the scheduler
SCHEDULER_IP_REFRESH = 60

# whether to add depth >= 1 blacklisted domain requests back to the queue
SCHEDULER_BACKLOG_BLACKLIST = True

'''
----------------------------------------
The below parameters configure how spiders throttle themselves across the cluster
All throttling is based on the TLD of the page you are requesting, plus any of the
following parameters:

Type: You have different spider types and want to limit how often a given type of
spider hits a domain

IP: Your crawlers are spread across different IP's, and you want each IP crawler clump
to throttle themselves for a given domain

Combinations for any given Top Level Domain:
None - all spider types and all crawler ips throttle themselves from one tld queue
Type only - all spiders throttle themselves based off of their own type-based tld queue,
    regardless of crawler ip address
IP only - all spiders throttle themselves based off of their public ip address, regardless
    of spider type
Type and IP - every spider's throttle queue is determined by the spider type AND the
    ip address, allowing the most fined grained control over the throttling mechanism
'''
# add Spider type to throttle mechanism
SCHEDULER_TYPE_ENABLED = str2bool(os.getenv('SCHEDULER_TYPE_ENABLED', True))

# add ip address to throttle mechanism
SCHEDULER_IP_ENABLED = str2bool(os.getenv('SCHEDULER_IP_ENABLED', True))
'''
----------------------------------------
'''

# how many times to retry getting an item from the queue before the spider is considered idle
SCHEUDLER_ITEM_RETRIES = 3

# how long to keep around stagnant domain queues
SCHEDULER_QUEUE_TIMEOUT = int(os.getenv('SCHEDULER_QUEUE_TIEOUT', 3600))

# log setup scrapy cluster crawler
SC_LOGGER_NAME = 'sc-crawler'
SC_LOG_DIR = os.getenv('SC_LOG_DIR', 'logs')
SC_LOG_FILE = 'sc_crawler.log'
SC_LOG_MAX_BYTES = 10 * 1024 * 1024
SC_LOG_BACKUPS = 5
SC_LOG_STDOUT = str2bool(os.getenv('SC_LOG_STDOUT', True))
SC_LOG_JSON = str2bool(os.getenv('SC_LOG_JSON', False))
SC_LOG_LEVEL = os.getenv('SC_LOG_LEVEL', 'INFO')


# stats setup
STATS_STATUS_CODES = str2bool(os.getenv('STATS_STATUS_CODES', True))
STATS_RESPONSE_CODES = [
    200,
    404,
    403,
    504,
]
STATS_CYCLE = 5
# from time variables in scutils.stats_collector class
STATS_TIMES = [
    'SECONDS_15_MINUTE',
    'SECONDS_1_HOUR',
    'SECONDS_6_HOUR',
    'SECONDS_12_HOUR',
    'SECONDS_1_DAY',
    'SECONDS_1_WEEK',
]

# Scrapy Settings
# ~~~~~~~~~~~~~~~
#DOWNLOADER_CLIENTCONTEXTFACTORY = 'crawling.contextfactory.MyClientContextFactory'

# Scrapy settings for distributed_crawling project
#
BOT_NAME = 'crawler'

SPIDER_MODULES = [
    'crawler.cinemaspiders',
    'crawler.moviespiders',
    'crawler.showingspiders',
]
NEWSPIDER_MODULE = 'crawler.showingspiders'

# Enables scheduling storing requests queue in redis.
SCHEDULER = "crawling.distributed_scheduler.DistributedScheduler"



# turn off: Store scraped item in redis for post-processing.
ITEM_PIPELINES = {
    # 'crawling.pipelines.KafkaPipeline': 100,
    # 'crawling.pipelines.LoggingBeforePipeline': 1,
    # send crawled item to target kafka topic for post processing
    'crawler.pipelines.CrawledItemToKafkaPipiline': 300,
}

SPIDER_MIDDLEWARES = {
    # engine side

    # copy all meta from input reponse to output request expect changed
    # in spider
    'crawling.meta_passthrough_middleware.MetaPassthroughMiddleware': 100,
    # record response status code
    'crawling.redis_stats_middleware.RedisStatsMiddleware': 101,
    # reset some scrapy provided meta to default value
    'crawler.spidermiddlewares.reset_meta.ResetMetaMiddleware': 103,

    # spider side
}

DOWNLOADER_MIDDLEWARES = {
    # Handle timeout retries with the redis scheduler and logger
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'crawling.redis_retry_middleware.RedisRetryMiddleware': 510,
    # exceptions processed in reverse order
    'crawling.log_retry_middleware.LogRetryMiddleware': 520,
    # custom cookies to not persist across crawl requests
    # this middleware prevents using of jar as request may come from
    # another spider, so cookies is added to header in spider middleware
    # turn off as we use redis to store cookies
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'crawling.custom_cookies.CustomCookiesMiddleware': None,
    # turn off as js engine currently not used
    'crawler.middlewares.selenium.SeleniumDownloaderMiddleware': None,
    # get cookies from redis to support cluster usage
    'crawler.middlewares.cookies.RedisCookiesMiddleware': 700,
    # provide optional proxy that support socks5
    'crawler.middlewares.proxy.ProxyDownloaderMiddleware': 751,
}

# Disable the built in logging in production
LOG_ENABLED = str2bool(os.getenv('LOG_ENABLED', False))

# Allow all return codes
HTTPERROR_ALLOW_ALL = True

RETRY_TIMES = 3

DOWNLOAD_TIMEOUT = 10

# Avoid in-memory DNS cache. See Advanced topics of docs for info
DNSCACHE_ENABLED = True

# JapanCinemaStatusSpider Settings
# ~~~~~~~~~~~~~~~

# kafka topic that crawled item is sended to
JCSS_DATA_PROCESSOR_TOPIC = os.getenv(
    'JCSS_DATA_PROCESSOR_TOPIC', 'jcss.data_processor')

# zookeeper path to store spider config
JCSS_ZOOKEEPER_PATH = os.getenv(
    "JCSS_ZOOKEEPER_PATH", "/japancinemastatusspider/spiders/")

# make timeout a bit longer
DOWNLOAD_TIMEOUT = 60

# add command to crawl showing data together
COMMANDS_MODULE = 'crawler.commands'

# TODO temporarily enable scrapy log for debug
import arrow
SC_LOG_FILE = str(arrow.now().format('YYYYMMDD HH mm ss')) + ".log"
LOG_ENABLED = True
LOG_LEVEL = "DEBUG"
LOG_FILE = SC_LOG_DIR + "/" + SC_LOG_FILE
SC_LOG_STDOUT = False
SC_LOG_LEVEL = "DEBUG"

# TODO previous settings need review
# Obey robots.txt rules
#ROBOTSTXT_OBEY = False

# add user agent
"""
DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Language': 'en',
   'User-Agent': 'Scrapy'
}
"""

# also retry for 404 request
#RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 404]
