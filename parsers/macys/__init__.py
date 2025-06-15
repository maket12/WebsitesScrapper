import os
import math
import random
import asyncio
from curl_cffi import AsyncSession
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from services.proxies import ProxyClient
from services.logs.logging import LoggerFactory
from services.csv_worker.csv_worker import CsvWorker
from utils.guess_extension import get_extension_from_mimetype

default_categories = {
    "mens-clothing": [
        {
            "name": "all-mens-clothing",
            "id": 197651,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/mens-clothing/all-mens-clothing&id"
                   "=197651&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "shop-all-mens-shoes",
            "id": 55822,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/mens-clothing/shop-all-mens-shoes&id=55822"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "mens-accessories",
            "id": 47665,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/mens-clothing/mens-accessories&id=47665"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        }
    ],
    "womens-clothing": [
        {
            "name": "all-womens-clothing",
            "id": 188851,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/womens-clothing/all-womens-clothing&id"
                   "=188851&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "all-womens-shoes",
            "id": 56233,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/womens-clothing/all-womens-shoes&id=56233"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "accessories",  # womens
            "id": 29440,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/womens-clothing/accessories&id=29440"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        }
    ],
    "jewelry-watches": [
        {
            "name": "all-jewelry",
            "id": 164045,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/jewelry-watches/all-jewelry&id=164045"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "all-watches",
            "id": 239616,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/jewelry-watches/all-watches&id=239616"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        }
    ],
    "kids-clothes": [
        {
            "name": "girls-clothing",
            "id": 61998,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/kids-clothes/girls-clothing&id=61998"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "boys-clothing",
            "id": 61999,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/kids-clothes/boys-clothing&id=61999"
                   "&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "baby-clothing",  # all
            "id": 64761,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/kids-clothes/baby-products/baby"
                   "-clothing&id=64761&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60"
                   "&pageIndex=1&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "toddler-girl-clothes",
            "id": 6581,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/kids-clothes/toddler-girl-clothes&id"
                   "=6581&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "toddler-boy-clothing",
            "id": 27058,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/kids-clothes/toddler-boy-clothing&id"
                   "=27058&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex=1"
                   "&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        },
        {
            "name": "toddler-kids-accessories",
            "id": 63009,
            "url": "https://www.macys.com/xapi/discover/v1/page?pathname=/shop/kids-clothes/toddler-kids-accessories"
                   "&id=63009&_navigationType=BROWSE&_shoppingMode=SITE&sortBy=ORIGINAL&productsPerPage=60&pageIndex"
                   "=1&_application=SITE&_regionCode=DE&currencyCode=EUR&size=medium"
        }
    ]
}


class MacysParser:
    def __init__(self, proxy_client: ProxyClient, categories=None, page_limit: int | None = None,
                 start_page: int = 1, logger=None):
        if categories is None:
            categories = default_categories

        self.BASE_PRODUCT_URL = "https://www.macys.com/xapi/digital/v1/product/"

        self.categories = categories
        self.page_limit = page_limit
        self.start_page = start_page

        self.current_category = None
        self.current_page = None

        self.images_folder_base = "files/macys/images"
        self.images_folder = None

        self.client = proxy_client

        self.csv_worker = CsvWorker(parser_name="macys", logger=logger)
        if logger is not None:
            self.logger = logger
        else:
            self.logger = LoggerFactory(logfile="macys.log", logger_name="macys").get_logger()

    def _set_current_category(self, category: str):
        self.current_category = category

    def _set_current_page(self, page: int):
        self.current_page = page

    def _set_images_folder(self, path: str = None):
        if path is not None:
            self.images_folder = path
        else:
            self.images_folder = self._get_images_folder()

    async def _get_product_url(self, product_id: int):
        return f"{self.BASE_PRODUCT_URL}{product_id}?clientId=PROS&currencyCode=EUR&_regionCode=DE"

    async def _get_pagination(self, current_url: str) -> str | None:
        try:
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)

            query_params["pageIndex"] = [str(self.current_page)]

            pathname = query_params.pop("pathname", [None])[0]

            new_query = urlencode(query_params, doseq=True)

            if pathname is not None:
                new_query = f"pathname={pathname}&{new_query}"

            new_url = urlunparse(parsed_url._replace(query=new_query))
            return new_url
        except Exception as e:
            self.logger.error(f"Возникла ошибка в get_pagination: {e}.")

    def _get_random_delay(self, left: int, right: int = None):
        if right:
            result = random.randint(left, right)
        else:
            result = random.randint(left, left + 5)
        return result

    def _get_images_folder(self):
        if self.current_category is None or self.current_page is None:
            return

        path = os.path.join(self.images_folder_base, self.current_category, str(self.current_page))
        os.makedirs(path, exist_ok=True)
        return path

    async def start(self):
        try:
            category_tasks = []
            self.csv_worker.create_table()
            for global_categories in self.categories.values():
                for category_obj in global_categories:
                    category = category_obj['name']

                    self._set_current_category(category=category)

                    self.logger.info(f"Начинаем парсить категорию {category}.")

                    task = asyncio.create_task(
                        self.parse_category(name=category, base_url=category_obj['url'])
                    )
                    category_tasks.append(task)

                    if self.client.iter_proxy():
                        await asyncio.gather(*category_tasks)
            self.logger.info("Все категории успешно собраны.")
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге: {e}.")

    async def parse_category(self, name: str, base_url: str):
        try:
            url_to_parse = base_url

            current_page = 0
            pages_limit = 0  # default
            self._set_current_page(page=self.start_page)
            while current_page <= pages_limit or pages_limit == 0:
                if self.page_limit:
                    if current_page > self.page_limit:
                        break

                if current_page != self.start_page:
                    url_to_parse = await self._get_pagination(current_url=url_to_parse)

                self._set_current_page(page=current_page)
                self._set_images_folder()

                self.logger.debug(f"Парсим {current_page} страницу.")

                all_products, max_amount = await self.get_all_products(url=url_to_parse)
                if all_products is None or max_amount is None:
                    self.logger.error(f"Ошибка загрузки продуктов для {name}, страница {current_page}.")
                    current_page += 1
                    continue

                res = await self.parse_products(all_products=all_products)
                if not res:
                    self.logger.critical(f"Не удалось корректно собрать {current_page} страницу.")

                if pages_limit > 0:
                    difference = round(current_page / pages_limit)
                    if self._get_random_delay(left=1, right=10) > 5:
                        self.logger.info(f"Собрано {difference}% в категории {name}.")
                        pages_limit = math.ceil(max_amount / 60)

                current_page += 1

            self.logger.info(f"Категория {name} полностью собрана.")
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге категории {name}: {e}.")

    async def parse_products(self, all_products: list):
        try:
            csv_rows = []
            images_to_download = []
            for product_id in all_products:
                try:
                    if len(csv_rows) % 15 == 0 and csv_rows != 0:
                        delay = self._get_random_delay(left=5)
                        self.logger.debug(f"Спарсили 15 продуктов. Перерыв {delay} секунд...")
                        await asyncio.sleep(delay)

                    csv_row, images = await self.get_product_info(product_id=product_id)

                    if not csv_row or not images:
                        self.logger.debug(f"Не удалось спарсить товар: {product_id}.")
                        continue

                    images_to_download.append(images)
                    csv_rows.append(csv_row)
                except Exception as e:
                    self.logger.error(f"Возникла ошибка при получении информации о продукте: {e}.")

            tasks = []
            for imgs in images_to_download:
                task = asyncio.create_task(self.download_images(images=imgs))
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks)
            self.logger.debug(f"Картинки успешно загружены.")

            self.csv_worker.write_to_table(rows=csv_rows)

            del csv_rows
            del tasks
            images_to_download.clear()

            return True
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге продуктов: {e}.")
            return False

    async def get_all_products(self, url: str):
        try:
            response = await self.client.get(url=url)

            if response.status_code != 200:
                self.logger.warning(f"Не смогли получить корректный ответ!")
                return None, None

            resp_data = response.json()

            all_products = resp_data["body"]["canvas"]["rows"][0]["rowSortableGrid"]["zones"][0]["facets"]["meta"][
                "productIds"]
            max_amount = resp_data["meta"]["context"]["productCount"]

            self.logger.debug("Успешно получили товары.")
            self.logger.info(f"Кол-во товаров на странице: {len(all_products)}.")
            self.logger.info(f"Кол-во товаров в категории: {max_amount}")

            return all_products, max_amount
        except Exception as e:
            self.logger.error(f"Возникла ошибка при получении продуктов: {e}")
            return None, None

    async def get_product_info(self, product_id: int):
        try:
            product_url = await self._get_product_url(product_id=product_id)
            response = await self.client.get(url=product_url)

            if response.status_code != 200:
                self.logger.warning(f"Не смогли получить корректный ответ!")
                return

            resp_data = response.json()
            product_list = resp_data["product"]
            if isinstance(product_list, list):
                resp_data = product_list[0]
            else:
                resp_data = product_list  # fallback, если вдруг придёт как dict

            """""""""""""""""""""
            "" Extract details ""
            """""""""""""""""""""
            details = resp_data["detail"]

            product_info = {
                "id": resp_data["id"],
                "category": resp_data["identifier"].get("topLevelCategoryName", ""),
                "name": details["name"],
                "description": details["description"],
                "features": details.get("bulletText", None)
            }

            """""""""""""""""""""
            ""  Extract images ""
            """""""""""""""""""""

            images = []
            images_to_download = []

            imagery = resp_data.get("imagery", {})
            image_list = imagery.get("images", [])
            base_url = resp_data.get("urlTemplate", {}).get("product", "")

            for img in image_list:
                file_path = img.get("filePath")
                if file_path and base_url:
                    url = base_url + file_path
                    images_to_download.append(url)
                    images.append(file_path.split('/')[-1])

            product_info["images"] = '|'.join(images)
            del images

            """""""""""""""""""""
            ""  Extract prices ""
            """""""""""""""""""""

            regular_price = None
            discounted_price = None

            try:
                tiered_price = (
                    resp_data.get("pricing", {})
                    .get("price", {})
                    .get("tieredPrice", [])
                )

                for price_item in tiered_price:
                    for value in price_item.get("values", []):
                        value_type = value.get("type", "").lower()
                        if value_type == "regular":
                            regular_price = value.get("formattedValue")
                        elif value_type == "discount":
                            discounted_price = value.get("formattedValue")
            except (KeyError, TypeError):
                pass

            product_info["regular_price"] = regular_price
            product_info["discounted_price"] = discounted_price

            """""""""""""""""""""
            ""  Extract rating ""
            """""""""""""""""""""

            try:
                product_info["rating"] = str(details["reviewStatistics"]["aggregate"]["rating"] * 20) + '%'
            except (KeyError, TypeError):
                product_info["rating"] = ""

            """""""""""""""""""""
            ""  Extract colors ""
            """""""""""""""""""""

            colors = resp_data["traits"].get("colors", "")
            try:
                product_info["color"] = colors["colorMap"][str(colors["selectedColor"])]["name"]
            except (KeyError, TypeError):
                product_info["color"] = ""

            """""""""""""""""""""
            ""  Extract sizes  ""
            """""""""""""""""""""

            try:
                sizes = resp_data["traits"]["sizes"]["sizeMap"]

                temp = []
                for size_obj in sizes.values():
                    try:
                        temp.append(size_obj["displayName"])
                    except (KeyError, TypeError):
                        pass
                product_info["size"] = '/'.join(temp)
            except (KeyError, TypeError):
                product_info["size"] = ""

            """""""""""""""""""""
            ""   Extract url   ""
            """""""""""""""""""""

            try:
                product_info["url"] = f"https://www.macys.com{resp_data['identifier']['productUrl']}"
            except (KeyError, TypeError):
                product_info["url"] = ""

            return product_info, images_to_download
        except Exception as e:
            self.logger.error(f"Возникла ошибка при получении инфо о товаре: {e}")
            return None, None

    async def download_images(self, images: list):
        try:
            async with AsyncSession(impersonate="chrome") as client:
                for image in images:
                    filepath = ""
                    try:
                        response = await client.get(image)
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
            self.logger.error(f"Возникла ошибка при скачивании изображений: {e}.")
