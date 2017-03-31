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

#TODO: Add documentation
class Product:
    def __init__(self, asin, name, price_new, price_used, link, price_external=None):
        self.asin = asin
        self.name = name
        self.new = price_new
        self.used = price_used
        self.link = link
        self.external = price_external

    def getDiff(self):
        if (self.new is None) or (self.used is None):
            return None
        value_new = Decimal(self.new)
        value_used = Decimal(self.used)
        return 100 * (value_new - value_used) / value_new

    def toJson(self):
        return json.dumps({'asin': self.asin, 'name': self.name, 'price_new': self.new, 'price_used': self.used, 'price_external': self.external, 'price_diff': str(self.getDiff()), 'link': self.link})

#TODO: Add documentation
class SearchItem:
    def __init__(self, name, url, useExternal, ext_baseurl, ext_xpath, ext_name_cut, asin_base_url):
        self.name = name
        self.url = url
        self.useExternal = useExternal
        self.ext_baseurl = ext_baseurl
        self.ext_xpath = ext_xpath
        self.ext_name_cut = ext_name_cut
        self.asin_base_url = asin_base_url

#TODO: Add documentation
class Xpathdef:
    _NEXT_PAGE = '//a[@id="pagnNextLink"]'
    _PRODUCT = '//li[contains(@id,"result_")]'
    _NAME = './/a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]'
    _PRICE_NEW = './/span[@class="a-size-base a-color-price s-price a-text-bold"]/text()'
    _PRICE_USED = './/span[@class="a-size-base a-color-price a-text-bold"]/text()'


global MAX_PAGE_COUNT
global MIN_PERCENT_SAVING
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

#TODO: Add documentation
def xstr(s):
    if s is None:
        return ''
    return str(s)

#TODO: Add documentation
def getProductDetailsPage(searchItem):
    COUNTER = 1
    logging.info('Scanning product pages for: ' + searchItem.name)

    while True:
        logging.debug('======PAGE '+ xstr(COUNTER) + '======')
        mod_url = searchItem.url + '&page=' + xstr(COUNTER)
        COUNTER = COUNTER + 1
        page = requests.get(mod_url,headers=headers)
        doc = html.fromstring(page.content)
        readProductDetails(doc, searchItem)
        if (not doc.xpath(Xpathdef._NEXT_PAGE)) or (COUNTER > MAX_PAGE_COUNT):
            break

#TODO: Add documentation
def readProductDetails(document, searchItem):
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
        LINK = searchItem.asin_base_url + '' + ASIN if RAW_ASIN else None

        p = Product(ASIN, NAME, NEW_PRICE, USED_PRICE, LINK)
        if searchItem.useExternal:
            logging.debug('Trying to get more price information from external site for: ' + p.name)
            price = getNewPrice(p.name, searchItem)
            if price:
                logging.debug('Found price: ' + price)
                p.external = price
        saveItem(p)

#TODO: Add documentation
def saveItem(product):
    if not isinstance(product, Product):
        raise ValueError('Object must be an instance of Product!')
    # if product.used and not product.new:
        # product.new = getNewPrice(product.name)
    # if (product.getDiff() and product.getDiff() > MIN_PERCENT_SAVING) or (product.used and not product.new):
    #     logging.info(product.toJson())
    if (product.getDiff() and product.getDiff() > MIN_PERCENT_SAVING):
        logging.info(product.toJson())

#TODO: Add documentation
def getNewPrice(name, searchItem):
    # split search strings by whitespace for searchItem.ext_name_cut whitespaces
    search_name = name.split(' ', searchItem.ext_name_cut)
    # if there are more items, they will be append as last element to the list, so I need to remove them
    if len(search_name) > searchItem.ext_name_cut:
        del search_name[-1]
    # search for that item on the external site
    searchUrl = searchItem.ext_baseurl + '+'.join(search_name)
    r = requests.get(searchUrl,headers=headers)
    doc = html.fromstring(r.content)
    # extract price element and return value if found, else None is returned
    raw_price = doc.xpath(searchItem.ext_xpath)
    price = re.sub(r'[^\d,]', '', str(raw_price[0])).replace(',', '.') if raw_price else None
    return price

#TODO: Add documentation
def loadYaml(filename):
    f = open(filename)
    itemList = yaml.load(f)
    f.close()
    searchItems = []
    for item in itemList:
        if not item['url']:
            logging.debug(item['name'] + ' will be skipped: url empty / commented out....')
            continue
        item = SearchItem(item['name'], item['url'].strip() ,item['external_price'], item['external_price_baseurl'], item['external_price_xpath'], item['external_price_cut_name'], item['asin_base_url'])
        logging.info('Adding SearchItem: ' + item.name)
        searchItems.append(item)
    return searchItems

#TODO: Add documentation
def run(filename):
    searchItems = loadYaml(filename)
    for item in searchItems:
        getProductDetailsPage(item)

#TODO: Add documentation
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get crawling boundaries')
    parser.add_argument('-f', '--file', help='the file containing all urls to crawl. Defaults to: pages.yml', default='pages.yml')
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
