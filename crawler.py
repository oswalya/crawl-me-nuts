from lxml import html
from decimal import Decimal
import csv
import os
import json
import requests
import re
import inspect

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


def ReadProductDetails(url):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    page = requests.get(url,headers=headers)
    doc = html.fromstring(page.content)

    XPATH_PRODUCT = '//li[contains(@id,"result_")]'
    XPATH_NAME = './/a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]'
    XPATH_PRICE_NEW = './/span[@class="a-size-base a-color-price s-price a-text-bold"]/text()'
    XPATH_PRICE_USED = './/span[@class="a-size-base a-color-price a-text-bold"]/text()'

    for i in doc.xpath(XPATH_PRODUCT):
        # print(html.tostring(i, pretty_print=True))
        RAW_NAME = i.xpath(XPATH_NAME)
        RAW_NEW_PRICE = i.xpath(XPATH_PRICE_NEW)
        RAW_USED_PRICE = i.xpath(XPATH_PRICE_USED)
        RAW_ASIN = i.get('data-asin')

        NAME = RAW_NAME[0].get('title') if RAW_NAME else None
        ASIN = RAW_ASIN if RAW_ASIN else None
        NEW_PRICE = re.sub(r'[^\d,]', '', str(RAW_NEW_PRICE[0])).replace(',', '.') if RAW_NEW_PRICE else None
        USED_PRICE = re.sub(r'[^\d,]', '', str(RAW_USED_PRICE[0])).replace(',', '.') if RAW_USED_PRICE else None
        LINK = 'https://www.amazon.de/gp/offer-listing/' + ASIN if RAW_ASIN else None

        saveItem(Product(ASIN, NAME, NEW_PRICE, USED_PRICE, LINK))


def saveItem(product):
    print "Name: " + xstr(product.name) + "\n"
    print "ASIN: " + xstr(product.asin) + "\n"
    print "NEW: " + xstr(product.new) + "\n"
    print "USED: " + xstr(product.used) + "\n"
    print "DIFF: " + xstr(product.getDiff()) + "\n"
    print "LINK: " + xstr(product.link) + "\n"
    print "\n"

def xstr(s):
    if s is None:
        return ''
    return str(s)

def Run():
    ReadProductDetails("https://www.amazon.de/gp/search/ref=sr_nr_p_89_0?fst=as%3Aoff&rh=n%3A562066%2Cn%3A%21569604%2Cn%3A761254%2Cn%3A1197292%2Cp_n_size_browse-bin%3A9590317031%7C9590316031%2Cp_n_feature_two_browse-bin%3A2711619031%2Cp_6%3AA8KICS1PHF7ZO%7CA3JWKAKR8XB7XF%2Cp_89%3ALG+Electronics&bbn=1197292&ie=UTF8&qid=1490774546")


if __name__ == "__main__":
    Run()
