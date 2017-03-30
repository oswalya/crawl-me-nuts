from lxml import html
from decimal import Decimal
import sys
import os
import json
import requests
import re
import inspect
import logging
import argparse
import yaml

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

class Xpathdef:
    _NEXT_PAGE = '//a[@id="pagnNextLink"]'
    _PRODUCT = '//li[contains(@id,"result_")]'
    _NAME = './/a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]'
    _PRICE_NEW = './/span[@class="a-size-base a-color-price s-price a-text-bold"]/text()'
    _PRICE_USED = './/span[@class="a-size-base a-color-price a-text-bold"]/text()'


global MAX_PAGE_COUNT;
global MIN_PERCENT_SAVING

def getProductDetailsPage(url):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
    COUNTER = 1

    while True:
        logging.debug('======PAGE '+ xstr(COUNTER) + '======')
        mod_url = url + '&page=' + xstr(COUNTER)
        COUNTER = COUNTER + 1
        page = requests.get(mod_url,headers=headers)
        doc = html.fromstring(page.content)
        readProductDetails(doc)
        if (not doc.xpath(Xpathdef._NEXT_PAGE)) or (COUNTER > MAX_PAGE_COUNT):
            break


def readProductDetails(document):
    for i in document.xpath(Xpathdef._PRODUCT):
        # print(html.tostring(i, pretty_print=True))
        RAW_NAME = i.xpath(Xpathdef._NAME)
        RAW_NEW_PRICE = i.xpath(Xpathdef._PRICE_NEW)
        RAW_USED_PRICE = i.xpath(Xpathdef._PRICE_USED)
        RAW_ASIN = i.get('data-asin')

        NAME = RAW_NAME[0].get('title').encode('utf-8') if RAW_NAME else None
        ASIN = RAW_ASIN if RAW_ASIN else None
        NEW_PRICE = re.sub(r'[^\d,]', '', str(RAW_NEW_PRICE[0])).replace(',', '.') if RAW_NEW_PRICE else None
        USED_PRICE = re.sub(r'[^\d,]', '', str(RAW_USED_PRICE[0])).replace(',', '.') if RAW_USED_PRICE else None
        LINK = 'https://www.amazon.de/gp/offer-listing/' + ASIN if RAW_ASIN else None

        saveItem(Product(ASIN, NAME, NEW_PRICE, USED_PRICE, LINK))

def saveItem(product):
    if not isinstance(product, Product):
        raise ValueError('Object must be an instance of Product!')
    # if product.used and not product.new:
        # product.new = getNewPrice(product.name)
    if (product.getDiff() and product.getDiff() > MIN_PERCENT_SAVING) or (product.used and not product.new):
        logging.info(product.toJson())

#TODO: WIP external price check
def getNewPrice(name):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
    logging.info('name: ' + name)
    search_name = name.split(' ', 2)
    del search_name[-1]
    searchBaseUrl = 'http://www.pricerunner.de/search?q='
    searchUrl = searchBaseUrl + '+'.join(search_name)
    logging.info('searchurl: ' + searchUrl )
    r = requests.get(searchUrl,headers=headers)
    doc = html.fromstring(r.content)
    raw_price = doc.xpath('//span[@class="amount"]/text()')
    price = re.sub(r'[^\d,]', '', str(raw_price[0])).replace(',', '.') if raw_price else None
    logging.info('price: ' + xstr(price))
    return price

def xstr(s):
    if s is None:
        return ''
    return str(s)

def run(filename):
    with open(filename) as f:
        content = f.readlines()
    for line in content:
        s = line.strip()
        if s == "":
            logging.debug('empty line, skipping....')
            continue
        if s.startswith('#'):
            logging.debug('commented out, skipping...')
            continue
        logging.info(line.strip() + "\n------------------------------------------------------\n")
        getProductDetailsPage(line.strip())

#TODO: WIP yaml load
def loadYaml(filename):
    f = open(filename)
    pageList = yaml.load(f)
    f.close()
    for page in pageList:
        print '-->' + i['name']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get crawling boundaries')
    parser.add_argument('-f', '--file', help='the file containing all urls to crawl. Defaults to: pages.txt', default='pages.txt')
    parser.add_argument('-s', '--saving', help='minimal percentage saving (default 30.0)', default=30.0, type=Decimal)
    parser.add_argument('-p', '--pages', help='Max pages to search (default 50)', default=50, type=int)
    parser.add_argument('-v', '--verbose', help='enable more verbose output', action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    MIN_PERCENT_SAVING = args.saving
    MAX_PAGE_COUNT = args.pages

    run(args.file)
    # loadYaml(args.file)
