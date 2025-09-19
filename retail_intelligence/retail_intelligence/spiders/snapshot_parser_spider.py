from collections.abc import Iterable
from typing import Any
import scrapy, logging, glob, os
from retail_intelligence.items import RetailIntelligenceItem
from retail_intelligence.itemloaders import ProductLoader

class SnapshotParserSpiderSpider(scrapy.Spider):
    name = "snapshot_parser_spider"
    
    def __init__(self, *args, **kwargs):
        # Call the parent class constructor
        super(SnapshotParserSpiderSpider, self).__init__(*args, **kwargs)

        # SpiderLoggerAdapter ke andar ka real logger access karo
        base_logger = self.logger.logger  

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(formatter)

        # Duplicate na ho is liye check karo
        if not any(isinstance(h, logging.StreamHandler) for h in base_logger.handlers):
            base_logger.addHandler(console_handler)

    def start_requests(self):
        files = glob.glob("html_pages/**/*.html", recursive=True)
        for file in files:
            try:
                abs_path = os.path.abspath(file)
                platform = "amazon" if "amazon" in file.lower() else "walmart"
                self.logger.info(f"Reading {platform.upper()} HTML file: {file}")
                with open(file, 'r', encoding='utf-8') as f:
                    html = f.read()
                    yield  scrapy.Request(
                        url=f"file:///{abs_path}",  # dummy URL for reference
                        callback=self.parse,
                        meta={'html': html, 'file': file,'platform':platform,},
                        dont_filter=True
                    )
            except Exception as e:
                self.logger.error(f"Error While Getting Files: {e}")
            
    def parse(self, response):
        platform = response.meta.get("platform", "unknown")

        if platform == "walmart":
            self.logger.info(f"Walmart Parsing is Start")
            yield from self.parse_walmart(response)
            self.logger.info(f"Walmart Parsing is End")
            
        if platform == "amazon":
            self.logger.info(f"Amazon Parsing is Start")
            yield from self.parse_amazon(response)
            self.logger.info(f"Amazaon Parsing is End")
            
        # unknown case logging
        if platform not in ["amazon", "walmart"]:
            self.logger.warning(f"Unknown platform for file: {response.meta.get('file')}")
            
    # Walmart Parser
    def parse_walmart(self, response):
        try:
            for product in response.xpath('//div[contains(@class,"mb0 ph0-xl pt0-xl")]'):
                loader = ProductLoader(item=RetailIntelligenceItem(), selector=product)

                title = product.xpath('.//span[@data-automation-id="product-title"]/text()').get()
                price = product.xpath('.//div[@data-automation-id="product-price"]/div/text()').get()
                currency = "$" if price and "$" in price else None
                image_url = product.xpath('.//img[@data-testid="productTileImage"]/@src').get()
                product_url = product.xpath('.//a[@link-identifier]/@href').get()
                rating = product.xpath('.//span[@data-testid="product-ratings"]/@data-value').get()
                review_count = product.xpath('.//span[@data-testid="product-reviews"]/@data-value').get()
                bestseller = product.xpath('.//span[@data-testid="badgeTagComponent"]/span/text()').get()
                
                loader.add_value("title", title)
                loader.add_value("price", price)
                loader.add_value("bestseller", bestseller)
                loader.add_value("currency", currency)
                loader.add_value("image_url", image_url)
                loader.add_value("rating", rating)
                loader.add_value("review_count",review_count)
                loader.add_value("product_url",  f"https://www.walmart.com{product_url}")

                loader.add_value("platform", "walmart")
                yield loader.load_item()
        except Exception as e:
            self.logger.error(f"Error parsing WALMART file {response.meta.get('file')}: {e}")

    # Amazon Parser
    def parse_amazon(self, response):
        try:
            self.logger.info(f"insidne amazon function")
            for product in response.css('div.puis-card-container'):
                loader = ProductLoader(item=RetailIntelligenceItem(), selector=product)
                
                title = product.xpath('.//h2//span/text()').get()
                price= product.xpath(".//span[@class='a-price a-text-price']//span[@class='a-offscreen']/text()").get()
                image_url = product.xpath(".//img[contains(@class,'s-image')]/@src").get()
                rating = product.xpath(".//span[@class='a-icon-alt']/text()").get()
                rel_url = product.xpath(".//a[@class='a-link-normal s-no-outline']/@href").get()
                review_count = product.xpath(".//span[@class='a-size-base s-underline-text']/text()").get()
                best_seller= product.xpath(".//span[contains(@class, 'rio-badge-label')]//span/text()").get()
                currency = product.xpath(".//span[@class='a-price-symbol']/text()").get()
                loader.add_value("title", title)
                loader.add_value("price", price)
                loader.add_value("bestseller", best_seller)
                loader.add_value("currency", currency)
                loader.add_value("image_url", image_url)
                loader.add_value("rating", rating)
                loader.add_value("review_count",review_count)
                loader.add_value("product_url", f"https://www.amazon.com{rel_url}")
                loader.add_value("platform", "amazon")

                yield loader.load_item()
        except Exception as e:
            self.logger.error(f"Error parsing AMAZON file {response.meta.get('file')}: {e}")