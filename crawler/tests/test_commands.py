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
        self.assertTrue('zookeeper_hosts' in opts.spargs)
        self.assertTrue('jcss_zookeeper_path' in opts.spargs)

        opts.all_spiders = True
        cmd.run(args, opts)
        cmd.crawler_process.crawl.assert_any_call(
            'aeon', zookeeper_hosts=opts.spargs['zookeeper_hosts'],
            jcss_zookeeper_path=opts.spargs['jcss_zookeeper_path'])
