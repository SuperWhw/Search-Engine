import time
import xml.etree.ElementTree as ET
import configparser
import csv
from tqdm import tqdm

import requests
from bs4 import BeautifulSoup
from faker import Faker
Faker.seed(5)


def get_soup(url, encoding="utf-8"):
    time.sleep(1)
    # use faker to create user_agent
    fake = Faker()
    headers = {
        "User-Agent": fake.internet_explorer(),
    }
    try:
        resp = requests.get(url, headers=headers)
        resp.encoding=encoding
        return BeautifulSoup(resp.text, features='lxml')
    except Exception as e:
        print("get_soup: %s : %s" % (type(e), url))
        return None


def get_news_item(category, root_url):
    news_list = []
    n_pages = 2 # scracth n pages for each category

    for c in category:
        url = root_url + c
        print(f'\nGet {n_pages} pages of news item in {url} ...')

        for page in tqdm(range(1,n_pages+1)):
            page_url = url + str(page) + '.shtml'
            soup = get_soup(page_url)
            if soup is None:
                continue
            news_ul = soup.find('ul', {'class': 'txt-list-a fz-14'})
            news_li = news_ul.find_all('li')
            for news in news_li:
                try:
                    # check if news is empty
                    if len(news.text) == 0:
                        continue

                    news_time = news.span.text
                    title = news.a.text.strip()
                    news_url = news.a['href']
                    news_info = {
                        "time":news_time,
                        "title": title,
                        "url": news_url
                    }
                    
                    news_list.append(news_info)
                except Exception as e:
                    print("get_news_item: %s : %s" % (type(e), url))
                    continue
    print('\nSuccessful get news list!\n')
    return news_list


def get_news_info(news_list, doc_file_path, doc_encoding="utf-8"):
    print('Get news info in news list ...\n')
    index = 1

    for news in tqdm(news_list):
        new_url = news.get('url')
        news_page = 1
        doc_text = ""

        # news may have more than one pages
        while True:
            if news_page == 1:
                soup = get_soup(new_url)
            else:
                soup = get_soup(new_url[:-6]+'_'+str(news_page)+'.shtml')
            
            try:
                doc = soup.find("div", {"class": "articleText"})   #find in web page
                if doc is None:
                    break
                doc_p = doc.find_all('p')
                for t in doc_p:
                    doc_text += t.text.strip()
            except Exception as e:
                print("get_news_info: %s : %s" % (type(e), new_url))
            
            news_page += 1

        # check if news url is empty
        if len(doc_text) == 0:
            continue

        # clean doc_text

        # write xml doc
        new_ET = ET.Element('news')
        ET.SubElement(new_ET, 'id').text = "%d"%(index)
        ET.SubElement(new_ET, 'url').text = news.get('url')
        ET.SubElement(new_ET, 'title').text = news.get('title')
        ET.SubElement(new_ET, 'datetime').text = news.get('time')
        ET.SubElement(new_ET, 'body').text = doc_text
        tree = ET.ElementTree(new_ET)
        tree.write(file_or_filename = doc_file_path+str(index)+'.xml', encoding = doc_encoding, xml_declaration = True)

        index += 1


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("./config.ini", encoding="utf-8")
    category = ['china/szyw/','science/ITyj/']
    root_url = "http://www.cankaoxiaoxi.com/"
    news_list = get_news_item(category, root_url)
    get_news_info(news_list, config['DEFAULT']['doc_file_path'])


# https://blog.csdn.net/qq_38130747/article/details/104638839
# http://bitjoy.net/2016/01/04/introduction-to-building-a-search-engine-2/