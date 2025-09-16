import scrapy


class SnapshotSpiderSpider(scrapy.Spider):
    name = "snapshot_spider"
    allowed_domains = ["generic.com"]
    start_urls = ["https://generic.com"]

    def parse(self, response):
        pass
