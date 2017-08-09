import unittest
import unicodedata

import crawler.items as items


class TestMovie(unittest.TestCase):
    def test_movie_loader(self):
        title = '\ufb01'
        result = unicodedata.normalize('NFKC', title)
        loader = items.MovieLoader()
        loader.add_value('title', title)
        item = loader.load_item()
        self.assertEqual(item['title'], result)
