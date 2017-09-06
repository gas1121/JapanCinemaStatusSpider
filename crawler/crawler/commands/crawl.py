from optparse import OptionGroup

from scrapy.commands.crawl import Command


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
