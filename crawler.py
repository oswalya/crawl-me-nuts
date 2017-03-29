from lxml import html
from decimal import Decimal
import sys
import os
import json
import requests
import re
import inspect
import logging

class Product:
    def __init__(self, asin, name, price_new, price_used, link):
        self.asin = asin
        self.name = name
        self.new = price_new
        self.used = price_used
        self.link = link

    def getDiff(self):
        if (self.new is None) or (self.used is None):
            return None
        value_new = Decimal(self.new)
        value_used = Decimal(self.used)
        return 100 * (value_new - value_used) / value_new

    def toJson(self):
        return json.dumps({'asin': self.asin, 'name': self.name, 'price_new': self.new, 'price_used': self.used, 'price_diff': str(self.getDiff()), 'link': self.link})


def getProductDetailsPage(url):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    XPATH_NEXT_PAGE = '//a[@id="pagnNextLink"]'
    COUNTER = 1

    while True:
        logging.debug('======PAGE '+ xstr(COUNTER) + '======')
        mod_url = url + '&page=' + xstr(COUNTER)
        COUNTER = COUNTER + 1
        page = requests.get(mod_url,headers=headers)
        doc = html.fromstring(page.content)
        readProductDetails(doc)
        if not doc.xpath(XPATH_NEXT_PAGE):
            break


def readProductDetails(document):
    XPATH_PRODUCT = '//li[contains(@id,"result_")]'
    XPATH_NAME = './/a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]'
    XPATH_PRICE_NEW = './/span[@class="a-size-base a-color-price s-price a-text-bold"]/text()'
    XPATH_PRICE_USED = './/span[@class="a-size-base a-color-price a-text-bold"]/text()'

    for i in document.xpath(XPATH_PRODUCT):
        # print(html.tostring(i, pretty_print=True))
        RAW_NAME = i.xpath(XPATH_NAME)
        RAW_NEW_PRICE = i.xpath(XPATH_PRICE_NEW)
        RAW_USED_PRICE = i.xpath(XPATH_PRICE_USED)
        RAW_ASIN = i.get('data-asin')

        NAME = RAW_NAME[0].get('title').encode('utf-8') if RAW_NAME else None
        ASIN = RAW_ASIN if RAW_ASIN else None
        NEW_PRICE = re.sub(r'[^\d,]', '', str(RAW_NEW_PRICE[0])).replace(',', '.') if RAW_NEW_PRICE else None
        USED_PRICE = re.sub(r'[^\d,]', '', str(RAW_USED_PRICE[0])).replace(',', '.') if RAW_USED_PRICE else None
        LINK = 'https://www.amazon.de/gp/offer-listing/' + ASIN if RAW_ASIN else None

        saveItem(Product(ASIN, NAME, NEW_PRICE, USED_PRICE, LINK))

def saveItem(product):
    if not isinstance(product, Product):
        logging.debug()
        raise ValueError('Object must be an instance of Product!')
    if product.getDiff() and product.getDiff() > 30.0:
        logging.info(product.toJson())

def xstr(s):
    if s is None:
        return ''
    return str(s)

def run(filename):
    with open(filename) as f:
        content = f.readlines()
    for line in content:
        logging.info(line.strip() + "\n------------------------------------------------------\n")
        getProductDetailsPage(line.strip())


if __name__ == "__main__":
    # Run('/home/bjess/workspace/python/amazon_crawler/pages.txt')
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    run('pages.txt')
