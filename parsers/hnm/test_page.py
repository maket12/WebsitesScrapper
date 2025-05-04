import asyncio
from curl_cffi import AsyncSession
import json
import re

async def main():
  async with AsyncSession(impersonate="chrome") as client:
    response = await client.get("https://www2.hm.com/en_us/productpage.1255289002.html")
    if response.status_code == 200:
      json_data = parse_data(response.text)
      with open("data/hnm/test_page.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

def parse_data(data: str):
  match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script><noscript>', data, re.DOTALL)
  if match:
    json_str = match.group(1)
    json_obj = json.loads(json_str)
    try:
      product_data = json_obj["props"]["pageProps"]["productPageProps"]["aemData"]["productArticleDetails"]["variations"]
      return product_data
    except KeyError:
      return None
  return None

if __name__ == "__main__":
  asyncio.run(main())
