from logging import Logger
from parser import Parser

from config import Config

# TODO - нам точно нужны все эти поля?
# TODO - image_path
fieldnames = [
  "product_id", # changed from productId to match load_products
  "brandName",
  "title",
  "link",
  "sku",
  "formattedPrice",
  "isSpecial",
  "isTrial",
  "hasNewProductFlag",
  "productCatalogImage",
  "ratingValue",
  "reviewCount",
  "currencyUsed",
  "countryUsed",
  "price",
  "formattedTrialPrice",
  "trialPrice",
  "formattedSpecialPrice",
  "specialPrice",
  "discountPercentValue",
  "hasDiscount",
  "shippingWeight",
  "packageQuantity",
  "dimensions",
  "lastUpdate",
  "allDescription",
  "productImages",
  "variation",
  "serving",
  "categories",
  "supplementFacts",
]


class IHerbParser(Parser):
  def __init__(self, client, logger: Logger, config: Config):
    super().__init__("iherb", client, logger, config, fieldnames)

  async def parse(self):
    pass
  
  # TODO
  def set_product(self, product_data: dict) -> dict:
    pass
