from urllib.parse import urlencode
import scrapy
import json

from sreality_scraper.sreality.items import SrealityItem

class CategoryMainCb(Enum):
    APARTMENT = 1
    HOUSE = 2
    LAND = 3
    COMMERCIAL = 4
    OTHER = 5


class CategorySubCb(Enum):
    NA = 1
    ONE_PLUS_KK = 2
    ONE_PLUS_ONE = 3
    TWO_PLUS_KK = 4
    TWO_PLUS_ONE = 5
    THREE_PLUS_KK = 6
    THREE_PLUS_ON = 7
    FOUR_PLUS_KK = 8
    FOUR_PLUS_ONE = 9
    FIVE_PLUS_KK = 10
    FIVE_PLUS_ONE = 11
    SIX_AND_LARGER = 12
    UNUSUAL = 16
    ROOM = 47  # leased apartments only
    # land
    HOUSINGS = 19
    COMMERCIAL = 18
    FIELDS = 20
    MEADOWS = 22
    FORRESTS = 21
    PONDS = 46
    ORCHARD_VINEYARD = 48
    GARDEN = 23
    OTHER_LAND = 24
    # commercial
    OFFICES = 25
    WAREHOUSES = 26
    PRODUCTION = 27
    RETAIL_SPACES = 28
    ACCOMMODATIONS = 29
    RESTAURANTS = 30
    AGRICULTURE = 31
    APARTMENT_BUILDING = 38
    OTHER_COMMERCIAL = 32
    DOCTORS_OFFICE = 56
    APARTMENTS = 57
    VIRTUAL_OFFICE = 49  # lease only

    # other
    GARAGE = 34
    PARKING_PLACE = 52
    MOBILE_HOME = 53
    WINE_CELLAR = 50
    ATTIC = 51
    OTHER = 36


# houses
class RoomCountCb(Enum):
    ONE_ROOM = 1
    TWO_ROOMS = 2
    THREE_ROOMS = 3
    FOUR_ROOMS = 4
    FIVE_ROOMS = 5
    UNUSUAL = 6


class CategoryTypeCb(Enum):
    PRODEJ = 1
    PRONAJEM = 2
    DRAZBA = 3
    PODIL = 4


class SrealitySpider(scrapy.Spider):
    name = "sreality"
    allowed_domains = ["www.sreality.cz"]
    params = [
        ("category_main_cb", "1"),
        ("category_type_cb", "2"),
        ("locality_region_id", "10"),
    ]
    base_url = "https://www.sreality.cz/api/cs/v2/estates?" + urlencode(params)
    per_page = 60  # Number of items per page

    def start_requests(self):
        url = f"{self.base_url}&per_page={self.per_page}"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
        result_size = data.get('result_size')
        total_pages = result_size // self.per_page + 2

        yield from self.parse_page(data)

        for page in range(1, total_pages):
            url = f"{self.base_url}?per_page={self.per_page}&page={page}"
            yield scrapy.Request(url)

    def parse_page(self, data):
        if data['_embedded']['estates']:
            estates = [estate['_links']['self']['href'] for estate in data['_embedded']['estates']]
            for href in estates:
                yield scrapy.Request(f"https://www.sreality.cz/api{href}", callback=self.parse_estate)

    def get_first_or_none(self, l1: list, string: str):
        filtered_dict = [item for item in l1 if string in item['name']]
        if len(filtered_dict) > 0:
            return filtered_dict[0].get('value')
        return None

    def parse_estate(self, response):
        sreality_item = SrealityItem()
        data = json.loads(response.text)
        sreality_item["id"] = data.get('recommendations_data').get('hash_id')
        sreality_item["type"] = data.get('codeItems').get('building_type_search')
        sreality_item["url"] = response.url
        sreality_item["rent"] = data.get('price_czk').get('value_raw')
        sreality_item["service_fees"] = self.get_first_or_none(data.get('items'), "Poznámka k ceně")
        # security_deposit = 
        sreality_item["address"] = data.get('locality').get('value')
        sreality_item["address"] = data.get('locality').get('accuracy')
        sreality_item["description"] = data.get('text').get('value')
        sreality_item["disposition"] = data.get('seo').get('category_sub_cb')
        sreality_item["available_from"] = self.get_first_or_none(data.get('items'), "Datum nastěhování")
        sreality_item["floor"] = self.get_first_or_none(data.get('items'), "Podlaží")
        sreality_item["area"] = self.get_first_or_none(data.get('items'), "Užitná plocha")
        sreality_item["furnished"] = data.get('recommendations_data').get('furnished')
        sreality_item["status"] = self.get_first_or_none(data.get('items'), "Stav objektu")
        sreality_item["ownership"] = data.get('codeItems').get('ownership')
        sreality_item["penb"] = self.get_first_or_none(data.get('items'), "Energetická náročnost budovy")
        # design = 
        sreality_item["balcony"] = data.get('recommendations_data').get('balcony')
        sreality_item["cellar"] = data.get('recommendations_data').get('cellar')
        # front_garden = 
        sreality_item["terrace"] = data.get('recommendations_data').get('terrace')
        sreality_item["elevator"] = data.get('recommendations_data').get('elevator')
        sreality_item["parking"] = data.get('recommendations_data').get('parking_lots')
        sreality_item["garage"] = data.get('recommendations_data').get('garage')
        # pets = 
        sreality_item["loggie"] = data.get('recommendations_data').get('loggia')
        yield sreality_item
