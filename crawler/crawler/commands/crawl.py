import sys
from optparse import OptionGroup

from kazoo.client import KazooClient
from kazoo.exceptions import KazooException
from kazoo.handlers.threading import KazooTimeoutError
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from scrapy.commands.crawl import Command
from scrapy.utils.project import get_project_settings


class CrawlCommand(Command):
    def short_desc(self):
        return "Override default crawl command to support run multiple spiders"

    def long_desc(self):
        return """Override default crawl command as we neeed to support run
multiple spiders in single process"""

    def add_options(self, parser):
        Command.add_options(self, parser)
        # custom options
        group = OptionGroup(parser, "Custom Options")
        group.add_option("--all_spiders", action="store_true", default=False,
                         help="run all spiders together")
        parser.add_option_group(group)

    def process_options(self, args, opts):
        Command.process_options(self, args, opts)

    def run(self, args, opts):
        # check zookeeper and kafka connection, exit if fail to connect
        if not self.is_remote_prepared():
            sys.exit(1)
        opts.spargs = {}
        if opts.all_spiders:
            self.run_multiple_spiders(args, opts)
        else:
            Command.run(self, args, opts)

    def run_multiple_spiders(self, args, opts):
        self.crawler_process.crawl('aeon', **opts.spargs)
        self.crawler_process.crawl('toho_v2', **opts.spargs)
        self.crawler_process.crawl('united', **opts.spargs)
        self.crawler_process.crawl('movix', **opts.spargs)
        self.crawler_process.crawl('kinezo', **opts.spargs)
        self.crawler_process.crawl('cinema109', **opts.spargs)
        self.crawler_process.crawl('korona', **opts.spargs)
        self.crawler_process.crawl('cinemasunshine', **opts.spargs)
        self.crawler_process.crawl('forum', **opts.spargs)
        self.crawler_process.crawl('walkerplus_movie', **opts.spargs)
        self.crawler_process.crawl('walkerplus_cinema', **opts.spargs)
        self.crawler_process.start()
        return

    def is_remote_prepared(self):
        """
        check if kafka and zookeeper is prepared
        """
        settings = get_project_settings()
        # ensure zookeeper connection
        zookeeper_host = settings.get('ZOOKEEPER_HOSTS')
        zk = KazooClient(hosts=zookeeper_host)
        prepared = False
        try:
            zk.start()
            prepared = True
        except (KazooException, KazooTimeoutError) as e:
            prepared = False
        finally:
            zk.stop()
        if not prepared:
            return False
        # ensure kafka connection
        kafka_host = settings.get('KAFKA_HOSTS')
        try:
            consumer = KafkaConsumer(
                "jcss.test", group_id="demo-id", bootstrap_servers=kafka_host)
            prepared = True
            consumer.close()
        except KafkaError as e:
            prepared = False
        return prepared
