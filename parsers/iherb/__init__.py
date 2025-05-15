import json
import time
import os
from logging import Logger
from parsers.parser import Parser

from bs4 import BeautifulSoup

from config import Config

from .data import CATEGORIES

# TODO - нам точно нужны все эти поля?
# TODO - image_path
fieldnames = [
  "product_id",  # changed from productId to match load_products
  "brandName",
  "title",
  "link",
  "sku",
  "formattedPrice",
  "isSpecial",
  "isTrial",
  "hasNewProductFlag",
  "productCatalogImage",
  "ratingValue",
  "reviewCount",
  "currencyUsed",
  "countryUsed",
  "price",
  "formattedTrialPrice",
  "trialPrice",
  "formattedSpecialPrice",
  "specialPrice",
  "discountPercentValue",
  "hasDiscount",
  "shippingWeight",
  "packageQuantity",
  "dimensions",
  "lastUpdate",
  "allDescription",
  "productImages",
  "variation",
  "serving",
  "categories",
  "supplementFacts",
]


class IHerbParser(Parser):
  def __init__(self, api_key: str, client, logger: Logger, config: Config):
    super().__init__("iherb", client, logger, config, fieldnames)

    self.api_key = api_key
    self.brand_map = {}
    self.categories = CATEGORIES  # {name, url, category_id, brands}
    self.api_cache = self.get_state("api_cache", {})

  async def parse(self):
    if not os.path.exists("data/iherb/brand_map.json") or self.is_full_parse:
      await self.get_all_brands()
    else:
      with open("data/iherb/brand_map.json", "r", encoding="utf-8") as f:
        self.brand_map = json.load(f)

    if not os.path.exists("data/iherb/categories.json") or self.is_full_parse:
      await self.get_brands_for_categories()
    else:
      with open("data/iherb/categories.json", "r", encoding="utf-8") as f:
        self.categories = json.load(f)

    await self.scrap_data_from_api()

  # TODO
  # def set_product(self, product_data: dict):
  #   pass

  # TODO - так как brands могут повторяться, стоит кешировать запросы к апи (self.api_cache)
  async def scrap_data_from_api(self):
    pass

  async def get_all_brands(self):
    self.logger.info("Getting all brands...")
    resp = await self.client.get("https://ru.iherb.com/catalog/brandsaz")
    soup = BeautifulSoup(resp.text, "html.parser")
    for element in soup.select("a[data-ga-event-category='Trending Brands']"):
      if "href" not in element.attrs:
        continue
      url = element.get("href")
      name = element.get_text(strip=True)
      self.brand_map[name] = url.rpartition("/")[2]

    self.logger.info("Brands found:", len(self.brand_map))

    with open("data/iherb/brand_map.json", "w", encoding="utf-8") as f:
      json.dump(self.brand_map, f, ensure_ascii=False, indent=2)

  async def get_brands_for_categories(self):
    self.logger.info("Getting brands for categories...")
    for category in self.categories:
      brand_names = await self.fetch_brand_names(category)
      brand_ids = []
      for brand_name in brand_names:
        brand_id = self.brand_map.get(brand_name)
        if brand_id is None:
          self.logger.error(f"Brand {brand_name} not found in brand map")
          continue
        brand_ids.append(brand_id)
      category["brands"] = brand_ids
      time.sleep(1)

    with open("data/iherb/categories.json", "w", encoding="utf-8") as f:
      json.dump(self.categories, f, ensure_ascii=False, indent=2)

  async def fetch_brand_names(self, category: dict):
    self.logger.info(
      f"Get brand names for category {category['name']} -> {category['url']}"
    )
    resp = await self.client.post(
      "https://catalog.app.iherb.com/category/v2/supplements/filters",
      json={
        "categoryIds": [category["category_id"]],
        "healthTopicIds": [],
        "attributeValueIds": [],
        "brandCodes": [],
        "priceRanges": [],
        "ratings": [],
        "weights": [],
        "specials": "",
        "sort": None,
        "showShippingSaver": False,
        "showITested": False,
        "searchWithinKeyWord": "",
        "programs": [],
        "showOnlyAvailable": False,
      },
    )
    json_data = json.loads(resp.text)
    if "filters" not in json_data:
      self.logger.error("No filters found")
      return []
    brand_names = []
    for filter_desc in json_data["filters"]:
      if filter_desc["filterName"] == "Brands":
        for filter_item in filter_desc["options"]:
          brand_names.append(filter_item["displayName"])
        break
    return brand_names
