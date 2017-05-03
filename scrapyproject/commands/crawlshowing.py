from scrapy.commands import ScrapyCommand


class CrawlShowingCommand(ScrapyCommand):
    requires_project = True

    def short_desc(self):
        return "Crawl all support cinemas' showing data"

    def run(self, args, opts):
        self.crawler_process.crawl(
            'site109', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'toho_v2', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'movix', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'aeon', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'united', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'kinezo', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'site109', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'cinemasunshine', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'forum', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.crawl(
            'korona', keep_old_data=True, crawl_all_cinemas=True,
            crawl_all_movies=True)
        self.crawler_process.start()
        return
