import asyncio
import json
import re
from collections import deque
from logging import Logger
from parser import Parser

from config import Config

from .data import BASE_URL, CATEGORIES


class FootlockerParser(Parser):
  def __init__(self, client, logger: Logger, config: Config):
    super().__init__("footlocker", client, logger, config)

    self.pages = self.get_state("pages", {})
    self.product_queue = deque(self.get_state("product_queue", []))

  def save_state(self):
    self.state["product_queue"] = list(self.product_queue)
    return super().save_state()

  async def parse(self):
    worker_task = asyncio.create_task(self.product_queue_worker())

    category_tasks = []
    for category in CATEGORIES:
      category_tasks.append(self.scrap_category(category))

    await asyncio.gather(*category_tasks)

    self.logger.info("Categories done.")

    while self.product_queue:
      await asyncio.sleep(1)

    # Cancel the worker task when done
    worker_task.cancel()
    try:
      await worker_task
    except asyncio.CancelledError:
      pass

  async def product_queue_worker(self):
    while True:
      if not self.product_queue:
        await asyncio.sleep(2)
        continue

      product_page = self.product_queue.popleft()
      success = await self.scrap_product_page(product_page)
      if not success:
        self.product_queue.append(product_page)
      self.save_state()

  async def scrap_category(self, category):
    category_name = category["name"]
    category_url = category["url_page"]
    current_page = self.pages.setdefault(category_name, 1)
    if current_page == -1:
      self.logger.info(f"Skipping {category_name} (already scraped)")
      return
    self.logger.info(f"Scraping {category_name} (page {current_page})")

    while True:
      url = category_url.format(current_page)
      self.logger.info(f"Fetching {url}")
      response = await self.client.get(url)
      if response.status_code != 200:
        self.logger.error(f"Failed to fetch {url}: {response.status_code}")
        await asyncio.sleep(5)
        continue
      page_data = self.parse_search_page(url, response.text)
      if not page_data:
        await asyncio.sleep(5)
        continue
      search_data = page_data.get("search", {})
      product_links = page_data.get("details", {}).get("selected", {})
      if not product_links:
        self.logger.info(f"No products on {url}")
        self.pages[category_name] = -1
        self.save_state()
        break

      product_url_map = {}
      added_products = 0
      for product_link in product_links.keys():
        product_full_url = BASE_URL + product_link
        product_sku = product_links[product_link].get("styleSku", None)
        should_scrap = product_sku not in self.products or self.is_full_parse
        # TODO !! - maybe scrap if there are more variants than we got
        if should_scrap and product_full_url not in self.product_queue:
          self.product_queue.append(product_full_url)
          added_products += 1
        if product_sku:
          product_url_map[product_sku] = product_full_url.rpartition("/")[0]

      self.logger.info(f"Added {added_products} product urls from {url}")

      products = search_data.get("products", [])
      processed_products = 0
      for product in products:
        processed_products += self.process_product(
          category_name, product, product_url_map
        )

      self.logger.info(
        f"Parsed basic information of {processed_products} product variants from {url}"
      )

      total_pages = search_data.get("pagination", {}).get("totalPages", 0)
      if current_page >= total_pages or current_page > 1:
        self.logger.info(f"Reached the last page of {category_name}")
        self.pages[category_name] = -1
        self.save_state()
        break
      current_page += 1
      self.pages[category_name] = current_page
      self.save_state()
      await asyncio.sleep(2)

  def process_product(self, category_name, product, product_url_map):
    name = product.get("name", None)
    if name is None:
      return 0
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
      variant_price = variant.get("price", {}).get("formattedListPrice", None)
      variant_color = variant.get("color", None)
      self.set_product(
        variant_sku, variant_url, category_name, variant_name, variant_price, variant_sku
      )
      self.update_product(variant_sku, color=variant_color)
      num_variants += 1
    return num_variants

  async def scrap_product_page(self, product_page):
    # TODO - implement this
    await asyncio.sleep(2)
    return True

  def parse_search_page(self, url, page_content):
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
