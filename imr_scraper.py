from bs4 import BeautifulSoup
import requests
import pickle
import hashlib
import logging
import json
import re

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
    data['Source'] = url
    bullets = bullets.split('\n')
    for item in bullets:
        if item:
            split = item.split(': ')
            if len(split) == 2:
                data[split[0]] = split[1]
            else:
                log.error('Unable to process bullet point: %s', item)
                if 'style' in item.lower():
                    if 'flat' in item.lower():
                        data['Style'] = 'Flat Top'
                    elif 'button' or 'nipple' in item.lower():
                        data['Style'] = 'Button/Nipple'

    # Consolidate columns
    for key in data:
        if 'dimensions' in key.lower():
            log.info('Found key: %s, renaming to "Dimensions".', key)
            data['Dimensions'] = data.pop(key)
        elif 'discharge' in key.lower():
            log.info('Found key: %s, renaming to "Discharge Current".', key)
            if type(data[key]) == type(str()):
                raw_string = data.pop(key)
                regex_match = re.match(r'[+-]?((\d+(\.\d*)?)|(\.\d+)) ?A', raw_string)
                if regex_match:
                    current = float(regex_match.group()[:-1])
                    data['Discharge Current (A)'] = current
                else:
                    data['Discharge Current (A)'] = None
        elif 'positive' in key.lower():
            log.info('Found key: %s, renaming to "Style".', key)
            data['Style'] = data.pop(key)
        elif 'weight' in key.lower():
            log.info('Found key: %s, value: %s, processing as "Weight (g)".', key, data[key])
            if type(data[key]) == type(str()):
                raw_string = data.pop(key)
                regex_match = re.match(r'[+-]?((\d+(\.\d*)?)|(\.\d+)) ?g', raw_string)
                if regex_match:
                    weight = float(regex_match.group()[:-1])
                    data['Weight (g)'] = weight
                else:
                    data['Weight (g)'] = None
        elif key == 'Nominal Capacity':
            log.info('Found key: %s, value: %s, processsing as "Nominal Capacity (mAh)".', key, data[key])
            raw_string = data.pop(key)
            regex_match = re.match(r'[+-]?((\d+(\.\d*)?)|(\.\d+)) ?mAh', raw_string)
            capacity = float(regex_match.group()[:-3])
            data[''.join([key, ' (mAh)'])] = capacity
        elif 'voltage' in key.lower():
            log.info('Found key: %s, value: %s, processsing as a voltage value.', key, data[key])
            if type(data[key]) != type(float()):
                data[key] = float(re.match(r'[+-]?((\d+(\.\d*)?)|(\.\d+)) ?V', data.pop(key)).group()[:-1])
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

