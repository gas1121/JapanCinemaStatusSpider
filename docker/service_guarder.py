"""
A guarder to ensure basic services for jcss is running so other modules can
work normally
"""
import sys
from time import sleep
import os
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from scutils.method_timer import MethodTimer


def is_kafka_prepared(kafka_host, time_out=100):
    @MethodTimer.timeout(time_out, False)
    def _is_kafka_prepared(kafka_host):
        while True:
            try:
                consumer = KafkaConsumer(
                    "jcss.test", group_id="jcss.guarder",
                    value_deserializer=lambda m: m.decode('utf-8'),
                    consumer_timeout_ms=5000,
                    auto_offset_reset='earliest',
                    bootstrap_servers=kafka_host)
                # do a read operation to ensure consumer can work
                for m in consumer:
                    pass
                consumer.close()
                return True
            except (KafkaError, OSError) as e:
                print("kafka service check failed, prepare another try")
            # sleep 5s between each try
            sleep(5)
    return _is_kafka_prepared(kafka_host)


if __name__ == '__main__':
    kafka_host = os.getenv('KAFKA_HOST', 'kafka:9092')
    time_out = os.getenv('GUARDER_TIMEOUT', 100)
    if not is_kafka_prepared(kafka_host, time_out):
        sys.exit(1)
