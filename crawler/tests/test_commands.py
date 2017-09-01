import unittest
from mock import MagicMock, patch

from kazoo.handlers.threading import KazooTimeoutError
from kafka.errors import KafkaError
from crawler.commands.crawl import CrawlCommand


class TestCrawlCommand(unittest.TestCase):
    @patch("crawler.commands.crawl.Command")
    def test_run(self, Command_mock):
        args = MagicMock()
        opts = MagicMock()
        opts.spargs = {}
        opts.all_spiders = False
        cmd = CrawlCommand()
        cmd.is_remote_prepared = MagicMock(return_value=True)
        cmd.crawler_process = MagicMock()
        cmd.run(args, opts)
        Command_mock.run.assert_called_once_with(cmd, args, opts)

        opts.all_spiders = True
        cmd.run(args, opts)
        cmd.crawler_process.crawl.assert_any_call('aeon')

    @patch("crawler.commands.crawl.KafkaConsumer")
    @patch("crawler.commands.crawl.KazooClient")
    @patch("crawler.commands.crawl.get_project_settings")
    @patch("crawler.commands.crawl.Command")
    def test_is_remote_prepared(
            self, Command_mock, get_project_settings_mock, KazooClient_mock,
            KafkaConsumer_mock):
        cmd = CrawlCommand()
        result = cmd.is_remote_prepared()
        self.assertTrue(result)

        KazooClient_mock().start = MagicMock(
            side_effect=KazooTimeoutError())
        result = cmd.is_remote_prepared()
        self.assertFalse(result)

        KazooClient_mock().start = MagicMock()
        KafkaConsumer_mock.side_effect = KafkaError()
        result = cmd.is_remote_prepared()
        self.assertFalse(result)
