import unittest
from mock import MagicMock, patch

from kafka.errors import KafkaTimeoutError

from crawler.items.movie import Movie
from crawler.pipelines import CrawledItemToKafkaPipiline


class TestCrawledItemToKafkaPipiline(unittest.TestCase):
    def setUp(self):
        self.topic = "test"
        self.pipe = CrawledItemToKafkaPipiline(
            MagicMock(), MagicMock(), self.topic)
        self.pipe.producer.send = MagicMock()
        self.pipe._get_time = MagicMock(return_value='the time')

    @patch('traceback.format_exc', return_value='traceback')
    def test_process_item(self, format_exc_mock):
        item = Movie(title="test", current_cinema_count=1)
        spider = MagicMock()
        spider.name = "test-spider"

        self.pipe.process_item(item, spider)
        expected = '{"current_cinema_count":1,"title":"test"}'
        self.pipe.producer.send.assert_called_once_with(self.topic, expected)
        self.pipe.producer.send.reset_mock()

        # item fail to send
        self.pipe.producer.send = MagicMock(
            side_effect=KafkaTimeoutError('bad kafka'))
        self.pipe.process_item(item, spider)
