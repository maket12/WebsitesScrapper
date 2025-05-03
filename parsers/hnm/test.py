import asyncio
from curl_cffi import AsyncSession
import os
import json
from bs4 import BeautifulSoup

category = {
    "name": "women",
    "url": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page=3&sort=RELEVANCE&pageId=/ladies/shop-by-product/view-all&page-size=36&categoryId=ladies_all&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false",
  }

async def main():
  async with AsyncSession() as client:
    response = await client.get(category["url"])
    if response.status_code == 200:
      with open("data/hnm/test.json", "w", encoding="utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
  asyncio.run(main())
