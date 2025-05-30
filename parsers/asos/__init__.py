import os
import random
import asyncio
from bs4 import BeautifulSoup
from curl_cffi import AsyncSession
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from utils.guess_extension import get_extension_from_mimetype
from services.logs.logging import LoggerFactory
from services.csv_worker.csv_worker import CsvWorker
from services.proxies import ProxyClient

default_categories = {
    "men": [
        {
            "name": "t-shirts-vests",
            "id": 7616,
            "url": "https://www.asos.com/api/product/search/v2/categories/7616?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "hoodies-sweatshirts",
            "id": 5668,
            "url": "https://www.asos.com/api/product/search/v2/categories/5668?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "jumpers-cardigans",
            "id": 7617,
            "url": "https://www.asos.com/api/product/search/v2/categories/7617?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "jeans",
            "id": 4208,
            "url": "https://www.asos.com/api/product/search/v2/categories/4208?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "shirts",
            "id": 3602,
            "url": "https://www.asos.com/api/product/search/v2/curations/3602?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "swimwear",
            "id": 13210,
            "url": "https://www.asos.com/api/product/search/v2/categories/13210?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "suits",
            "id": 5678,
            "url": "https://www.asos.com/api/product/search/v2/categories/5678?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "loungewear",
            "id": 18797,
            "url": "https://www.asos.com/api/product/search/v2/categories/18797?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "trousers-chinos",
            "id": 4910,
            "url": "https://www.asos.com/api/product/search/v2/categories/4910?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "sportswear",
            "id": 26090,
            "url": "https://www.asos.com/api/product/search/v2/categories/26090?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "co-ords",
            "id": 28291,
            "url": "https://www.asos.com/api/product/search/v2/categories/28291?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "jackets-coats",
            "id": 3606,
            "url": "https://www.asos.com/api/product/search/v2/categories/3606?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "polo-shirts",
            "id": 4616,
            "url": "https://www.asos.com/api/product/search/v2/categories/4616?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "shorts",
            "id": 7078,
            "url": "https://www.asos.com/api/product/search/v2/curations/7078?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "socks",
            "id": 16329,
            "url": "https://www.asos.com/api/product/search/v2/categories/16329?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "tall",
            "id": 20753,
            "url": "https://www.asos.com/api/product/search/v2/categories/20753?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=150"
        },
        {
            "name": "underwear",
            "id": 20317,
            "url": "https://www.asos.com/api/product/search/v2/categories/20317?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "shoes-boots-trainers",
            "id": 4209,
            "url": "https://www.asos.com/api/product/search/v2/categories/4209?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "accessories",
            "id": 4210,
            "url": "https://www.asos.com/api/product/search/v2/curations/4210?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "body-care",
            "id": 27142,
            "url": "https://www.asos.com/api/product/search/v2/categories/27142?offset=72&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=72"
        }
    ],
    "women": [
        {
            "name": "tops",
            "id": 4169,
            "url": "https://www.asos.com/api/product/search/v2/curations/4169?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "dresses",
            "id": 8799,
            "url": "https://www.asos.com/api/product/search/v2/curations/8799?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "skirts",
            "id": 2639,
            "url": "https://www.asos.com/api/product/search/v2/categories/2639?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "shorts",
            "id": 9263,
            "url": "https://www.asos.com/api/product/search/v2/categories/9263?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "co-ords",
            "id": 19632,
            "url": "https://www.asos.com/api/product/search/v2/categories/19632?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "swimwear-beachwear",
            "id": 2238,
            "url": "https://www.asos.com/api/product/search/v2/categories/2238?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "jeans",
            "id": 3630,
            "url": "https://www.asos.com/api/product/search/v2/categories/3630?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "loungewear",
            "id": 21867,
            "url": "https://www.asos.com/api/product/search/v2/categories/21867?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "sportswear",
            "id": 26091,
            "url": "https://www.asos.com/api/product/search/v2/curations/26091?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "coats-jackets",
            "id": 2641,
            "url": "https://www.asos.com/api/product/search/v2/categories/2641?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "curve-plus-size",
            "id": 9577,
            "url": "https://www.asos.com/api/product/search/v2/categories/9577?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "hoodies-sweatshirts",
            "id": 11321,
            "url": "https://www.asos.com/api/product/search/v2/categories/11321?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "jumpers-cardigans",
            "id": 2637,
            "url": "https://www.asos.com/api/product/search/v2/categories/2637?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "jumpsuits-playsuits",
            "id": 7618,
            "url": "https://www.asos.com/api/product/search/v2/categories/7618?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "lingerie-nightwear",
            "id": 6046,
            "url": "https://www.asos.com/api/product/search/v2/categories/6046?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "maternity",
            "id": 5813,
            "url": "https://www.asos.com/api/product/search/v2/categories/5813?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "multipacks",
            "id": 19224,
            "url": "https://www.asos.com/api/product/search/v2/categories/19224?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "petite",
            "id": 4177,
            "url": "https://www.asos.com/api/product/search/v2/categories/4177?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "premium-brands",
            "id": 15210,
            "url": "https://www.asos.com/api/product/search/v2/categories/15210?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "socks-tights",
            "id": 7657,
            "url": "https://www.asos.com/api/product/search/v2/categories/7657?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "suits-separates",
            "id": 13632,
            "url": "https://www.asos.com/api/product/search/v2/categories/13632?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "tall",
            "id": 18984,
            "url": "https://www.asos.com/api/product/search/v2/categories/18984?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "trousers-leggings",
            "id": 2640,
            "url": "https://www.asos.com/api/product/search/v2/curations/2640?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "shoes",
            "id": 4172,
            "url": "https://www.asos.com/api/product/search/v2/categories/4172?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        },
        {
            "name": "accessories",
            "id": 4174,
            "url": "https://www.asos.com/api/product/search/v2/curations/4174?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200&tst-category-curated-version=1"
        },
        {
            "name": "face-body",
            "id": 1314,
            "url": "https://www.asos.com/api/product/search/v2/categories/1314?offset=0&includeNonPurchasableTypes"
                   "=restocking&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB"
                   "&customerLoyaltyTier=null&keyStoreDataversion=4i7nlxk-44&advertisementsPartnerId=100712"
                   "&advertisementsVisitorId=b7b32dff-e94c-4786-a755-d57c9b820cf4&advertisementsOptInConsent=true"
                   "&limit=200"
        }
    ]
}


class AsosParser:
    def __init__(self, proxy_client: ProxyClient, categories=None, logger=None):
        if categories is None:
            categories = default_categories

        self.BASE_PRODUCT_URL = "https://asos.com/"

        self.categories = categories

        self.current_category = None
        self.current_offset = 0
        self.products_limit = 0

        self.images_folder_base = "files/asos/images"
        self.images_folder = None

        self.client = proxy_client

        self.tasks = []

        self.csv_worker = CsvWorker(parser_name="asos")
        if logger is not None:
            self.logger = logger
        else:
            self.logger = LoggerFactory(logfile="asos.log", logger_name="asos").get_logger()

    def _set_current_category(self, category: str):
        self.current_category = category

    def _set_products_limit(self, limit: int):
        self.products_limit = limit

    def _set_images_folder(self, path: str = None):
        if path is not None:
            self.images_folder = path
        else:
            self.images_folder = self._get_images_folder()

    def _get_images_folder(self):
        if self.current_category is None:
            return

        path = os.path.join(self.images_folder_base, self.current_category)
        os.makedirs(path, exist_ok=True)
        return path

    def _get_offset(self, current_url: str):
        try:
            self.current_offset += 200

            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)

            query_params["offset"] = [str(self.current_offset)]

            pathname = query_params.pop("pathname", [None])[0]

            new_query = urlencode(query_params, doseq=True)

            if pathname is not None:
                new_query = f"pathname={pathname}&{new_query}"

            new_url = urlunparse(parsed_url._replace(query=new_query))
            return new_url
        except Exception as e:
            self.logger.error(f"Возникла ошибка в _get_offset: {e}.")
            return None

    def _get_product_url(self, sub_url: str):
        return f"{self.BASE_PRODUCT_URL}{sub_url}"

    def _get_random_delay(self, left: int, right: int = None):
        if right:
            result = random.randint(left, right)
        else:
            result = random.randint(left, left + 5)
        return result

    async def start(self):
        try:
            category_tasks = []
            self.csv_worker.create_table()
            for global_categories in self.categories.values():
                for category_obj in global_categories:
                    category = category_obj['name']

                    self._set_current_category(category=category)

                    self.logger.info(f"Начинаем парсить категорию {category}.")

                    task = await asyncio.create_task(
                        self.parse_category(name=category, base_url=category_obj['url'])
                    )
                    category_tasks.append(task)

                    if self.client.iter_proxy():
                        await asyncio.gather(*category_tasks)

                    # delay = self._get_random_delay(left=30, right=40)
                    # self.logger.info(f"Задержка {delay} секунд.")
                    # await asyncio.sleep(delay)
            self.logger.info("Все категории успешно собраны.")
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге: {e}.")

    async def parse_category(self, name: str, base_url: str):
        try:
            while self.current_offset < self.products_limit or self.products_limit == 0:
                if self.current_offset != 0:
                    base_url = self._get_offset(current_url=base_url)  # offset += 200

                self._set_images_folder()

                all_products, max_amount = await self.get_all_products(url=base_url)
                if all_products is None or max_amount is None:
                    self.logger.error(f"Ошибка загрузки товаров для категории {name}.")
                    continue

                await self.parse_products(products=all_products, category=name)

                self._set_products_limit(limit=max_amount)

                difference = self.current_offset / self.products_limit * 100

                if self._get_random_delay(left=1, right=10) > 5:
                    self.logger.info(f"Собрано {difference}% в категории {name}.")

                delay = self._get_random_delay(left=6, right=10)
                self.logger.info(f"Задержка {delay} секунд.")
                await asyncio.sleep(delay)

            self.current_offset = 0
            self._set_products_limit(0)

            await asyncio.gather(*self.tasks)
            self.tasks.clear()

            self.logger.info(f"Категория {name} полностью собрана.")
        except Exception as e:
            self.logger.error(f"Возникла ошибка при парсинге категории: {e}.")

    async def parse_products(self, products: list, category: str = ""):
        try:
            csv_rows = []
            images_to_download = []
            for product in products:
                try:
                    if len(csv_rows) > 5:
                        break
                    csv_row, images = await self.get_product_info(product=product, category=category)

                    if not csv_row or not images:
                        self.logger.warning(f"Не удалось спарсить товар: {product['id']}")
                        continue

                    delay = self._get_random_delay(left=2, right=3)
                    await asyncio.sleep(delay)

                    images_to_download.append(images)
                    csv_rows.append(csv_row)
                except Exception as e:
                    self.logger.error(f"Возникла ошибка при получении информации о продукте: {e}.")

            # Запускаем задачи на скачивание
            for imgs in images_to_download:
                task = asyncio.create_task(self.download_images(images=imgs))
                self.tasks.append(task)

            self.logger.info(f"Распарсили {len(products)} товаров.")

            self.csv_worker.write_to_table(rows=csv_rows)

            del csv_rows
            images_to_download.clear()

            return True
        except Exception as e:
            self.logger.error(f"Возникла ошибка при получении информации о продуктах: {e}.")
            return False

    async def get_all_products(self, url: str):
        try:
            response = await self.client.get(url=url)

            if response.status_code != 200:
                self.logger.warning(f"Не смогли получить корректный ответ!")
                return None, None

            resp_data = response.json()

            all_products = resp_data["products"]
            max_amount = resp_data["itemCount"]

            if len(all_products) == 0 or max_amount == 0:
                self.logger.warning("Получили пустое кол-во товаров!")
                return None, None

            return all_products, max_amount
        except Exception as e:
            self.logger.error(f"Возникла ошибка при получении товаров: {e}.")
            return None, None

    async def get_product_info(self, product: dict, category: str = ""):
        try:
            product_info = {
                "id": product["id"],
                "category": category,
                "name": product["name"],
                "brand": product["brandName"]
            }

            """""""""""""""""""""
            ""  Extract images ""
            """""""""""""""""""""

            images = [product["imageUrl"].split('/')[-1]] if product["imageUrl"] else []
            images_for_downloading = []

            additional_images = product["additionalImageUrls"]

            for img in additional_images:
                images_for_downloading.append(img)
                images.append(img.split('/')[-1])

            product_info["images"] = '|'.join(images)
            del images

            """""""""""""""""""""
            ""  Extract prices ""
            """""""""""""""""""""

            price = None

            try:
                price_objs = product["price"]
                for price_obj in price_objs.items():
                    if price_obj[0] == "current":
                        price = price_obj[1]["text"]
                        break
            except (KeyError, TypeError):
                pass

            product_info["price"] = price

            """""""""""""""""""""
            ""  Extract color  ""
            """""""""""""""""""""

            product_info["color"] = product["colour"]

            """""""""""""""""""""
            ""   Extract url   ""
            """""""""""""""""""""

            product_info["url"] = self._get_product_url(sub_url=product["url"])

            response = (await self.client.get(product_info["url"])).text
            soup = BeautifulSoup(response, "html.parser")

            """""""""""""""""""""
            ""  Extract sizes  ""
            """""""""""""""""""""

            select_tag = soup.find("select", id="variantSelector")
            sizes = []

            if select_tag:
                for option in select_tag.find_all("option")[1:]:  # skip "Please select"
                    sizes.append(option.get_text(strip=True))

            product_info["size"] = '|'.join(sizes)

            """""""""""""""""""""
            ""  Extract desc   ""
            """""""""""""""""""""

            description_block = soup.find("div", id="productDescriptionDetails")
            items = []

            if description_block:
                for item in description_block.find_all("li"):
                    items.append(item.get_text(strip=True))

            product_info["description"] = '\n'.join(items)

            items.clear()

            size_fit_block = soup.find("div", id="productDescriptionSizeAndFit")
            if size_fit_block:
                fit_info = size_fit_block.find("div", class_="F_yfF")
                if fit_info:
                    items.append(fit_info.decode_contents().replace("<br>", "\n"))

            product_info["description"] += '\n' + ''.join(items)

            """""""""""""""""""""
            ""  Extract promo  ""
            """""""""""""""""""""

            promo_box = soup.find("div", attrs={"data-testid": "promo-message-box"})
            if promo_box:
                text = [p.get_text(strip=True) for p in promo_box.find_all("p")]
                product_info["promo"] = '\n'.join(text)
            else:
                product_info["promo"] = ""

            return product_info, images_for_downloading
        except Exception as e:
            self.logger.error(f"Возникла ошибка при получении информации о продукте: {e}.")
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
