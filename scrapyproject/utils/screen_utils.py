import re


class ScreenUtils(object):
    special_name_list = [
        ["PREMIER", "プレミア"],
        ["SELECT", "セレクト"]
    ]

    @staticmethod
    def get_seat_count(screens, cinema_name, target_screen):
        """
        get screen seat count from given data.
        """
        remain_screens = ScreenUtils.query_by_number(
            screens, cinema_name, target_screen)
        if len(remain_screens) == 1:
            return list(remain_screens.values())[0]
        remain_screens = ScreenUtils.query_by_special_name(
            remain_screens, cinema_name, target_screen)
        if len(remain_screens) == 1:
            return list(remain_screens.values())[0]
        # TODO fitler by sub cinema
        return 0

    @staticmethod
    def query_by_regex(regex_str, screens):
        screen_name_list = screens.keys()
        match_screens = {}
        for curr_screen_name in screen_name_list:
            match = re.findall(regex_str, curr_screen_name)
            if match:
                match_screens[curr_screen_name] = screens[curr_screen_name]
        return match_screens

    @staticmethod
    def query_by_number(screens, cinema_name, target_screen):
        """
        get useful screens by its number,if no number in target screen name,
        or more than one screen is found, function will fail and return all
        origin screens
        """
        # try to extract screen number
        screen_number = re.findall(r'.+?(\d+)', target_screen)
        if not screen_number:
            return screens
        screen_number = screen_number[-1]
        regex_str = r'^.+#[^0-9]+?' + screen_number + r'[^0-9]*?$'
        match_screens = ScreenUtils.query_by_regex(regex_str, screens)
        if not match_screens:
            return screens
        return match_screens

    @staticmethod
    def query_by_special_name(screens, cinema_name, target_screen):
        """
        get screen seat count by special name like:
        "PREMIER" "SELECT" "プレミア" "セレクト"
        """
        used_name_list = None
        for curr_name_list in ScreenUtils.special_name_list:
            for curr_name in curr_name_list:
                if curr_name in target_screen:
                    used_name_list = curr_name_list
        if not used_name_list:
            return screens
        for used_name in used_name_list:
            regex_str = r'^.+#.*?' + used_name + r'.*?$'
            match_screens = ScreenUtils.query_by_regex(regex_str, screens)
            if match_screens:
                break
        if not match_screens:
            return screens
        return match_screens
