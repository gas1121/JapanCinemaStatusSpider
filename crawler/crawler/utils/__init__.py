"""
Util classes
"""

from crawler.utils.screen_utils import ScreenUtils
from crawler.utils.site_utils import *
from crawler.utils.spider_helper import *
from scutils.log_factory import LogFactory


def sc_log_setup(settings):
    # set up the default sc logger
    my_level = settings.get('SC_LOG_LEVEL', 'INFO')
    my_name = settings.get('SC_LOGGER_NAME', 'sc-logger')
    my_output = settings.get('SC_LOG_STDOUT', True)
    my_json = settings.get('SC_LOG_JSON', False)
    my_dir = settings.get('SC_LOG_DIR', 'logs')
    my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
    my_file = settings.get('SC_LOG_FILE', 'main.log')
    my_backups = settings.get('SC_LOG_BACKUPS', 5)

    return LogFactory.get_instance(json=my_json,
                                   name=my_name,
                                   stdout=my_output,
                                   level=my_level,
                                   dir=my_dir,
                                   file=my_file,
                                   bytes=my_bytes,
                                   backups=my_backups)
