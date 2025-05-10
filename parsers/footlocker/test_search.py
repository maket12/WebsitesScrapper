import asyncio
from curl_cffi import AsyncSession
import os
import re
import json

test_category = {
  "name": "men_shoes",
  "page_url": "https://www.footlocker.co.uk/en/category/men/shoes.html?currentPage=0"
}

async def main():
  async with AsyncSession(impersonate="chrome") as client:
    resp = await client.get(test_category["page_url"])
    if resp.status_code == 200:
      os.makedirs("data/footlocker", exist_ok=True)
      with open("data/footlocker/test_search.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    else:
      print(f"Failed to fetch data: {resp.status_code}")

async def parse_page():
  with open("data/footlocker/test_search.html", "r", encoding="utf-8") as f:
    page_content = f.read()
    match = re.search(r'window\.footlocker\.STATE_FROM_SERVER\s*=\s*(\{.*?\});', page_content, re.DOTALL)
    if match:
      json_str = match.group(1)
      try:
        data = json.loads(json_str)
        products = data
        with open("data/footlocker/search_data.json", "w", encoding="utf-8") as f:
          json.dump(products, f, indent=2)
      except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    else:
      print("STATE_FROM_SERVER not found in page.")

if __name__ == "__main__":
  asyncio.run(parse_page())
