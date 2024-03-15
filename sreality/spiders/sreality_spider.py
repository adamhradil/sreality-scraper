from enum import Enum
import json
from urllib.parse import urlencode
import scrapy  # type: ignore

from sreality_scraper.sreality.items import SrealityItem



class SrealityUrlBuilder:
    @staticmethod
    def map_category_main_cb(category_main_cbx):
        mapping = {
            CategoryMainCb.APARTMENT.value: "byt",
            CategoryMainCb.HOUSE.value: "dum",
            CategoryMainCb.LAND.value: "pozemek",
            CategoryMainCb.COMMERCIAL.value: "komercni",
            CategoryMainCb.OTHER.value: "ostatni"
        }
        return mapping.get(category_main_cbx)

    @staticmethod
    def map_category_sub_cb(category_sub_cbx):
        mapping = {
            CategorySubCb.ONE_PLUS_KK.value: "1+kk",
            CategorySubCb.ONE_PLUS_ONE.value: "1+1",
            CategorySubCb.TWO_PLUS_KK.value: "2+kk",
            CategorySubCb.TWO_PLUS_ONE.value: "2+1",
            CategorySubCb.THREE_PLUS_KK.value: "3+kk",
            CategorySubCb.THREE_PLUS_ON.value: "3+1",
            CategorySubCb.FOUR_PLUS_KK.value: "4+kk",
            CategorySubCb.FOUR_PLUS_ONE.value: "4+1",
            CategorySubCb.FIVE_PLUS_KK.value: "5+kk",
            CategorySubCb.FIVE_PLUS_ONE.value: "5+1",
            CategorySubCb.SIX_AND_LARGER.value: "6-a-vice",
            CategorySubCb.UNUSUAL.value: "atypicky",
            CategorySubCb.ROOM.value: "pokoj",
        }
        return mapping.get(category_sub_cbx)

    @staticmethod
    def map_category_type_cb(category_type_cbx):
        mapping = {
            CategoryTypeCb.PRONAJEM.value: "pronajem",
            CategoryTypeCb.PRODEJ.value: "prodej",
            CategoryTypeCb.DRAZBA.value: "drazba",
            CategoryTypeCb.PODIL.value: "podil"
        }
        return mapping.get(category_type_cbx)


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
            url = f"{self.base_url}&per_page={self.per_page}&page={page}"
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

    def build_sreality_url(self, data):
        category_main_cbx = data.get("seo").get("category_main_cb")
        category_sub_cbx = data.get("seo").get("category_sub_cb")
        category_type_cbx = data.get("seo").get("category_type_cb")
        locality = data.get("seo").get("locality")
        hash_id = data.get('recommendations_data').get('hash_id')

        category_main_cbx = SrealityUrlBuilder.map_category_main_cb(category_main_cbx)
        category_sub_cbx = SrealityUrlBuilder.map_category_sub_cb(category_sub_cbx)
        category_type_cbx = SrealityUrlBuilder.map_category_type_cb(category_type_cbx)

        return f"https://www.sreality.cz/detail/{category_type_cbx}/{category_main_cbx}/{category_sub_cbx}/{locality}/{hash_id}"

    def parse_estate(self, response):
        sreality_item = SrealityItem()
        data = json.loads(response.text)
        sreality_item["id"] = data.get('recommendations_data').get('hash_id')
        sreality_item["type"] = data.get('codeItems').get('building_type_search')
        sreality_item["url"] = self.build_sreality_url(data)
        sreality_item["rent"] = data.get('price_czk').get('value_raw')
        sreality_item["service_fees"] = self.get_first_or_none(data.get('items'), "Poznámka k ceně")
        # security_deposit =
        sreality_item["address"] = data.get("locality").get("value")
        sreality_item["address_accuracy"] = data.get('locality').get('accuracy')
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
        sreality_item["gps_lat"] = data.get('recommendations_data').get('locality_gps_lat')
        sreality_item["gps_lon"] = data.get('recommendations_data').get('locality_gps_lon')

        yield sreality_item
