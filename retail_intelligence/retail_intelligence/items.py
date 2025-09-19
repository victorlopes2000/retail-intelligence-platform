# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RetailIntelligenceItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    image_url = scrapy.Field()
    product_url = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()
    brand = scrapy.Field()
    platform = scrapy.Field()
    bestseller= scrapy.Field()
    
    
