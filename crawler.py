from lxml import html
import csv,os,json
import requests

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

        NAME = ' '.join(''.join(RAW_NAME[0].get("title")).split()) if RAW_NAME else 'Empty'
        NEW_PRICE = ' '.join(''.join(RAW_NEW_PRICE[0]).split()) if RAW_NEW_PRICE else 'Empty'
        USED_PRICE = ' '.join(''.join(RAW_USED_PRICE[0]).split()) if RAW_USED_PRICE else 'Empty'

        print NAME + "\n";
        print NEW_PRICE + "\n";
        print USED_PRICE + "\n";
        print "\n"


def Run():
    ReadProductDetails("https://www.amazon.de/gp/search/ref=sr_nr_p_89_0?fst=as%3Aoff&rh=n%3A562066%2Cn%3A%21569604%2Cn%3A761254%2Cn%3A1197292%2Cp_n_size_browse-bin%3A9590317031%7C9590316031%2Cp_n_feature_two_browse-bin%3A2711619031%2Cp_6%3AA8KICS1PHF7ZO%7CA3JWKAKR8XB7XF%2Cp_89%3ALG+Electronics&bbn=1197292&ie=UTF8&qid=1490774546")


if __name__ == "__main__":
    Run()
