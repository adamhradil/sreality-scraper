# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SrealityItem(scrapy.Item):

    id = scrapy.Field()
    url = scrapy.Field()
    type = scrapy.Field()
    rent = scrapy.Field()
    service_fees = scrapy.Field()
    address = scrapy.Field()
    address_accuracy = scrapy.Field()
    description = scrapy.Field()
    disposition = scrapy.Field()
    available_from = scrapy.Field()
    floor = scrapy.Field()
    area = scrapy.Field()
    furnished = scrapy.Field()
    status = scrapy.Field()
    ownership = scrapy.Field()
    penb = scrapy.Field()
    balcony = scrapy.Field()
    cellar = scrapy.Field()
    terrace = scrapy.Field()
    elevator = scrapy.Field()
    parking = scrapy.Field()
    garage = scrapy.Field()
    loggie = scrapy.Field()
