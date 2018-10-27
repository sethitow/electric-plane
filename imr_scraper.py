from bs4 import BeautifulSoup
import requests
import pickle
import hashlib
import logging
import json

def get_content(url):
    log.info('Getting contents for URL %s', url)
    file_name = ''.join([hashlib.sha1(url.encode('utf-8')).hexdigest(), '.pickle'])
    try:
        with open(file_name, 'rb') as file:
            log.info('Cache file opened, loading pickle.')
            r = pickle.load(file)
    except FileNotFoundError as e:
        log.info('Got FileNotFoundError, making GET request.')
        r = requests.get(url)
        with open(file_name, 'wb') as file:
            pickle.dump(r, file)
    return r.content

def get_bullets(content):
    soup = BeautifulSoup(content, 'html.parser')
    prod_desc = soup.find_all('div', {"class": "ProductDescriptionContainer"})
    return prod_desc[0].find_all('ul')[0].get_text()

def parse_bullets(bullets, url=None):
    data = {}
    bullets = bullets.split('\n')
    for item in bullets:
        if item:
            split = item.split(': ')
            try:
                data[split[0]] = split[1]
            except IndexError:
                log.exception('Unable to process bullet point: %s', item)
    data['source'] = url
    return data

def get_urls(content):
    soup = BeautifulSoup(content, 'html.parser')
    prod_list = soup.find_all('ul', {"class": "ProductList"})
    list_items = prod_list[0].find_all('li')
    url_list = []
    for item in list_items:
        a = item.find_all('div',{"class": "ProductImage"})[0].find_all('a')
        url_list.append(a[0]['href'])
    return url_list


if __name__ == '__main__':

    log = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    url_18650 = 'https://www.imrbatteries.com/18650-batteries/'
    all_battery_data = []
    for url in get_urls(get_content(url_18650)):
        content = get_content(url)
        bullets = get_bullets(content)
        data = parse_bullets(bullets, url)
        all_battery_data.append(data)
    with open('18650_data.json', 'w') as file:
        json.dump(all_battery_data, file)

