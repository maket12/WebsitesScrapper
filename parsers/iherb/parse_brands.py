from bs4 import BeautifulSoup
import json

def main():
  with open("data/iherb_brandz.html", "r", encoding="utf-8") as f:
    data = f.read()
  parsed = parse_html(data)
  with open("data/brand_names.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)
  print("done")

def parse_html(data: str):
  soup = BeautifulSoup(data, "html.parser")
  result = {}
  for element in soup.select("a[data-ga-event-category='Trending Brands']"):
    if "href" not in element.attrs:
      continue
    url = element.get("href")
    name = element.get_text(strip=True)
    result[name] = url.rpartition("/")[2]
  return result

if __name__ == "__main__":
  main()
