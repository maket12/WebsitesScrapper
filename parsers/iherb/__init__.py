import json
import os
import time

from bs4 import BeautifulSoup
from curl_cffi import AsyncSession

from .data import scrap_categories

async def scrap_essential():
  if not os.path.exists("data/iherb"):
    os.makedirs("data/iherb")

  async with AsyncSession() as client:
    if not os.path.exists("data/iherb/brand_map.json"):
      await get_all_brands(client)

    if not os.path.exists("data/iherb/categories.json"):
      with open("data/iherb/brand_map.json", "r", encoding="utf-8") as f:
        brand_map = json.load(f)
      await scrap_category_list(client, scrap_categories, brand_map)


async def scrap_full():
  pass


async def scrap_category_list(client: AsyncSession, categories: list, brand_map: dict):
  print("Scraping categories...")
  for category in categories:
    brand_names = await fetch_brand_names(client, category)
    brand_ids = []
    for brand_name in brand_names:
      brand_id = brand_map.get(brand_name)
      if brand_id is None:
        print(f"Brand {brand_name} not found in brand map")
        continue
      brand_ids.append(brand_id)
    category["brands"] = brand_ids
    time.sleep(1)

  with open("data/iherb/categories.json", "w", encoding="utf-8") as f:
    json.dump(categories, f, ensure_ascii=False, indent=2)


async def fetch_brand_names(client: AsyncSession, category: dict):
  print(f"Get brand names for category {category['name']} -> {category['url']}")
  resp = await client.post(
    "https://catalog.app.iherb.com/category/v2/supplements/filters",
    impersonate="chrome",
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
    print("No filters found")
    return []
  brand_names = []
  for filter_desc in json_data["filters"]:
    if filter_desc["filterName"] == "Brands":
      for filter_item in filter_desc["options"]:
        brand_names.append(filter_item["displayName"])
      break
  return brand_names


async def get_all_brands(client: AsyncSession):
  print("Getting all brands...")
  resp = await client.get("https://ru.iherb.com/catalog/brandsaz", impersonate="chrome")
  brands = parse_brands_html(resp.text)
  print("Brands found:", len(brands))

  with open("data/iherb/brand_map.json", "w", encoding="utf-8") as f:
    json.dump(brands, f, ensure_ascii=False, indent=2)


def parse_brands_html(data: str):
  soup = BeautifulSoup(data, "html.parser")
  result = {}
  for element in soup.select("a[data-ga-event-category='Trending Brands']"):
    if "href" not in element.attrs:
      continue
    url = element.get("href")
    name = element.get_text(strip=True)
    result[name] = url.rpartition("/")[2]
  return result
