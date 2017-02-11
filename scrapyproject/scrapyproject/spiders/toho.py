# -*- coding: utf-8 -*-
import datetime
import scrapy


class TohoSpider(scrapy.Spider):
    name = "toho"
    allowed_domains = ["hlo.tohotheater.jp", "www.tohotheater.jp"]
    start_urls = ['https://www.tohotheater.jp/theater/find.html']

    def parse(self, response):
        cinema_page_url = response.xpath(
            '//a[span[span[contains(text(), "TOHO CINEMAS SHINJUKU")]]]/@href'
            ).extract_first()
        if cinema_page_url is not None:
            cinema_page_url = response.urljoin(cinema_page_url)
            request = scrapy.Request(cinema_page_url,
                                     callback=self.parse_cinema)
            request.meta["selectDate"] = 20170212
            yield request

    def parse_cinema(self, response):
        # generate session url
        movieSection = response.xpath(
            '//div[contains(text(),"KIMINONAWA")]/../../..'
            )
        allSessionUrlItems = movieSection.xpath(
            '//a[@class="wrapper"]/@href')
        for currSessionUrlItem in allSessionUrlItems:
            url = self.generate_session_url(currSessionUrlItem)
            yield scrapy.Request(url, callback=self.parse_session)

    def generate_session_url(self, currSessionUrlItem):
        # example: javascript:ScheduleUtils.purchaseTicket(
        #  "20170212", "076", "013132", "0761", "11", "2")
        # example: https://hlo.tohotheater.jp/net/ticket/076/TNPI2040J03.do
        # ?site_cd=076&jyoei_date=20170209&gekijyo_cd=0761&screen_cd=10
        # &sakuhin_cd=014183&pf_no=5&fnc=1&pageid=2000J01&enter_kbn=
        parameters = currSessionUrlItem.re(r'purchaseTicket\("([0-9]+)", '
                                           '"([0-9]+)", "([0-9]+)", '
                                           '"([0-9]+)", "([0-9]+)", '
                                           '"([0-9]+)"\)')
        return "https://hlo.tohotheater.jp/net/ticket/076/"\
               "TNPI2040J03.do?site_cd={site_cd}&jyoei_date={jyoei_date}"\
               "&gekijyo_cd={gekijyo_cd}&screen_cd={screen_cd}"\
               "&sakuhin_cd={sakuhin_cd}&pf_no={pf_no}&fnc={fnc}"\
               "&pageid={pageid}&enter_kbn={enter_kbn}".format(
                   site_cd=parameters[1], jyoei_date=parameters[0],
                   gekijyo_cd=parameters[3], screen_cd=parameters[4],
                   sakuhin_cd=parameters[2], pf_no=parameters[5],
                   fnc="1", pageid="2000J01", enter_kbn="")

    def parse_session(self, response):
        # example img src="/layout/0761/ppt/10/spacer.gif"
        screenItemSrc = response.xpath('//img[contains(@src, "/ppt/")]/@src'
                                       ).extract_first()
        itemList = screenItemSrc.split('/')
        screen = itemList[4]

        empty_seat_count = len(response.css('[alt~="空席(選択可)"]'))
        booked_seat_count = len(response.css('[alt~="購入済(選択不可)"]'))
        total_seat_count = empty_seat_count + booked_seat_count
        yield {
            'title': response.xpath('//dd[@class="message-movie-title"]/text()'
                                    ).extract_first(),
            'date': response.xpath('//dd[@class="message-showdate"]/text()'
                                   ).extract_first(),
            'time': response.xpath('//dd[@class="message-showdate"]/text()'
                                   ).extract_last(),
            'ciname_name': response.xpath(
                '//dd[@class="message-theater-name"]/text()').extract_first(),
            'screen': screen,
            'book_status': str(booked_seat_count)+'/'+str(total_seat_count),
            'record_time': datetime.datetime.now().strftime(
                "%I:%M%p on %B %d, %Y")
        }
