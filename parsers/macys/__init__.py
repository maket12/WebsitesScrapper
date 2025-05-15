import json
import math
import random
import asyncio
from curl_cffi import AsyncSession
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from services.logs.logging import logger as lg
from services.csv_worker.csv_worker import CsvWorker

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
    def __init__(self, categories=None, product_limit: int = None, logger=lg):
        if categories is None:
            categories = default_categories

        self.BASE_PRODUCT_URL = "https://www.macys.com/xapi/digital/v1/product/"

        self.categories = categories
        self.product_limit = product_limit

        self.client = None

        self.csv_worker = CsvWorker(parser_name="macys")
        self.logger = logger

    async def __aenter__(self):
        self.client = AsyncSession(impersonate="chrome")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()

    async def get_product_url(self, product_id: int):
        return f"{self.BASE_PRODUCT_URL}{product_id}?clientId=PROS&currencyCode=EUR&_regionCode=DE"

    async def get_pagination(self, current_url: str, page: int) -> str | None:
        try:
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)

            query_params["pageIndex"] = [str(page)]

            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse(parsed_url._replace(query=new_query))
            return new_url.decode()
        except Exception as e:
            self.logger.error(f"Возникла ошибка в get_pagination: {e}.")

    def _get_random_delay(self, left: int, right: int = None):
        if right:
            result = random.randint(left, right)
        else:
            result = random.randint(left, left + 5)
        return result

    async def start(self):
        try:
            self.csv_worker.create_table()
            for global_category in self.categories.items():
                for category_obj in global_category[1]:
                    self.logger.info(f"Начинаем парсить категорию {category_obj['name']}.")
                    await self.parse_category(
                        name=category_obj['name'], base_url=category_obj['url']
                    )
                    if self.product_limit is None:
                        delay = self._get_random_delay(left=90, right=200)
                        self.logger.info(f"Задержка {delay} секунд.")
                        await asyncio.sleep(delay)
                    return

        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге: {e}.")

    async def parse_category(self, name: str, base_url: str):
        try:
            url_to_parse = base_url

            pages_limit = 2  # default
            current_page = 1
            while current_page < pages_limit or pages_limit == 0:
                if self.product_limit:
                    if current_page * 60 >= self.product_limit:
                        break

                if current_page != 1:
                    url_to_parse = await self.get_pagination(
                        current_url=url_to_parse, page=current_page
                    )

                self.logger.debug(f"Парсим {current_page} страницу.")

                all_products, max_amount = await self.get_all_products(url=url_to_parse)
                if all_products is None or max_amount is None:
                    self.logger.error(f"Ошибка загрузки продуктов для {name}, страница {current_page}. Пропускаем категорию.")
                    current_page += 1
                    continue

                res = await self.parse_products(all_products=all_products)
                if not res:
                    self.logger.critical(f"Не удалось корректно собрать {current_page} страницу.")

                if round(current_page / pages_limit, 1) == 0.1:
                    self.logger.info(f"Собрано 10% в категории {name}.")
                    pages_limit = math.ceil(max_amount / 60)

                elif round(current_page / pages_limit, 2) == 0.25:
                    self.logger.info(f"Собрано 25% в категории {name}.")
                    pages_limit = math.ceil(max_amount / 60)

                elif round(current_page / pages_limit, 1) == 0.5:
                    self.logger.info(f"Собрано 50% в категории {name}.")
                    pages_limit = math.ceil(max_amount / 60)

                elif round(current_page / pages_limit, 2) == 0.75:
                    self.logger.info(f"Собрано 75% в категории {name}.")
                    pages_limit = math.ceil(max_amount / 60)

                elif round(current_page / pages_limit, 1) == 0.9:
                    self.logger.info(f"Собрано 90% в категории {name}.")
                    pages_limit = math.ceil(max_amount / 60)

                current_page += 1

                delay = self._get_random_delay(left=10, right=18)
                self.logger.info(f"Задержка {delay} секунд.")
                await asyncio.sleep(delay)

            self.logger.info(f"Категория {name} полностью собрана.")
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге категории {name}: {e}.")

    async def parse_products(self, all_products: list):
        try:
            csv_rows = []
            for product_id in all_products:
                if len(csv_rows) % 15 == 0 and csv_rows != 0:
                    delay = self._get_random_delay(left=7)
                    self.logger.debug(f"Спарсили 15 продуктов. Перерыв {delay} секунд...")
                    await asyncio.sleep(delay)

                csv_row = await self.get_product_info(product_id=product_id)

                if not csv_row:
                    self.logger.debug(f"Не удалось спарсить товар: {product_id}.")
                    continue

                csv_rows.append(csv_row)

            self.csv_worker.write_to_table(rows=csv_rows)

            return True
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге продуктов: {e}.")

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
            self.logger.warning(f"Проблемная ссылка: {url}.")
            self.logger.error(f"Возникла ошибка при получении продуктов: {e}")
            return None, None

    async def get_product_info(self, product_id: int) -> dict | None:
        try:
            product_url = await self.get_product_url(product_id=product_id)
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
                "images": ""
            }

            """""""""""""""""""""
            ""  Extract images ""
            """""""""""""""""""""
            

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
                    # values всегда список (иногда из одного элемента)
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
            ""   Extract sizes ""
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
                product_info["url"] = f"https://www.macys.com/{resp_data["identifier"]["productUrl"]}"
            except (KeyError, TypeError):
                product_info["url"] = ""

            return product_info
        except Exception as e:
            self.logger.error(f"Возникла ошибка при получении инфо о товаре: {e}")


if __name__ == "__main__":
    async def main():
        async with MacysParser(product_limit=120) as a:
            await a.start()
    asyncio.run(main())

