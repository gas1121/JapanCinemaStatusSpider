import os
import json

import arrow
from kazoo.client import KazooClient
from kafka_monitor import KafkaMonitor


zookeeper_host = os.getenv("ZOOKEEPER_HOST", "zookeeper:2181")
zookeeper_file_path = os.getenv(
    "JS_ZOOKEEPER_PATH", "/japancinemastatusspider/spiders/")
zookeeper_file_id = os.getenv("JS_ZOOKEEPER_ID", "all")


sample_cinema = ["TOHOシネマズ府中", "TOHOシネマズ海老名",
                 "TOHOシネマズ西宮OS", "TOHOシネマズ仙台",
                 "MOVIX仙台", "MOVIX三好", "MOVIXさいたま"]


def create_domain_throttle_job(url, hits=20, window=60, scale=1.0,
                               uuid="abc123", appid="testapp",
                               action="domain-update"):
    data = {}
    data["url"] = url
    data["hits"] = hits
    data["window"] = window
    data["scale"] = scale
    data["uuid"] = uuid
    data["appid"] = appid
    data["action"] = action
    return data


def create_crawl_job(url, spiderid, appid="testapp", crawlid="abc123"):
    data = {}
    data["url"] = url
    data["appid"] = appid
    data["crawlid"] = crawlid
    data["spiderid"] = spiderid
    return data


def send_job_to_kafka(topic, job):
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.setup()
    # set kafka topic
    kafka_monitor.settings['KAFKA_INCOMING_TOPIC'] = topic
    kafka_monitor.logger.info("begin to send job to kafka", job)
    kafka_monitor.feed(job)
    kafka_monitor.close()
    kafka_monitor.logger.info("job done")


def change_spider_config(spiderid=None, use_sample=False,
                         crawl_booking_data=False, use_proxy=False,
                         require_js=False, crawl_all_cinemas=False,
                         crawl_all_movies=False, movie_list=['君の名は。'],
                         cinema_list=['TOHOシネマズ海老名'], date=None):
    """
    change spider config with zookeeper
    """
    # TODO do all spider config by zookeeper
    zookeeper = KazooClient(hosts=zookeeper_host)
    zookeeper.start()
    file_name = zookeeper_file_id
    if spiderid:
        file_name = spiderid
    file_full_path = zookeeper_file_path + file_name
    # read data if already exists
    data_dict = {}
    if zookeeper.exists(file_full_path):
        old_data = zookeeper.get(file_full_path)[0]
        data_dict = json.loads(old_data.decode('utf-8'))
    else:
        zookeeper.ensure_path(file_full_path)
    # set up spider config
    data_dict["use_sample"] = use_sample
    data_dict["crawl_booking_data"] = crawl_booking_data
    data_dict["use_proxy"] = use_proxy
    data_dict["require_js"] = require_js
    data_dict["crawl_all_cinemas"] = crawl_all_cinemas
    data_dict["crawl_all_movies"] = crawl_all_movies
    data_dict["movie_list"] = movie_list
    data_dict["cinema_list"] = sample_cinema if use_sample else cinema_list
    # set date to tomorrow as default
    data_dict["date"] = arrow.now().format('YYYYMMDD') if not date else date
    data = json.dumps(data_dict)

    zookeeper.set(file_full_path, data.encode('utf-8'))
    zookeeper.stop()
    zookeeper.close()
