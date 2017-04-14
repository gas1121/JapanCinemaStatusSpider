import re


class ScreenUtils(object):
    @staticmethod
    def get_seat_count_by_number(screens, cinema_name, target_screen):
        """
        get screen seat count by its number
        if no number in target screen name of more than one screen is
        found, function will fail and return 0
        """
        # try to extract screen number
        screen_number = re.findall(r'.+?(\d+)', target_screen)
        if not screen_number:
            return 0
        screen_number = screen_number[-1]
        screen_name_list = screens.keys()
        match_screens = []
        for curr_screen_name in screen_name_list:
            match = re.findall(
                r'^.+#[^0-9]+?' + screen_number + r'[^0-9]*?$',
                curr_screen_name)
            if match:
                match_screens.append(curr_screen_name)
        if not match_screens:
            return 0
        if len(match_screens) == 1:
            return screens[match_screens[0]]
        # when more than one screen is found judge by cinema name
        # TODO
        return 0
