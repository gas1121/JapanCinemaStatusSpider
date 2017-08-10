import unittest
import unicodedata

import crawler.items as items


class TestItems(unittest.TestCase):
    def test_standardize_cinema_name(self):
        name = items.standardize_cinema_name(' \ufb01')
        self.assertEqual(name, 'fi')

    def test_standardize_screen_name(self):
        name = items.standardize_screen_name(' \ufb01', 'cinema1')
        self.assertEqual(name, 'fi')


class TestMovie(unittest.TestCase):
    def test_movie_loader(self):
        title = '\ufb01'
        result = unicodedata.normalize('NFKC', title)
        loader = items.MovieLoader()
        loader.add_value('title', title)
        item = loader.load_item()
        self.assertEqual(item['title'], result)


class TestCinema(unittest.TestCase):
    def test_cinema_loader(self):
        loader = items.CinemaLoader()
        loader.context['cinema_name'] = 'cinema1'
        loader.add_value('names', 'cinema1')
        loader.add_value('names', 'cinema2')
        loader.add_value('site', 'http://Test.org')
        item = loader.load_item()
        self.assertEqual(item['names'], ['cinema1', 'cinema2'])
        # at the current we only store site's top domain
        # TODO use tldextract to get top domain
        self.assertEqual(item['site'], 'test.org')
