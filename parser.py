import os
import csv
import json
from datetime import datetime
from config import Config
from logging import Logger

default_fieldnames = [
  "product_id",
  "category",
  "name",
  "price",
  "article",
  "description",
  "image_path",
  "url",
  "color",
  "sizes",
  "last_update",
]


class Parser:
  def __init__(
    self, parser_name, client, logger: Logger, config: Config, fieldnames=None
  ):
    self.parser_name = parser_name
    self.client = client
    self.logger: Logger = logger.getChild(parser_name)
    self.config = config
    self.is_full_parse = config.is_full_parse

    self.images = {}
    self.products = {}
    self.state = {}
    self.fieldnames = fieldnames if fieldnames else default_fieldnames
    self.images_file = f"data/{self.parser_name}/images.txt"
    self.state_file = f"data/{self.parser_name}/state.json"
    self.products_file = f"data/{self.parser_name}.csv"

    self.load()

  async def parse(self):
    pass

  def set_product(self, id, url, category, name, price, article):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    image_path = f"data/images/{self.parser_name}/products/{id}"
    product = self.products.setdefault(id, {})
    product.update(
      {
        "product_id": id,
        "url": url,
        "category": category,
        "name": name,
        "price": price,
        "article": article,
        "image_path": image_path,
        "last_update": current_time,
      }
    )

  def update_product(self, id, color=None, sizes=None, description=None):
    if id in self.products:
      current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      update_data = {}
      update_data["last_update"] = current_time
      if color:
        update_data["color"] = color
      if sizes:
        update_data["sizes"] = sizes
      if description:
        update_data["description"] = description
      self.products[id].update(update_data)

  def set_product_image(self, product_id, image_id, image_url):
    full_image_id = f"{self.parser_name}/products/{product_id}/{image_id}"
    self.images[full_image_id] = image_url

  def get_state(self, key, default):
    return self.state.setdefault(key, default)

  def load(self):
    os.makedirs(f"data/{self.parser_name}", exist_ok=True)
    if not self.config.reset_state:
      self.load_state()
    self.load_images()
    self.load_products()

  def load_state(self):
    if os.path.exists(self.state_file):
      with open(self.state_file, "r", encoding="utf-8") as f:
        self.state = json.load(f)
    else:
      self.state = {}

  def load_images(self):
    if os.path.exists(self.images_file):
      with open(self.images_file, "r", encoding="utf-8") as f:
        for line in f:
          image_path, image_url = line.strip().split("@")
          self.images[image_path] = image_url

  def load_products(self):
    if os.path.exists(self.products_file):
      with open(self.products_file, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=self.fieldnames)
        for row in reader:
          product_id = row["product_id"]
          self.products[product_id] = {field: row[field] for field in self.fieldnames}

  def save_products(self):
    os.makedirs("data", exist_ok=True)

    with open(self.products_file, "w", newline="", encoding="utf-8") as csvfile:
      writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
      writer.writeheader()
      for product in self.products.values():
        writer.writerow(product)

  def save_state(self):
    if not os.path.exists(f"data/{self.parser_name}"):
      os.makedirs(f"data/{self.parser_name}")

    state_path = f"data/{self.parser_name}/state.json"
    with open(state_path, "w", encoding="utf-8") as f:
      json.dump(self.state, f, ensure_ascii=False, indent=2)

  def save_images(self):
    if not os.path.exists(f"data/{self.parser_name}"):
      os.makedirs(f"data/{self.parser_name}")

    with open(self.images_file, "w", encoding="utf-8") as f:
      for image_path, image_url in self.images.items():
        f.write(f"{image_path}@{image_url}\n")

  def save_all(self):
    self.save_products()
    self.save_state()
    self.save_images()
