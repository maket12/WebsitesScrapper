import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def main():
  with sync_playwright() as p:
    browser = p.chromium.launch(
      headless=True,
      args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
      user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
      viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()
    page.goto("https://ru.iherb.com/c/supplements?cids=101072", wait_until="domcontentloaded")

    data = page.content()
    with open("test.html", "w", encoding="utf-8") as f:
      f.write(data)
    parsed = parse_html(data)

    with open("parsed.json", "w", encoding="utf-8") as f:
      json.dump(parsed, f, ensure_ascii=False, indent=2)

    print("done")
    browser.close()

def main_file():
  with open("test.html", "r", encoding="utf-8") as f:
    data = f.read()
  parsed = parse_html(data)
  with open("parsed.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)
  print("done")

def parse_html(data: str):
  soup = BeautifulSoup(data, "html.parser")
  result = []
  for element in soup.select(".product-inner"):
    link = element.select_one(".product-link")
    price = element.select_one(".price")
    if link is None:
      continue
    url = link.get("href")
    title = link.get("title")
    price_text = price.get_text(strip=True) if price else None
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
