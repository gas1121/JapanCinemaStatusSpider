from kafka_monitor import KafkaMonitor


if __name__ == '__main__':
    kafka_monitor = KafkaMonitor("localsettings.py")
    kafka_monitor.setup()
    try:
        kafka_monitor.run()
    finally:
        kafka_monitor.logger.info("Closing Kafka Monitor")
        kafka_monitor.close()
