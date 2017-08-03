import os
import json
from kazoo.client import KazooClient
from kafka_monitor import KafkaMonitor


zookeeper_host = os.getenv("ZOOKEEPER_HOST", "zookeeper:2181")
zookeeper_file_path = os.getenv(
    "JS_ZOOKEEPER_PATH", "/japancinemastatusspider/spiders/")
zookeeper_file_id = os.getenv("JS_ZOOKEEPER_ID", "all")


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
                         crawl_booking_data=False):
    """
    change spider config with zookeeper
    """
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
    # set data
    data_dict["use_sample"] = use_sample
    data_dict["crawl_booking_data"] = crawl_booking_data
    data = json.dumps(data_dict)
    zookeeper.set(file_full_path, data.encode('utf-8'))
    zookeeper.stop()
    zookeeper.close()
