import unittest
from mock import MagicMock, patch

from crawler.commands.crawl import CrawlCommand


class TestCrawlCommand(unittest.TestCase):
    @patch("crawler.commands.crawl.Command")
    def test_run(self, Command_mock):
        args = MagicMock()
        opts = MagicMock()
        opts.spargs = {}
        opts.all_spiders = False
        cmd = CrawlCommand()
        cmd.crawler_process = MagicMock()
        cmd.run(args, opts)
        Command_mock.run.assert_called_once_with(cmd, args, opts)

        opts.all_spiders = True
        cmd.run(args, opts)
        cmd.crawler_process.crawl.assert_any_call('aeon')
