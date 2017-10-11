import unittest
from mock import MagicMock, patch

from kafka.errors import KafkaTimeoutError

from crawler.items.showing_booking import ShowingBooking
from crawler.items.showing import Showing
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
        item1 = Movie(title='Your Name.', current_cinema_count=15)
        item2 = ShowingBooking(
            book_status="SoldOut", showing=Showing(title="Your Name."))
        spider = MagicMock()
        spider.name = "test-spider"

        self.pipe.process_item(item1, spider)
        expected = '{"current_cinema_count":15,"title":"Your Name."}'
        self.pipe.producer.send.assert_called_once_with(self.topic, expected)
        self.pipe.producer.send.reset_mock()
        self.pipe.process_item(item2, spider)
        expected = '{"book_status":"SoldOut","showing":{"title":"Your Name."}}'
        self.pipe.producer.send.assert_called_once_with(self.topic, expected)
        self.pipe.producer.send.reset_mock()

        # item fail to send
        self.pipe.producer.send = MagicMock(
            side_effect=KafkaTimeoutError('bad kafka'))
        self.pipe.process_item(item1, spider)
