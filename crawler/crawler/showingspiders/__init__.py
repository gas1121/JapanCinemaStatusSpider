# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from crawler.showingspiders.aeon import AeonSpider
from crawler.showingspiders.toho_v2 import TohoV2Spider
from crawler.showingspiders.united import UnitedSpider
from crawler.showingspiders.movix import MovixSpider
from crawler.showingspiders.kinezo import KinezoSpider
from crawler.showingspiders.cinema109 import Cinema109Spider
from crawler.showingspiders.korona import KoronaSpider
from crawler.showingspiders.cinemasunshine import CinemaSunshineSpider
from crawler.showingspiders.forum import ForumSpider


def set_independent_job_dir(curr_dir):
    def modify_job_dir(spidercls, curr_dir):
        spidercls.custom_settings = spidercls.custom_settings or {}
        spidercls.custom_settings['JOBDIR'] = \
            curr_dir + '/' + spidercls.name
    modify_job_dir(AeonSpider, curr_dir)
    modify_job_dir(TohoV2Spider, curr_dir)
    modify_job_dir(UnitedSpider, curr_dir)
    modify_job_dir(MovixSpider, curr_dir)
    modify_job_dir(KinezoSpider, curr_dir)
    modify_job_dir(Cinema109Spider, curr_dir)
    modify_job_dir(KoronaSpider, curr_dir)
    modify_job_dir(CinemaSunshineSpider, curr_dir)
    modify_job_dir(ForumSpider, curr_dir)
