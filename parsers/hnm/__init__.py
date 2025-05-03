import json
import logging
from parser import Parser

from config import Config

from .data import categories
from bs4 import BeautifulSoup
import asyncio


class HNMParser(Parser):
  def __init__(self, client, logger: logging.Logger, config: Config):
    super().__init__("hnm", client, logger, config)

    self.pages = self.get_state("pages", {})
    self.product_queue = self.get_state("product_description_queue", {})

  def parse(self):
    pass

  async def scrap_category(self, category: dict):
    category_name = category["name"]
    category_url = category["url"]
    current_page = self.pages.setdefault(category_name, 1)
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
        # TODO
        pass
      
      total_pages = data.get("pagination", {}).get("totalPages", 0)
      if current_page >= total_pages:
        self.logger.info(f"Reached the last page of {category_name}")
        break
      current_page += 1
      self.pages[category_name] = current_page
      self.save_state()

  async def scrap_description(self, product_page: str) -> str:
    response = await self.client.get(product_page)
    if response.status_code != 200:
      self.logger.error(f"Failed to fetch {product_page}: {response.status_code}")
      return None

    soup = BeautifulSoup(response.text, "html.parser")
    description = soup.find("div", {"id": "section-descriptionAccordion"})
    if description:
      content = description.contents[0]
      for tag in content.find_all(True):
        if "class" in tag.attrs:
          del tag.attrs["class"]
      return str(content)
    else:
      self.logger.error(f"Failed to parse product description at {product_page}")
      return None
