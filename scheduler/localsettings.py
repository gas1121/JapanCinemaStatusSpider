# THIS FILE SHOULD STAY IN SYNC WITH /kafka-monitor/settings.py

import os
def str2bool(v):
    return str(v).lower() in ('true', '1') if type(v) == str else bool(v)

# Redis host information
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Kafka server information
KAFKA_HOSTS = [x.strip() for x in os.getenv('KAFKA_HOSTS', 'kafka:9092').split(',')]
KAFKA_INCOMING_TOPIC = os.getenv('KAFKA_INCOMING_TOPIC', 'demo.incoming')
KAFKA_GROUP = os.getenv('KAFKA_GROUP', 'demo-group')
KAFKA_FEED_TIMEOUT = 10
KAFKA_CONSUMER_AUTO_OFFSET_RESET = 'earliest'
KAFKA_CONSUMER_TIMEOUT = 50
KAFKA_CONSUMER_COMMIT_INTERVAL_MS = 5000
KAFKA_CONSUMER_AUTO_COMMIT_ENABLE = True
KAFKA_CONSUMER_FETCH_MESSAGE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
KAFKA_PRODUCER_BATCH_LINGER_MS = 25  # 25 ms before flush
KAFKA_PRODUCER_BUFFER_BYTES = 4 * 1024 * 1024  # 4MB before blocking

# plugin setup
PLUGIN_DIR = 'plugins/'
PLUGINS = {
    'plugins.scraper_handler.ScraperHandler': 100,
    'plugins.action_handler.ActionHandler': 200,
    'plugins.stats_handler.StatsHandler': 300,
    'plugins.zookeeper_handler.ZookeeperHandler': 400,
}

# logging setup
LOGGER_NAME = 'kafka-monitor'
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_FILE = 'kafka_monitor.log'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUPS = 5
LOG_STDOUT = str2bool(os.getenv('LOG_STDOUT', True))
LOG_JSON = str2bool(os.getenv('LOG_JSON', False))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# stats setup
STATS_TOTAL = str2bool(os.getenv('STATS_TOTAL', True))
STATS_PLUGINS = str2bool(os.getenv('STATS_PLUGINS', True))
STATS_CYCLE = 5
STATS_DUMP = 60
# from time variables in scutils.stats_collector class
STATS_TIMES = [
    'SECONDS_15_MINUTE',
    'SECONDS_1_HOUR',
    'SECONDS_6_HOUR',
    'SECONDS_12_HOUR',
    'SECONDS_1_DAY',
    'SECONDS_1_WEEK',
]

# main thread sleep time
SLEEP_TIME = 0.01
HEARTBEAT_TIMEOUT = 120

# JapanCinemaStatusSpider Settings
# ~~~~~~~~~~~~~~~

# clear showing and showing booking data when scheduler starts
JCSS_CLEAR_SHOWING_AT_INIT = os.getenv('JCSS_CLEAR_SHOWING_AT_INIT', False)

# kafka topic that crawled item is sended to
JCSS_DATA_PROCESSOR_TOPIC = os.getenv(
    'JCSS_DATA_PROCESSOR_TOPIC', 'jcss.data_processor')

# zookeeper host
JCSS_ZOOKEEPER_HOST = os.getenv("ZOOKEEPER_HOST", "zookeeper:2181")

# zookeeper path to store spider config
JCSS_ZOOKEEPER_PATH = os.getenv(
    "JCSS_ZOOKEEPER_PATH", "/japancinemastatusspider/spiders/")

# default cinema for each cinema chain
JCSS_DEFAULT_CINEMAS = {
    "aeon": ["イオンシネマ板橋"],
    "toho_v2": ["TOHOシネマズ 新宿"],
    "united": ["ユナイテッド・シネマとしまえん"],
    "movix": ["新宿ピカデリー"],
    "kinezo": ["新宿バルト9"],
    "cinema109": ["109シネマズ湘南"],
    "korona": ["青森コロナシネマワールド"],
    "cinemasunshine": ["シネマサンシャイン池袋"],
    "forum": ["フォーラム八戸"],
}

# default movies to crawl
JCSS_DEFAULT_MOVIES = ['君の名は。']

# sample cinema for a quick showing crawl job
JCSS_SAMPLE_CINEMAS = [
    "TOHOシネマズ府中", "TOHOシネマズ海老名", "TOHOシネマズ西宮OS",
    "TOHOシネマズ仙台", "MOVIX仙台", "MOVIX三好", "MOVIXさいたま"
]
