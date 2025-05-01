from bs4 import BeautifulSoup
import json

category = "supplements"

def main():
  with open(f"data/iherb_{category}.html", "r", encoding="utf-8") as f:
    data = f.read()
  with open("data/brand_names.json", "r", encoding="utf-8") as f:
    brand_names = json.load(f)

  parsed = parse_html(data, brand_names)
  with open(f"data/brands_{category}.txt", "w", encoding="utf-8") as f:
    f.write(parsed)
  print("done")

def parse_html(data: str, brand_names: dict):
  soup = BeautifulSoup(data, "html.parser")
  result = []
  for element in soup.select("label[data-ga-event-action='brands']"):
    brand_name = element.get("title")
    brand_id = brand_names.get(brand_name)
    if brand_id is None:
      print(brand_name)
      continue
    result.append(brand_id)
  return '\n'.join(result)

if __name__ == "__main__":
  main()
