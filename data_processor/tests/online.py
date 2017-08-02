import unittest

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import plugins


class TestPlugins(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
