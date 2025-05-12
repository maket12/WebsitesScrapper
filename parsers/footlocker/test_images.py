import asyncio
import json
import os
import re

from curl_cffi import AsyncSession

"""
Sample response from the images endpoint:
/*jsonp*/altset_314209908004({ "set": { "pv": "1.0", "type": "img_set", "n": "FLEU/314209908004", "item": [{"i":{"n":"FLEU/314209908004_01"},"s":{"n":"FLEU/314209908004_01"},"dx":"2000","dy":"1032","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_02"},"s":{"n":"FLEU/314209908004_02"},"dx":"2000","dy":"949","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_03"},"s":{"n":"FLEU/314209908004_03"},"dx":"2000","dy":"2000","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_04"},"s":{"n":"FLEU/314209908004_04"},"dx":"800","dy":"800","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_05"},"s":{"n":"FLEU/314209908004_05"},"dx":"2000","dy":"1059","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_06"},"s":{"n":"FLEU/314209908004_06"},"dx":"2000","dy":"1022","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_07"},"s":{"n":"FLEU/314209908004_07"},"dx":"1555","dy":"2000","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_08"},"s":{"n":"FLEU/314209908004_08"},"dx":"2000","dy":"831","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_09"},"s":{"n":"FLEU/314209908004_09"},"dx":"2000","dy":"2000","iv":"_XXXXX"}
    ,{"i":{"n":"FLEU/314209908004_10"},"s":{"n":"FLEU/314209908004_10"},"dx":"2000","dy":"2000","iv":"_XXXXX"}
    ] } },"314209908004");
"""

async def get_images(sku):
  base_url = "https://images.footlocker.com/is/image/"
  fmt = f"{base_url}FLEU/{sku}/?req=set,json&id={sku}&handler=altset_{sku}"
  async with AsyncSession(impersonate="chrome") as client:
    resp = await client.get(fmt)
    if resp.status_code != 200:
      print(f"Failed to fetch data: {resp.status_code}")
      return None
    
    text = resp.text
    # Remove the jsonp wrapper to extract the JSON part
    match = re.search(r'altset_\d+\((.*),"[0-9]+"\);', text, re.DOTALL)
    if not match:
      print("Failed to parse JSONP response")
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

if __name__ == "__main__":
  sku = "314209908004"
  os.makedirs("data/footlocker", exist_ok=True)
  images = asyncio.run(get_images(sku))
  print(images)
