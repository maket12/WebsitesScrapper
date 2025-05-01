import requests
import json
from bs4 import BeautifulSoup


def main():
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
  }
  response = requests.get("https://ru.iherb.com/c/supplements?cids=101072", headers=headers)
  data = response.text
  print(data)
  parsed = parse_html(data)
  with open("parsed.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)
  print("done")


def parse_html(data: str):
  soup = BeautifulSoup(data, "html.parser")
  result = []
  for element in soup.select(".product-inner"):
    link = element.select_one(".product-link")
    price = element.select_one(".price bdi")
    if link is None:
      continue
    url = link.get("href")
    title = link.get("title")
    price_text = None
    if price:
      parts = price.get_text().split(";")
      price_text = parts[1] if len(parts) > 1 else None
    result.append(
      {
        "url": url,
        "title": title,
        "price": price_text,
      }
    )
  return result


if __name__ == "__main__":
  main()
