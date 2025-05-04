
BASE_URL = "https://www2.hm.com"

CATEGORIES = [
  {
    "name": "women",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/ladies/shop-by-product/view-all&page-size=36&categoryId=ladies_all&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false",
  },
  {
    "name": "men",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/men/shop-by-product/view-all&page-size=36&categoryId=men_viewall&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false"
  },
  {
    "name": "kids9-14",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/kids/9-14y/clothing/view-all&page-size=36&categoryId=kids_olderkids_clothing&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false"
  },
  {
    "name": "beauty",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/beauty/shop-by-product/view-all&page-size=36&categoryId=beauty_all&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false"
  }
]

LOW_PRIORITY_CATEGORIES = [
  {
    "name": "home",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/home/shop-by-product/view-all&page-size=36&categoryId=home_all&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false"
  },
  {
    "name": "kids2-8",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/kids/shop-by-product/clothing/view-all&page-size=36&categoryId=kids_clothing&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false"
  },
  {
    "name": "baby",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/baby/shop-by-product/clothing/view-all&page-size=36&categoryId=kids_newbornbaby_clothing&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false"
  },
  {
    "name": "newborn",
    "url_page": "https://api.hm.com/search-services/v1/en_us/listing/resultpage?pageSource=PLP&page={}&sort=RELEVANCE&pageId=/baby/newborn/clothing/view-all&page-size=36&categoryId=kids_new_born_clothing&filters=sale:false||oldSale:false&touchPoint=DESKTOP&skipStockCheck=false"
  }
]
