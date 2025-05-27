import asyncio
import csv
import json
import os
from datetime import datetime
from logging import Logger

from curl_cffi import AsyncSession

from config import Config
from utils.guess_extension import get_extension_from_mimetype

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

    self.products = {}
    self.state = {}
    self.fieldnames = fieldnames if fieldnames else default_fieldnames
    self.state_file = f"data/{self.parser_name}/state.json"
    self.products_file = f"data/{self.parser_name}.csv"

    self.download_image_tasks = set()

    self.load()

  async def start(self):
    pass

  def set_product(self, id, url, category, name, price, article):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    image_path = f"data/{self.parser_name}/images/{id}"
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

  def get_images_folder(self, product_id):
    return f"data/{self.parser_name}/images/{product_id}"

  def get_state(self, key, default):
    return self.state.setdefault(key, default)

  def load(self):
    os.makedirs(f"data/{self.parser_name}", exist_ok=True)
    if not self.config.reset_state:
      self.load_state()
    self.load_products()

  def load_state(self):
    if os.path.exists(self.state_file):
      with open(self.state_file, "r", encoding="utf-8") as f:
        self.state = json.load(f)
    else:
      self.state = {}

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
      json.dump(self.state, f, ensure_ascii=False)

  def save_all(self):
    self.save_products()
    self.save_state()

  def track_image_task(self, images):
    task = asyncio.create_task(self.download_images(images))
    self.download_image_tasks.add(task)
    task.add_done_callback(self.download_image_tasks.discard)
    return task

  async def wait_for_image_tasks(self):
    await asyncio.gather(*self.download_image_tasks)

  async def download_images(self, images: dict):
    try:
      async with AsyncSession(impersonate="chrome") as client:
        success_count = 0
        for image_path, image_url in images.items():
          retries = 3
          for attempt in range(retries):
            try:
              response = await client.get(image_url)
              if response.status_code == 200:
                ext = get_extension_from_mimetype(response)
                filepath = f"{image_path}{ext}"
                dirname = os.path.dirname(filepath)
                os.makedirs(dirname, exist_ok=True)

                with open(filepath, "wb") as file:
                  file.write(response.content)

                success_count += 1
                break
              else:
                self.logger.warning(
                  f"Не удалось загрузить изображение, код: {response.status_code}."
                )
            except Exception as e:
              self.logger.error(
                f"Возникла ошибка при скачивании изображения по пути {image_path}: {e}."
              )
            if attempt < retries - 1:
              await asyncio.sleep(2)
            else:
              self.logger.error(
                f"Не удалось скачать изображение {image_url} после {retries} попыток."
              )
          await asyncio.sleep(0.5)

        self.logger.info(f"Скачано {success_count} изображений.")
    except Exception as e:
      self.logger.error(f"Возникла ошибка при скачивании изображений: {e}.")
