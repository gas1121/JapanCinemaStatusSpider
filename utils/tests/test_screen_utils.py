import unittest

from jcssutils import ScreenUtils


class TestScreenUtils(unittest.TestCase):
    def test_get_seat_count(self):
        # TODO test case
        pass

    def test_query_by_number(self):
        screens = {
            "test#screen1": 10,
            "test#screen2": 20,
            "test#screen11": 30,
        }
        cinema_name = "test cinema"
        bad_data = [
            "test#screen0", "test#screen111", "screen2sss111"]
        for curr_screen in bad_data:
            result = ScreenUtils.query_by_number(
                screens, cinema_name, curr_screen)
            self.assertEqual(len(result), len(screens))
        good_data = {
            "test#screen1": "test#screen1",
            "screen1": "test#screen1",
            "screen11": "test#screen11",
            "screen01": "test#screen1",
            "screen2": "test#screen2",
        }
        for curr_screen in good_data:
            result = ScreenUtils.query_by_number(
                screens, cinema_name, curr_screen)
            self.assertEqual(len(result), 1)
            self.assertTrue(good_data[curr_screen] in result)

    def test_query_by_special_name(self):
        screens = {
            "test#screen1": 12,
            "test#PREMIER": 10,
            "test#セレクト": 20,
            "test#プラチナ": 30,
            "test#ssssssss": 30,
        }
        cinema_name = "test cinema"
        bad_data = [
            "test#screen0", "test#zzzzz", "screen1", "test#ssssssss"]
        # 3 screens should be filtered
        for curr_screen in bad_data:
            result = ScreenUtils.query_by_special_name(
                screens, cinema_name, curr_screen)
            self.assertEqual(len(result), 2)
        good_data = {
            "PREMIER": "test#PREMIER",
            "セレクト": "test#セレクト",
            "セレクトsss": "test#セレクト",
            "プラチナ": "test#プラチナ",
        }
        for curr_screen in good_data:
            result = ScreenUtils.query_by_special_name(
                screens, cinema_name, curr_screen)
            self.assertEqual(len(result), 1)
            self.assertTrue(good_data[curr_screen] in result)

    def test_query_by_sub_cinema(self):
        # TODO test case
        pass
