import requests
import uuid

'''
curl --request GET \
	--url https://iherb-product-data-api.p.rapidapi.com/api/IHerb/brands \
	--header 'Content-Type: application/json' \
	--header 'x-rapidapi-host: iherb-product-data-api.p.rapidapi.com' \
	--header 'x-rapidapi-key: deda66c5ebmsha2bee7bd5d349b4p114fc9jsndb5e5ca8aa23'
'''

headers = {
  "Content-Type": "application/json",
  "x-rapidapi-host": "iherb-product-data-api.p.rapidapi.com",
  "x-rapidapi-key": "deda66c5ebmsha2bee7bd5d349b4p114fc9jsndb5e5ca8aa23"
}

random_uuid = uuid.uuid4().hex[:16]
brands_url = "https://iherb-product-data-api.p.rapidapi.com/api/IHerb/brands?page=1"
brands2_url = "https://iherb-product-data-api.p.rapidapi.com/api/IHerb/brands/cen/products?page=1"

response = requests.get(brands2_url, headers=headers)
with open("brands2.json", "w", encoding="utf-8") as f:
  f.write(response.text)
