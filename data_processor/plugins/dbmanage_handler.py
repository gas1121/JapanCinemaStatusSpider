from kafka_monitor_plugins.base_handler import BaseHandler


class DbManageHandler(BaseHandler):
    schema = "dbmanage_schema.json"

    def setup(self, settings):
        pass

    def handle(self, dict):
        pass
