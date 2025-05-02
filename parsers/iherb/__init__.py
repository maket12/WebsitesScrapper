from rnet import Impersonate, Client
from bs4 import BeautifulSoup
import json
import os

async def scrap_essential():
  if not os.path.exists("data/iherb"):
    os.makedirs("data/iherb")
  
  client = Client(impersonate=Impersonate.Chrome134)
  if not os.path.exists("data/iherb/brand_map.json"):
    await get_all_brands(client)
  
  if not os.path.exists("data/iherb/categories.json"):
    with open("data/iherb/brand_map.json", "r", encoding="utf-8") as f:
      brand_map = json.load(f)
    await scrap_category_list(client, scrap_categories[:1], brand_map)


async def scrap_full():
  pass


scrap_categories = [
  {
    "name": "Vitamins",
    "url": "https://ru.iherb.com/c/supplements?cids=101072",
  },
  {
    "name": "Bone, Joint & Cartilage",
    "url": "https://ru.iherb.com/c/supplements?cids=100727",
  },
  {
    "name": "Minerals",
    "url": "https://ru.iherb.com/c/supplements?cids=1800",
  },
  {
    "name": "Children's Health",
    "url": "https://ru.iherb.com/c/supplements?cids=100349",
  },
  {
    "name": "Amino Acids",
    "url": "https://ru.iherb.com/c/supplements?cids=1694",
  },
  {
    "name": "Brain & Cognitive",
    "url": "https://ru.iherb.com/c/supplements?cids=105803",
  },
  {
    "name": "Women's Health",
    "url": "https://ru.iherb.com/c/supplements?cids=8741",
  },
  {
    "name": "Fish Oil & Omegas (EPA DHA)",
    "url": "https://ru.iherb.com/c/supplements?cids=1542",
  },
  {
    "name": "Men's Health",
    "url": "https://ru.iherb.com/c/supplements?cids=3282",
  },
  {
    "name": "Phospholipids",
    "url": "https://ru.iherb.com/c/supplements?cids=102094",
  },
]

async def scrap_category_list(client: Client, categories: list, brand_map: dict):
  print("Scraping categories...")
  for category in categories:
    brand_ids = await scrap_category(client, category, brand_map)
    category["brands"] = brand_ids
  
  with open("data/iherb/categories.json", "w", encoding="utf-8") as f:
    json.dump(categories, f, ensure_ascii=False, indent=2)

async def scrap_category(client: Client, category: dict, brand_map: dict):
  print(f"Scraping category {category['name']} -> {category['url']}")
  resp = await client.get(category["url"])
  data = await resp.text()
  brand_names = parse_brand_names(data)
  print("Brand names found:", len(brand_names))
  brand_ids = []
  for brand_name in brand_names:
    brand_id = brand_map.get(brand_name)
    if brand_id is None:
      print(f"{brand_name} not found in brand map")
      continue
    brand_ids.append(brand_id)
  return brand_ids


async def get_all_brands(client: Client):
  print("Getting all brands...")
  resp = await client.get("https://www.iherb.com/catalog/brandsaz")
  data = await resp.text()
  brands = parse_brands_html(data)
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


def parse_brand_names(data: str):
  soup = BeautifulSoup(data, "html.parser")
  result = []
  for element in soup.select("label[data-ga-event-action='brands']"):
    brand_name = element.get("title")
    result.append(brand_name)
  return result
