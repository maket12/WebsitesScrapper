import asyncio
import json
import logging
import re
from parsers.parser import Parser

from config import Config

from .data import BASE_URL, CATEGORIES, LOW_PRIORITY_CATEGORIES


class HNMParser(Parser):
  def __init__(self, client, logger: logging.Logger, config: Config):
    super().__init__("hnm", client, logger, config)

    self.pages = self.get_state("pages", {})
    self.product_queue = self.get_state("product_queue", {})
    self.categories_done = False

  async def parse(self):
    worker_task = asyncio.create_task(self.product_queue_worker())

    category_tasks = []
    for category in CATEGORIES:
      category_tasks.append(self.scrap_category(category))

    await asyncio.gather(*category_tasks)

    self.logger.info("Scraping low priority categories...")
    for category in LOW_PRIORITY_CATEGORIES:
      await self.scrap_category(category)

    self.categories_done = True
    await worker_task
    self.logger.info("Scraping completed.")

  async def product_queue_worker(self):
    while True:
      if not self.product_queue:
        if self.categories_done:
          break
        await asyncio.sleep(2)
        continue

      tasks = []
      for _ in range(4):
        tasks.append(self.product_queue_task())

      await asyncio.gather(*tasks)
      await asyncio.sleep(1)

  async def product_queue_task(self):
    if not self.product_queue:
      return

    try:
      product_id = next(iter(self.product_queue))
      product_page = self.product_queue.pop(product_id)
      success = await self.scrap_product_page(product_id, product_page)
      if not success:
        self.product_queue[product_id] = product_page
      self.save_state()
    except Exception as e:
      self.logger.error(f"Error in product queue task: {e}")
      await asyncio.sleep(5)

  async def scrap_category(self, category: dict):
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
      data = json.loads(response.text)
      products = data.get("plpList", {}).get("productList", [])
      if not products:
        self.logger.info(f"No more products in {category_name} (page {current_page})")
        break
      for product in products:
        self.process_product(product)

      total_pages = data.get("pagination", {}).get("totalPages", 0)
      if current_page >= total_pages:
        self.logger.info(f"Reached the last page of {category_name}")
        self.pages[category_name] = -1
        self.save_state()
        break
      current_page += 1
      self.pages[category_name] = current_page
      self.save_state()
      await asyncio.sleep(2)

  def process_product(self, product: dict):
    base_id = product.get("id", None)
    if base_id is None:
      return
    base_url = product.get("url", None)
    if base_url is None:
      return
    base_url = BASE_URL + base_url

    should_scrap = base_id not in self.products or self.is_full_parse
    if should_scrap:
      self.product_queue[base_id] = base_url
      self.logger.info(f"Added {base_id} to product queue")

    name = product.get("productName", "unknown")
    category = product.get("mainCatCode", "unknown")
    prices = product.get("prices", [])
    price = "unknown"
    if prices:
      price = prices[0].get("formattedPrice", "unknown")
    sizes = product.get("sizes", [])
    size = "unknown"
    if sizes:
      size = "/".join(sorted(s.get("label", None) for s in sizes if "label" in s))

    for swatch in product.get("swatches", []):
      article_id = swatch.get("articleId", None)
      if article_id is None:
        continue

      url = swatch.get("url", None)
      if url is None:
        continue

      url = BASE_URL + url
      color = swatch.get("colorName", "unknown")

      self.set_product(
        article_id,
        url,
        category,
        name,
        price,
        article_id,
      )

      self.update_product(article_id, color=color, sizes=size)

  async def scrap_product_page(self, product_id: str, product_page: str):
    self.logger.info(f"Scraping product page for {product_id} at {product_page}")
    response = await self.client.get(product_page)
    if response.status_code != 200:
      self.logger.error(f"Failed to fetch {product_page}: {response.status_code}")
      return False

    page_data = self.parse_page_data(response.text)
    if page_data is None:
      self.logger.error(f"Failed to parse product page data for {product_id}")
      return False

    for product_id, product_data in page_data.items():
      description = product_data.get("description", "unknown")
      self.update_product(product_id, description=description)
      for i, image in enumerate(product_data.get("images", [])):
        image_url = image.get("baseUrl", None)
        if image_url is None:
          continue
        self.set_product_image(product_id, str(i + 1), image_url)

    return True

  def parse_page_data(self, data: str):
    match = re.search(
      r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script><noscript>',
      data,
      re.DOTALL,
    )
    if match:
      json_str = match.group(1)
      json_obj = json.loads(json_str)
      try:
        product_data = json_obj["props"]["pageProps"]["productPageProps"]["aemData"][
          "productArticleDetails"
        ]["variations"]
        return product_data
      except KeyError:
        return None
    return None
