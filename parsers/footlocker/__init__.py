import asyncio
import json
import re
import urllib.parse as urlparse
from logging import Logger

from config import Config
from parsers.parser import Parser

from .data import BASE_URL, CATEGORIES


class FootlockerParser(Parser):
  def __init__(self, client, logger: Logger, config: Config):
    super().__init__("footlocker", client, logger, config)

    self.get_state("category_queries_done", False)
    self.query_queue = self.get_state("query_queue", [])
    self.product_queue = self.get_state("product_queue", [])
    self.images_queue = self.get_state("images_queue", [])
    self.categories_done = False

  async def start(self):
    if not self.get_state("category_queries_done", False):
      self.logger.info("Scraping category queries...")
      for category in CATEGORIES:
        success = False
        while not success:
          success = await self.scrap_category_queries(category)
          if not success:
            await asyncio.sleep(5)

    self.state["category_queries_done"] = True
    self.save_state()

    worker_task = asyncio.create_task(self.product_queue_worker())
    images_task = asyncio.create_task(self.images_queue_worker())

    self.logger.info("Scraping query pages...")
    while self.query_queue:
      query_page = self.query_queue.pop(0)
      success = await self.scrap_query_page(query_page)
      if not success:
        self.query_queue.append(query_page)
      self.save_state()
      await asyncio.sleep(1)

    self.categories_done = True
    await worker_task
    await images_task
    await self.wait_for_image_tasks()
    self.logger.info("Scraping completed.")

  async def product_queue_worker(self):
    self.logger.info("Product queue worker started.")
    while True:
      if not self.product_queue:
        if self.categories_done:
          break
        await asyncio.sleep(2)

      tasks = []
      for _ in range(4):
        tasks.append(self.product_queue_task())

      await asyncio.gather(*tasks)
      await asyncio.sleep(1)

  async def images_queue_worker(self):
    while True:
      if not self.images_queue:
        if self.categories_done:
          break
        await asyncio.sleep(2)

      tasks = []
      for _ in range(4):
        tasks.append(self.images_queue_task())

      await asyncio.gather(*tasks)
      await asyncio.sleep(1)

  async def product_queue_task(self):
    if not self.product_queue:
      return

    try:
      product_page = self.product_queue.pop(0)
      success = await self.scrap_product_page(product_page)
      if not success:
        self.product_queue.append(product_page)
      self.save_state()
    except Exception as e:
      self.logger.error(f"Error in product queue worker: {e}")
      await asyncio.sleep(5)

  async def images_queue_task(self):
    if not self.images_queue:
      return

    try:
      sku = self.images_queue.pop(0)
      success = await self.scrap_product_images(sku)
      if not success:
        self.images_queue.append(sku)
      self.save_state()
    except Exception as e:
      self.logger.error(f"Error in failed images queue worker: {e}")
      await asyncio.sleep(5)

  async def scrap_category_queries(self, category):
    category_name = category["name"]
    category_url = category["url"]
    self.logger.info(f"Fetching {category_url}")

    response = await self.client.get(category_url)
    if response.status_code != 200:
      self.logger.error(f"Failed to fetch {category_url}: {response.status_code}")
      return False

    page_data = self.parse_state_from_page(category_url, response.text)
    if not page_data:
      return False

    queries = self.get_queries_for_category(category_name, category_url, page_data)
    if not queries:
      self.logger.error(f"Failed to parse query URLs from {category_url}")
      return False

    self.logger.info(f"Found {len(queries)} queries for {category_name}")
    for query in queries:
      if query not in self.query_queue:
        self.query_queue.append(query)

    self.save_state()
    return True

  def get_queries_for_category(self, category_name, category_url, page_data):
    facets = page_data.get("search", {}).get("facets", [])
    if not facets:
      return None
    queries = []
    for facet in facets:
      if facet.get("name") == "Model":
        for value in facet.get("values", []):
          value_name = value.get("name", None)
          if value_name is None:
            continue
          value_query = value.get("query", {}).get("query", {}).get("value", None)
          if value_query is None:
            continue
          value_url = f"{category_url}?query={urlparse.quote(value_query)}"
          queries.append(f"{category_name};;{value_name};;{value_url}")
    return queries

  async def scrap_query_page(self, query):
    category_name, query_name, query_url = query.split(";;")

    self.logger.info(
      f"Scraping {category_name} - {query_name}; fetching query url {query_url}"
    )
    response = await self.client.get(query_url)
    if response.status_code != 200:
      self.logger.error(f"Failed to fetch {query_url}: {response.status_code}")
      return False

    page_data = self.parse_state_from_page(query_url, response.text)
    if not page_data:
      return False

    search_data = page_data.get("search", {})
    product_links = page_data.get("details", {}).get("selected", {})
    if not product_links:
      self.logger.info(f"No products on {query_url}, This should not happen.")
      return True

    product_url_map = {}
    added_products = 0
    for product_link in product_links.keys():
      product_full_url = BASE_URL + product_link
      product_sku = product_links[product_link].get("styleSku", None)
      should_scrap = product_sku not in self.products or self.is_full_parse
      if should_scrap and product_full_url not in self.product_queue:
        self.product_queue.append(product_full_url)
        added_products += 1
      if product_sku:
        product_url_map[product_sku] = product_full_url.rpartition("/")[0]

    self.logger.info(f"Added {added_products} product urls from {query_url}")

    products = search_data.get("products", [])
    processed_products = 0
    for product in products:
      processed_products += self.process_product(product, product_url_map)

    self.logger.info(
      f"Parsed basic information of {processed_products} product variants from {query_url}"
    )
    return True

  def process_product(self, product, product_url_map):
    name = product.get("name", None)
    if name is None:
      return 0
    name, _, category_name = name.rpartition(" - ")
    if name == "":
      name = category_name
      category_name = "N/A"

    sku = product.get("sku", None)
    if sku is None:
      return 0
    url = product_url_map.get(sku, None)
    if url is None:
      return 0
    full_url = f"{url}/{sku}.html"

    price = product.get("price", {}).get("formattedValue", None)
    color = None
    temp = product.get("baseOptions", [])
    if temp:
      color = temp[0].get("selected", {}).get("style", None)

    self.set_product(sku, full_url, category_name, name, price, sku)
    self.update_product(sku, color=color)

    num_variants = 1
    for variant in product.get("variantOptions", []):
      variant_sku = variant.get("sku", None)
      if variant_sku is None:
        continue
      variant_url = f"{url}/{variant_sku}.html"
      variant_name = variant.get("name", None)
      if variant_name is None:
        continue
      variant_name, _, variant_category_name = variant_name.rpartition(" - ")
      if variant_name == "":
        variant_name = variant_category_name
        variant_category_name = category_name

      variant_price = variant.get("price", {}).get("formattedSalePrice", None)
      variant_color = variant.get("color", None)
      self.set_product(
        variant_sku,
        variant_url,
        variant_category_name,
        variant_name,
        variant_price,
        variant_sku,
      )
      self.update_product(variant_sku, color=variant_color)
      num_variants += 1
    return num_variants

  async def scrap_product_page(self, product_page_url):
    self.logger.info(f"Scraping product page {product_page_url}")
    response = await self.client.get(product_page_url)
    if response.status_code != 200:
      self.logger.error(f"Failed to fetch {product_page_url}: {response.status_code}")
      return False

    product_data = self.get_product_data(product_page_url, response.text)

    if not product_data:
      self.logger.error(f"Failed to parse product data from {product_page_url}")
      return False

    return await self.process_product_data(product_data, product_page_url)

  def get_product_data(self, product_page, response_text):
    page_data = self.parse_state_from_page(product_page, response_text)
    if not page_data:
      return None

    product_data = (
      page_data.get("api", {})
      .get("productDetails", {})
      .get("getDetails", {})
      .get("data", None)
    )
    return product_data

  async def process_product_data(self, product_data, product_page_url):
    base_page = product_page_url.rpartition("/")[0]
    style_data = product_data.get("style", {})
    sku = style_data.get("sku", None)
    if sku is None:
      return False

    model_data = product_data.get("model", {})
    name = model_data.get("name", None)
    if name is None:
      return False
    name, _, category_name = name.rpartition(" - ")
    if name == "":
      name = category_name
      category_name = "N/A"

    description = model_data.get("description", None)
    color = style_data.get("color", None)
    price = style_data.get("price", {}).get("formattedSalePrice", None)

    size_data = product_data.get("sizes", {})
    sizes = []
    for size in size_data:
      is_active = size.get("active", False)
      size_value = size.get("size", None)
      if is_active and size_value is not None:
        sizes.append(size_value)
    size_str = ";".join(sizes)
    if not size_str:
      size_str = "N/A"

    self.set_product(
      sku,
      product_page_url,
      category_name,
      name,
      price,
      sku,
    )
    self.update_product(
      sku,
      color=color,
      sizes=size_str,
      description=description,
    )
    self.images_queue.append(sku)

    style_variants = product_data.get("styleVariants", [])
    subproducts = {}
    for variant in style_variants:
      variant_sku = variant.get("sku", None)
      if variant_sku is None:
        continue
      variant_url = f"{base_page}/{variant_sku}.html"
      variant_price = variant.get("price", {}).get("formattedSalePrice", None)
      variant_color = variant.get("color", None)
      variant_size = variant.get("size", None)
      is_active = variant.get("active", False) and variant_size is not None
      if variant_sku not in subproducts:
        subproducts[variant_sku] = {
          "url": variant_url,
          "price": variant_price,
          "color": variant_color,
          "sizes": [],
        }
      if is_active:
        subproducts[variant_sku]["sizes"].append(variant_size)

    for variant_sku, variant_data in subproducts.items():
      variant_url = variant_data["url"]
      variant_price = variant_data["price"]
      variant_color = variant_data["color"]
      variant_sizes = variant_data["sizes"]
      size_str = ";".join(variant_sizes)
      if not size_str:
        size_str = "N/A"
      self.set_product(
        variant_sku,
        variant_url,
        category_name,
        name,
        variant_price,
        sku,
      )
      self.update_product(
        variant_sku,
        color=variant_color,
        sizes=size_str,
        description=description,
      )
      self.images_queue.append(variant_sku)

    self.save_state()
    return True

  async def scrap_product_images(self, sku):
    images = await self.get_product_images(sku)
    if images:
      image_dict = {}
      image_folder = self.get_images_folder(sku)
      for i, image_url in enumerate(images):
        image_path = f"{image_folder}/{i + 1}"
        image_dict[image_path] = image_url

      self.track_image_task(image_dict)
      return True

    return False

  async def get_product_images(self, sku):
    base_url = "https://images.footlocker.com/is/image/"
    images_url = f"{base_url}FLEU/{sku}/?req=set,json&id={sku}&handler=altset_{sku}"
    self.logger.debug(f"Fetching images from {images_url}")
    response = await self.client.get(images_url)
    if response.status_code != 200:
      self.logger.error(f"Failed to fetch images: {response.status_code}")
      return None

    text = response.text
    # Remove the jsonp wrapper to extract the JSON part
    match = re.search(r'altset_\d+\((.*),"[0-9]+"\);', text, re.DOTALL)
    if not match:
      self.logger.error("Failed to parse JSONP response")
      return None

    json_str = match.group(1)
    data = json.loads(json_str)
    items = data["set"]["item"]

    # Build image URLs
    image_urls = []
    for item in items:
      image_name = item["i"]["n"]
      url = f"{base_url}{image_name}"
      image_urls.append(url)

    return image_urls

  def parse_state_from_page(self, url, page_content):
    match = re.search(
      r"window\.footlocker\.STATE_FROM_SERVER\s*=\s*(\{.*?\});", page_content, re.DOTALL
    )
    if match:
      json_str = match.group(1)
      try:
        data = json.loads(json_str)
        return data
      except json.JSONDecodeError as e:
        self.logger.error(f"{url} : JSON decode error: {e}")
        return None

    self.logger.error(f"{url} : STATE_FROM_SERVER not found in page.")
    return None
