import asyncio
import random
import json
import time
import os
from curl_cffi import AsyncSession
from bs4 import BeautifulSoup
from parsers.iherb.data import CATEGORIES
from services.csv_worker.csv_worker import CsvWorker
from services.logs.logging import LoggerFactory
from utils.guess_extension import get_extension_from_mimetype


class IHerbParser:
    def __init__(self, api_key: str, parse_all: bool = False, images_enabled: bool = True,
                 limit: int = None, offset: int = 0, logger=None):
        self.api_key = api_key

        self.parse_all = parse_all
        self.images_enabled = images_enabled
        self.limit = limit
        self.offset = offset

        self.brand_map = {}
        self.categories = CATEGORIES  # {name, url, category_id, brands}

        self.client = None

        self.base_api_url = "https://iherb-product-data-api.p.rapidapi.com/api/IHerb/brands/"
        self.api_url = None
        self.api_headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "iherb-product-data-api.p.rapidapi.com"
        }

        self.csw_rows = []

        self.current_brand = None
        self.current_page = 1
        self.total_pages = None

        self.images_folder_base = "files/iherb/images"
        self.images_folder = None
        self.images = []

        self.csv_worker = CsvWorker(parser_name="iherb", logger=logger)
        if logger is not None:
            self.logger = logger
        else:
            self.logger = LoggerFactory(logfile="iherb.log", logger_name="iherb").get_logger()

    async def __aenter__(self):
        self.client = AsyncSession(impersonate="chrome")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()

    def _set_current_brand(self, brand: str):
        self.current_brand = brand

    def _set_current_page(self, page: int):
        self.current_page = page

    def _set_total_pages(self, amount: int | None):
        self.total_pages = amount

    def _set_api_url(self):
        if self.current_page is None:
            self._set_current_page(page=1)
        self.api_url = f"{self.base_api_url}{self.current_brand}/products?page={self.current_page}"

    def _set_images_folder(self, path: str = None):
        if path is not None:
            self.images_folder = path
        else:
            self.images_folder = self._get_images_folder()

    def _set_image(self, image: str):
        self.images.append(image)

    def _clear_images(self):
        self.images = []

    def _get_images_folder(self):
        if self.current_brand is None:
            return

        path = os.path.join(self.images_folder_base, self.current_brand)
        os.makedirs(path, exist_ok=True)
        return path

    def _set_row(self, row: dict):
        self.csw_rows.append(row)

    def _write_rows(self):
        if len(self.csw_rows) > 0:
            self.csv_worker.write_to_table(rows=self.csw_rows)
            self.csw_rows = []

    async def _load_data(self):
        try:
            if not os.path.exists("files/iherb/brand_map.json") or self.parse_all:
                await self.get_all_brands()
            else:
                with open("files/iherb/brand_map.json", "r", encoding="utf-8") as f:
                    self.brand_map = json.load(f)

            if not os.path.exists("files/iherb/categories.json") or self.parse_all:
                await self.get_brands_for_categories()
            else:
                with open("files/iherb/categories.json", "r", encoding="utf-8") as f:
                    self.categories = json.load(f)
        except Exception as e:
            self.logger.error(f"Возникла ошибка при загрузке начальных данных: {e}.")

    async def start(self):
        try:
            self.csv_worker.create_table()

            c = 0

            await self._load_data()

            brands = list(self.brand_map.values())[self.offset:]
            brands_len = len(brands)
            for brand in brands:
                if self.limit is not None:
                    if c == self.limit:
                        break

                self.logger.debug(f"Начинаем парсить бренд {brand}.")

                self._set_current_brand(brand=brand)
                await self.parse_brand()
                self._set_total_pages(amount=None)
                self._set_current_page(page=1)

                self.logger.debug(f"Бренд {brand} полностью спарсен.")

                c += 1
                difference = round((c / brands_len) * 100)
                if random.randint(1, 10) > 5:
                    self.logger.info(f"Собрано {difference}% брендов.")

            self.logger.debug("Все бренды успешно собраны.")
            self.logger.info("Парсер завершает свою работу...")
        except Exception as e:
            self.logger.critical(f"Возникла ошибка при парсинге: {e}.")

    async def parse_brand(self):
        try:
            while self.total_pages is None or self.current_page < self.total_pages:
                self.logger.info(f"Собираем {self.current_page} страницу.")

                self._set_api_url()
                self._set_images_folder()

                response = await self.client.get(
                    url=self.api_url,
                    headers=self.api_headers
                )

                if response.status_code != 200:
                    await self.download_images()
                    self._write_rows()
                    if response.status_code == 400:
                        self.logger.warning(f"Бренд {self.current_brand} не найден.")
                        break
                    if response.status_code == 429:
                        if "rate limit per minute" in response.text:
                            self.logger.warning(f"Словили флуд: {response.text}. Пауза - минута.")
                            await asyncio.sleep(61)
                        else:
                            self.logger.warning(f"Словили флуд: {response.text}. Пауза - сутки.")
                            await asyncio.sleep(86400)
                    else:
                        self.logger.warning(f"Не смогли получить данные по бренду {self.current_brand}. Код: {response.status_code}.")
                    continue

                resp_data = response.json()
                products = resp_data["products"]

                self._set_current_page(resp_data["currentPage"] + 1)
                self._set_total_pages(resp_data["totalPages"])

                if not isinstance(products, list):
                    await self.download_images()
                    self._write_rows()
                    self.logger.warning("Не смогли получить продукты.")
                    return

                for product in products:
                    try:
                        csv_row = {
                            "productId": product.get("productId", ""),
                            "brandName": product.get("brandName", ""),
                            "title": product.get("title", ""),
                            "link": product.get("link", ""),
                            "sku": product.get("sku", ""),
                            "formattedPrice": product.get("formattedPrice", ""),
                            "isSpecial": product.get("isSpecial", ""),
                            "isTrial": product.get("isTrial", ""),
                            "hasNewProductFlag": product.get("hasNewProductFlag", ""),
                            "productCatalogImage": product.get("productCatalogImage", ""),
                            "ratingValue": product.get("ratingValue", ""),
                            "reviewCount": product.get("reviewCount", ""),
                            "currencyUsed": product.get("currencyUsed", ""),
                            "countryUsed": product.get("countryUsed", ""),
                            "price": product.get("price", ""),
                            "formattedTrialPrice": product.get("formattedTrialPrice", ""),
                            "trialPrice": product.get("trialPrice", ""),
                            "formattedSpecialPrice": product.get("formattedSpecialPrice", ""),
                            "specialPrice": product.get("specialPrice", ""),
                            "discountPercentValue": product.get("discountPercentValue", ""),
                            "hasDiscount": product.get("hasDiscount", ""),
                            "shippingWeight": product.get("shippingWeight", ""),
                            "packageQuantity": product.get("packageQuantity", ""),
                            "dimensions": str(product.get("dimensions")) if product.get("dimensions") else "",
                            "lastUpdate": product.get("lastUpdate", ""),
                            "allDescription": product.get("allDescription", ""),
                            "productImages": "",
                            "variation": str(product.get("variation")) if product.get("variation") else "",
                            "serving": str(product.get("serving")) if product.get("serving") else "",
                            "categories": ','.join(product.get("categories", [])) if product.get("categories") else "",
                            "supplementFacts": str(product.get("supplementFacts")) if product.get(
                                "supplementFacts") else ""
                        }

                        images = product.get("productImages", [])
                        for img in images:
                            img_path = str(os.path.join(self.images_folder, img.split('/')[-1]))
                            csv_row["productImages"] += f"|{img_path}" if len(
                                csv_row["productImages"]) > 0 else img_path
                            self._set_image(image=img)

                        for field in self.csv_worker.fieldnames:
                            if field not in csv_row:
                                csv_row[field] = ""

                        self._set_row(row=csv_row)
                    except Exception as e:
                        self.logger.error(f"Возникла ошибка при парсинге продукта: {e}.")

                self.logger.info(f"Страница {self.current_page} успешно собрана. Кол-во продуктов: {len(products)}.")

                await asyncio.sleep(0.7)

            await self.download_images()
            self._write_rows()
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге бренда {self.current_brand}: {e}.")

    async def download_images(self):
        try:
            if not self.images_enabled:
                return

            self.logger.debug("Начинаем загрузку картинок.")
            for image in self.images:
                filepath = ""
                try:
                    response = await self.client.get(image)
                    if response.status_code == 200:
                        filename = image.split('/')[-1]
                        filename = filename.split('.')[0]

                        ext = get_extension_from_mimetype(response)
                        filepath = os.path.join(self.images_folder, filename + ext)

                        with open(filepath, "wb") as file:
                            file.write(response.content)
                    else:
                        self.logger.warning(f"Не удалось загрузить изображение, код: {response.status_code}.")
                except Exception as e:
                    self.logger.error(f"Возникла ошибка при скачивании изображения по пути {filepath}: {e}.")
        except Exception as e:
            self.logger.error(f"Вознилка ошибка при скачивании изображений: {e}.")
        finally:
            self.logger.debug(f"Картинки загружены. Количество скачанных картинок: {len(self.images)}.")
            self._clear_images()

    async def get_all_brands(self):
        self.logger.info("Getting all brands...")
        resp = await self.client.get("https://ru.iherb.com/catalog/brandsaz")
        soup = BeautifulSoup(resp.text, "html.parser")
        for element in soup.select("a[data-ga-event-category='Trending Brands']"):
            if "href" not in element.attrs:
                continue
            url = element.get("href")
            name = element.get_text(strip=True)
            self.brand_map[name] = url.rpartition("/")[2]

        self.logger.info(f"Brands found: {len(self.brand_map)}")

        with open("data/iherb/brand_map.json", "w", encoding="utf-8") as f:
            json.dump(self.brand_map, f, ensure_ascii=False, indent=2)

    async def get_brands_for_categories(self):
        self.logger.info("Getting brands for categories...")
        for category in self.categories:
            brand_names = await self.fetch_brand_names(category)
            brand_ids = []
            for brand_name in brand_names:
                brand_id = self.brand_map.get(brand_name)
                if brand_id is None:
                    self.logger.error(f"Brand {brand_name} not found in brand map")
                    continue
                brand_ids.append(brand_id)
            category["brands"] = brand_ids
            time.sleep(1)

        with open("data/iherb/categories.json", "w", encoding="utf-8") as f:
            json.dump(self.categories, f, ensure_ascii=False, indent=2)

    async def fetch_brand_names(self, category: dict):
        self.logger.info(
            f"Get brand names for category {category['name']} -> {category['url']}"
        )
        resp = await self.client.post(
            "https://catalog.app.iherb.com/category/v2/supplements/filters",
            json={
                "categoryIds": [category["category_id"]],
                "healthTopicIds": [],
                "attributeValueIds": [],
                "brandCodes": [],
                "priceRanges": [],
                "ratings": [],
                "weights": [],
                "specials": "",
                "sort": None,
                "showShippingSaver": False,
                "showITested": False,
                "searchWithinKeyWord": "",
                "programs": [],
                "showOnlyAvailable": False,
            },
        )
        json_data = json.loads(resp.text)
        if "filters" not in json_data:
            self.logger.error("No filters found")
            return []
        brand_names = []
        for filter_desc in json_data["filters"]:
            if filter_desc["filterName"] == "Brands":
                for filter_item in filter_desc["options"]:
                    brand_names.append(filter_item["displayName"])
                break
        return brand_names
