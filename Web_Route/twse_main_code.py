import os
import time
from tqdm import tqdm
from datetime import datetime, timedelta, date
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup, Comment
import re
import requests
from collections import deque
import random
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from openpyxl import load_workbook
from logbook import Logger, StreamHandler
import sys
from fake_useragent import UserAgent
from loguru import logger

import tejapi
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

base = config['TEJ']['base']
key = config['TEJ']['key']

tejapi.ApiConfig.api_base = base
tejapi.ApiConfig.api_key = key
tejapi.ApiConfig.ignoretz = True

now = datetime.now()
ua = UserAgent()
ua = ua.random
headers = {'user-agent':ua}

log = Logger('Web_Route')
StreamHandler(sys.stdout).push_application()

chrome_options = Options() # 設定自動開瀏覽器的方法
chrome_options.add_argument("--start-maximized")  # 可選：最大化瀏覽器窗口
chrome_options.add_argument("--headless") # 無頭模式,不打開瀏覽器視窗
chrome_options.add_argument("--proxy-pac-url") # 設定proxy,但好像沒用
chrome_options.add_argument(f"--user-agent={ua}")
# data_dict = {'WEBSITE_ID':'', 'MAP_ROUTE':'', 'LINK':'', 'TABLE_FG':'', 'ATTACHMENT_FG':'', 'FORM_FG':'', 'CSV_AND_HTML_BUTTON_FG':''} # 設定dictionary
# api_url_list=[]
data_df = pd.DataFrame(columns=['WEBSITE_ID', 'MAP_ROUTE', 'LINK', 'TABLE_FG', 'ATTACHMENT_FG', 'FORM_FG', 'CSV_AND_HTML_BUTTON_FG', 'API_URL'])

from identify_date_select import identify_date_select
from handle_api import get_api, api_url_generator
from date_params import get_date_interval
from date_handler import DateHandler
from get_api_JsonData import get_api_Data
from sitemap_content import crawler_content, def_crawler_content_with_table
from enter_coid import enter_coid
from exception_url import Stock_Selection_Criteria
from get_twse_link import get_twse_link

def web_process(url):
    global data_df, url_list, api_url_list
    queue =deque()
    queue.append(url)
    while(queue):
        link_exist = [df_link for df_link in data_df["LINK"]]
        url = queue.popleft()
        # if url in link_exist:
        #     print(f"{url} - 此網頁已處理！")
        #     continue
        # else:
        #     pass
    
    data_link = pd.read_excel("../output/link/output_link.xlsx")
    if url == "https://www.twse.com.tw/zh/products/broker/infomation/summary.html":
        route = data_link[data_link['LINK'] == "https://www.twse.com.tw/zh/products/broker/infomation/list.html"]['MAP_ROUTE'].iloc[0]
    else:
        route = data_link[data_link['LINK'] == url]['MAP_ROUTE'].iloc[0]
    print(route, '\n')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(3)
    resd = driver.page_source
    soup = BeautifulSoup(resd, 'lxml')
    try:
        popup = driver.find_element(By.CLASS_NAME,"ok")
        popup.click()
    except:
        pass
    
    if url != "https://www.twse.com.tw/zh/listed/selection-criteria.html":
        calendar_dict, menu_dict = identify_date_select(soup, driver, url)
        print(calendar_dict, menu_dict)
        params_of_date, date_options = get_date_interval(calendar_dict)
        coid_list = enter_coid()

        type_options = list(menu_dict.keys())
        if 'sortKind' in type_options:
            logger.info("Delete the type options -> sortKind")
            del menu_dict['sortKind']
        elif 'stockDays' in type_options:
            logger.info('Delete the type options -> stockDays')
            del menu_dict['stockDays']
        else:
            pass
    else:
        logger.info("此網址要例外處理")
        date_options, menu_name_dict, menu_query_dict = Stock_Selection_Criteria(soup, driver)

    try:
        data_api = get_api(url)
    except:
        data_api = ""
        api_url = ""

    if date_options == "interval":
        if len(menu_dict) == 0:
            logger.info(f"日期區間，無下拉式選單！")
            api_url = api_url_generator(data_api, params_of_date)
            print(api_url)
            Json_Data = get_api_Data(api_url)
            if Json_Data['status'] == "OK":
                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                    table = False
                else:
                    table = True
                data_dict = crawler_content(soup, url, table, route, api_url)
                logger.success(data_dict)
                print(data_dict)
                df_dict = pd.DataFrame(data_dict, index=[0])
                data_df = pd.concat([data_df, df_dict], ignore_index=True)
            else:
                try:
                    log.warning(f"{Json_Data['status']}")
                    start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                    no_raw_date = Json_Data['status']
                    pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                    matches = re.findall(pattern, no_raw_date)

                    year, month, day = matches[0]
                    month = month.zfill(2)
                    day = day.zfill(2)
                    AD_year = int(year) + 1911
                    minimum_date = f"{AD_year}{month}{day}"
                    params_of_date = params_of_date.replace(start_date, minimum_date)

                    api_url = api_url_generator(data_api, params_of_date)
                    print(api_url)
                    Json_Data = get_api_Data(api_url)
                    if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                        table = False
                    else:
                        table = True
                    data_dict = crawler_content(soup, url, table, route, api_url)
                    logger.success(data_dict)
                    print(data_dict)
                    df_dict = pd.DataFrame(data_dict, index=[0])
                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
                except:
                    logger.info(f"{Json_Data['status']}")
                    table = False
                    data_dict = crawler_content(soup, url, table, route, api_url)
                    logger.success(data_dict)
                    print(data_dict)
                    df_dict = pd.DataFrame(data_dict, index=[0])
                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
        elif len(menu_dict) == 1:
            logger.info(f"日期區間迭代單一下拉式選單或股票輸入格！")
            type_options = list(menu_dict.keys())
            dict1 = menu_dict[type_options[0]]
            for (key1, value1) in dict1.items():
                if type_options[0] == "stockNo" or "stockNo" in value1:
                    for stock in coid_list:
                        time.sleep(2)
                        value_stock = value1 + stock
                        key_stock = key1 + f"{stock}"
                        check_route = route+">>"+key_stock
                        if check_route in data_df['MAP_ROUTE'].unique():
                            logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                            continue
                        api_url = api_url_generator(data_api, params_of_date, value_stock)
                        print(api_url)
                        Json_Data = get_api_Data(api_url)
                        if Json_Data['status'] == "OK":
                            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                table = False
                            else:
                                table = True
                            data_dict = crawler_content(soup, url, table, route, api_url, key_stock)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                        else:
                            try:
                                start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                                no_raw_date = Json_Data['status']
                                pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                                matches = re.findall(pattern, no_raw_date)
                                log.warning(f"{Json_Data['status']}")
                                year, month, day = matches[0]
                                month = month.zfill(2)
                                day = day.zfill(2)
                                AD_year = int(year) + 1911
                                minimum_date = f"{AD_year}{month}{day}"
                                params_of_date = params_of_date.replace(start_date, minimum_date)

                                api_url = api_url_generator(data_api, params_of_date, value_stock)
                                print(api_url)
                                time.sleep(2)
                                Json_Data = get_api_Data(api_url)
                                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                    table = False
                                else:
                                    table = True
                                data_dict = crawler_content(soup, url, table, route, api_url, key_stock)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                            except:
                                logger.info(f"{Json_Data['status']}")
                                table = False
                                data_dict = crawler_content(soup, url, table, route, api_url, key_stock)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                else:
                    check_route = route+">>"+key1
                    if check_route in data_df['MAP_ROUTE'].unique():
                        logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                        continue
                    api_url = api_url_generator(data_api, params_of_date, value1)
                    print(api_url)
                    Json_Data = get_api_Data(api_url)
                    if Json_Data['status'] == "OK":
                        if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                            table = False
                        else:
                            table = True
                        data_dict = crawler_content(soup, url, table, route, api_url, key1)
                        logger.success(data_dict)
                        print(data_dict)
                        df_dict = pd.DataFrame(data_dict, index=[0])
                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                    else:
                        try:
                            log.warning(f"{Json_Data['status']}")
                            start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                            no_raw_date = Json_Data['status']
                            pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                            matches = re.findall(pattern, no_raw_date)

                            year, month, day = matches[0]
                            month = month.zfill(2)
                            day = day.zfill(2)
                            AD_year = int(year) + 1911
                            minimum_date = f"{AD_year}{month}{day}"
                            params_of_date = params_of_date.replace(start_date, minimum_date)

                            api_url = api_url_generator(data_api, params_of_date, value1)
                            print(api_url)
                            time.sleep(2)
                            Json_Data = get_api_Data(api_url)
                            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                table = False
                            else:
                                table = True
                            data_dict = crawler_content(soup, url, table, route, api_url, key1)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                        except:
                            logger.info(f"{Json_Data['status']}")
                            table = False
                            data_dict = crawler_content(soup, url, table, route, api_url, key1)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
        elif len(menu_dict) == 2:
            logger.info(f"日期區間迭代兩個下拉式選單或股票輸入格！")
            type_options = list(menu_dict.keys())
            dict1 = menu_dict[type_options[0]]
            dict2 = menu_dict[type_options[1]]
            for (key1, value1) in dict1.items():
                for (key2, value2) in dict2.items():
                    if "STKNO" in value1:
                        for stock in coid_list:
                            value_stock = value1 + f"&stockNo={stock}"
                            time.sleep(3)
                            key_stock = key1 + f"{stock}"
                            check_route = route+">>"+key_stock+">>"+key2
                            if check_route in data_df['MAP_ROUTE'].unique():
                                logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                                continue
                            api_url = api_url_generator(data_api, params_of_date, value_stock, value2)
                            print(api_url)
                            Json_Data = get_api_Data(api_url)
                            if Json_Data['status'] == "OK":
                                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                    table = False
                                else:
                                    table = True
                                selectName_Route = key_stock+">>"+key2
                                data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                            else:
                                try:
                                    log.warning(f"{Json_Data['status']}")
                                    start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                                    no_raw_date = Json_Data['status']
                                    pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                                    matches = re.findall(pattern, no_raw_date)

                                    year, month, day = matches[0]
                                    month = month.zfill(2)
                                    day = day.zfill(2)
                                    AD_year = int(year) + 1911
                                    minimum_date = f"{AD_year}{month}{day}"
                                    params_of_date = params_of_date.replace(start_date, minimum_date)
                                    api_url = api_url_generator(data_api, params_of_date, value_stock, value2)
                                    print(api_url)
                                    Json_Data = get_api_Data(api_url)
                                    if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                        table = False
                                    else:
                                        table = True
                                    selectName_Route = key_stock+">>"+key2
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                except:
                                    logger.info(f"{Json_Data['status']}")
                                    table = False
                                    selectName_Route = key_stock+">>"+key2
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)

                    elif "stockNo" in value1:
                        for stock in coid_list:
                            time.sleep(3)
                            value_stock = value1 + stock
                            key_stock = key1 + f"{stock}"
                            check_route = route+">>"+key_stock+">>"+key2
                            if check_route in data_df['MAP_ROUTE'].unique():
                                logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                                continue
                            api_url = api_url_generator(data_api, params_of_date, value_stock, value2)
                            print(api_url)
                            Json_Data = get_api_Data(api_url)
                            if Json_Data['status'] == "OK":
                                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                    table = False
                                else:
                                    table = True
                                selectName_Route = key_stock+">>"+key2
                                data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                            else:
                                try:
                                    log.warning(f"{Json_Data['status']}")
                                    start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                                    no_raw_date = Json_Data['status']
                                    pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                                    matches = re.findall(pattern, no_raw_date)

                                    year, month, day = matches[0]
                                    month = month.zfill(2)
                                    day = day.zfill(2)
                                    AD_year = int(year) + 1911
                                    minimum_date = f"{AD_year}{month}{day}"
                                    params_of_date = params_of_date.replace(start_date, minimum_date)
                                    api_url = api_url_generator(data_api, params_of_date, value_stock, value2)
                                    print(api_url)
                                    Json_Data = get_api_Data(api_url)
                                    if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                        table = False
                                    else:
                                        table = True
                                    selectName_Route = key_stock+">>"+key2
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                except:
                                    logger.info(f"{Json_Data['status']}")
                                    table = False
                                    selectName_Route = key_stock+">>"+key2
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)

                    elif "stockNo" in value2:
                        for stock in coid_list:
                            time.sleep(3)
                            value_stock = value2 + stock
                            key_stock = key2 + f"{stock}"
                            check_route = route+">>"+key1+">>"+key_stock
                            if check_route in data_df['MAP_ROUTE'].unique():
                                logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                                continue
                            api_url = api_url_generator(data_api, params_of_date, value1, value_stock)
                            if url == "https://www.twse.com.tw/zh/products/sbl/disclosures/t13sa710.html":
                                match = re.search(r'tradeType=([^&]*)', api_url)
                                if match and stock == '1101':
                                    tradeType = match.group(1)
                                    if tradeType == 'F':
                                        print("日期區間拉最大")
                                    else:
                                        print("拉 2024 年年初")
                                        api_url = api_url.replace('19900101', '20240101')
                            print(api_url)
                            Json_Data = get_api_Data(api_url)
                            if Json_Data['status'] == "OK":
                                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                    table = False
                                else:
                                    table = True
                                selectName_Route = key1+">>"+key_stock
                                data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                            else:
                                try:
                                    log.warning(f"{Json_Data['status']}")
                                    start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                                    no_raw_date = Json_Data['status']
                                    pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                                    matches = re.findall(pattern, no_raw_date)

                                    year, month, day = matches[0]
                                    month = month.zfill(2)
                                    day = day.zfill(2)
                                    AD_year = int(year) + 1911
                                    minimum_date = f"{AD_year}{month}{day}"
                                    params_of_date = params_of_date.replace(start_date, minimum_date)
                                    api_url = api_url_generator(data_api, params_of_date, value1, value_stock)
                                    print(api_url)
                                    Json_Data = get_api_Data(api_url)
                                    if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                        table = False
                                    else:
                                        table = True
                                    selectName_Route = key1+">>"+key_stock
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                except:
                                    logger.info(f"{Json_Data['status']}")
                                    table = False
                                    selectName_Route = key1+">>"+key_stock
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)

                    else:
                        check_route = route+">>"+key1+">>"+key2
                        if check_route in data_df['MAP_ROUTE'].unique():
                            logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                            continue
                        api_url = api_url_generator(data_api, params_of_date, value1, value2)
                        print(api_url)
                        Json_Data = get_api_Data(api_url)
                        time.sleep(3)
                        if Json_Data['status'] == "OK":
                            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                table = False
                            else:
                                table = True
                            selectName_Route = key1+">>"+key2
                            data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                        else:
                            try:
                                log.warning(f"{Json_Data['status']}")
                                start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                                no_raw_date = Json_Data['status']
                                pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                                matches = re.findall(pattern, no_raw_date)

                                year, month, day = matches[0]
                                month = month.zfill(2)
                                day = day.zfill(2)
                                AD_year = int(year) + 1911
                                minimum_date = f"{AD_year}{month}{day}"
                                params_of_date = params_of_date.replace(start_date, minimum_date)
                                api_url = api_url_generator(data_api, params_of_date, value1, value2)
                                print(api_url)
                                Json_Data = get_api_Data(api_url)
                                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                    table = False
                                else:
                                    table = True
                                selectName_Route = key1+">>"+key2
                                data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                            except:
                                logger.info(f"{Json_Data['status']}")
                                table = False
                                selectName_Route = key1+">>"+key2
                                data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
        elif len(menu_dict) == 3:
            logger.info(f"日期區間迭代三個下拉式選單或股票輸入格！")
            type_options = list(menu_dict.keys())
            dict1 = menu_dict[type_options[0]]
            dict2 = menu_dict[type_options[1]]
            dict3 = menu_dict[type_options[2]]
            for (key1, value1) in dict1.items():
                for (key2, value2) in dict2.items():
                    for (key3, value3) in dict3.items():
                        if "stockNo" in value1:
                            for stock in coid_list:
                                value_stock = value1 + stock
                                key_stock = key1 + f"{stock}"
                                check_route = route+">>"+key_stock+">>"+key2+">>"+key3
                                if check_route in data_df['MAP_ROUTE'].unique():
                                    logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                                    continue
                                api_url = api_url_generator(data_api, params_of_date, value_stock, value2, value3)
                                print(api_url)
                                time.sleep(3)
                                Json_Data = get_api_Data(api_url)
                                if Json_Data['status'] == "OK":
                                    if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                        table = False
                                    else:
                                        table = True
                                    selectName_Route = key_stock+">>"+key2+">>"+key3
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                else:
                                    try:
                                        log.warning(f"{Json_Data['status']}")
                                        start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                                        no_raw_date = Json_Data['status']
                                        pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                                        matches = re.findall(pattern, no_raw_date)

                                        year, month, day = matches[0]
                                        month = month.zfill(2)
                                        day = day.zfill(2)
                                        AD_year = int(year) + 1911
                                        minimum_date = f"{AD_year}{month}{day}"
                                        params_of_date = params_of_date.replace(start_date, minimum_date)
                                        api_url = api_url_generator(data_api, params_of_date, value_stock, value2, value3)
                                        print(api_url)
                                        Json_Data = get_api_Data(api_url)
                                        if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                            table = False
                                        else:
                                            table = True
                                        selectName_Route = key_stock+">>"+key2+">>"+key3
                                        data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                        logger.success(data_dict)
                                        print(data_dict)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    except:
                                        logger.info(f"{Json_Data['status']}")
                                        table = False
                                        selectName_Route = key_stock+">>"+key2+">>"+key3
                                        data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                        logger.success(data_dict)
                                        print(data_dict)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                        else:
                            check_route = route+">>"+key1+">>"+key2+">>"+key3
                            if check_route in data_df['MAP_ROUTE'].unique():
                                logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                                continue
                            api_url = api_url_generator(data_api, params_of_date, value1, value2, value3)
                            print(api_url)
                            time.sleep(3)
                            Json_Data = get_api_Data(api_url)
                            if Json_Data['status'] == "OK":
                                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                    table = False
                                else:
                                    table = True
                                selectName_Route = key1+">>"+key2+">>"+key3
                                data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                            else:
                                try:
                                    log.warning(f"{Json_Data['status']}")
                                    start_date = re.search(r'startDate=(\d+)', params_of_date).group(1)
                                    no_raw_date = Json_Data['status']
                                    pattern = r'(\d{2,3})年(\d{1,2})月(\d{1,2})日'
                                    matches = re.findall(pattern, no_raw_date)

                                    year, month, day = matches[0]
                                    month = month.zfill(2)
                                    day = day.zfill(2)
                                    AD_year = int(year) + 1911
                                    minimum_date = f"{AD_year}{month}{day}"
                                    params_of_date = params_of_date.replace(start_date, minimum_date)
                                    api_url = api_url_generator(data_api, params_of_date, value1, value2, value3)
                                    print(api_url)
                                    Json_Data = get_api_Data(api_url)
                                    if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                        table = False
                                    else:
                                        table = True
                                    selectName_Route = key1+">>"+key2+">>"+key3
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                except:
                                    logger.info(f"{Json_Data['status']}")
                                    table = False
                                    selectName_Route = key1+">>"+key2+">>"+key3
                                    data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                    logger.success(data_dict)
                                    print(data_dict)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
        elif len(menu_dict) == 4:
            logger.info(f"日期區間迭代四個下拉式選單或股票輸入格！")
            type_options = list(menu_dict.keys())
            dict1 = menu_dict[type_options[0]]
            dict2 = menu_dict[type_options[1]]
            dict3 = menu_dict[type_options[2]]
            dict4 = menu_dict[type_options[3]]
    elif date_options == "none":
        if len(menu_dict) == 0:
            tab_links = soup.find('div',attrs={'class':'tab-links'})
            if tab_links == None:
                logger.info(f"沒有日期選單，也沒有下拉式選單！")
                no_form = True
                api_url = ""
                data_dict = def_crawler_content_with_table(soup, url, no_form, route, api_url)
                logger.success(data_dict)
                print(data_dict)
                df_dict = pd.DataFrame(data_dict, index=[0])
                data_df = pd.concat([data_df, df_dict], ignore_index=True)
            else:
                logger.info(f"沒有日期選單，也沒有下拉式選單，但是網頁內有同樣MAP_ROUTE的超連結！")
                tab_links_items = tab_links.find_all('li')
                non_active_item = []
                non_active_link = []
                for item in tab_links_items:
                    if "active" in item.get('class', []):
                        active_item = item
                        active_text = active_item.text.strip()
                        active_link = active_item.a['href']
                        no_form = True
                        api_url = ""
                        data_dict = def_crawler_content_with_table(soup, url, no_form, route, api_url, selectName=active_text)
                        logger.success(data_dict)
                        print(data_dict)
                        df_dict = pd.DataFrame(data_dict, index=[0])
                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                    else:
                        non_active_item.append(item.text.strip())
                        non_active_link.append(item.a['href'])

                for hyperlink in non_active_link:
                    hyperurl = url.replace(active_link, hyperlink)
                    print(f'網頁超連結網址：{hyperurl}')
                    time.sleep(2)
                    web_process(hyperurl)
        elif len(menu_dict) == 1:
            dict1 = menu_dict[type_options[0]]
            for (key1, value1) in dict1.items():
                if type_options[0] == "stockNo":
                    if len(data_api) == 0:     # 針對 https://www.twse.com.tw/zh/products/securities/warrant/infomation/profile.html 的處理
                        table = False
                        data_dict = crawler_content(soup, url, table, route, api_url)
                        logger.success(data_dict)
                        print(data_dict)
                        df_dict = pd.DataFrame(data_dict, index=[0])
                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                    else:
                        logger.info(f"股票輸入格！")
                        for stock in coid_list:
                            value_stock = value1 + stock
                            key_stock = key1 + f"{stock}"
                            api_url = api_url_generator(data_api, params_of_date, value_stock)
                            print(api_url)
                            time.sleep(3)
                            Json_Data = get_api_Data(api_url)
                            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                table = False
                            else:
                                table = True
                            data_dict = crawler_content(soup, url, table, route, api_url, key_stock)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                else:
                    if "law" in url:
                        api_url = api_url_generator(data_api)
                        print(api_url)
                        time.sleep(3)
                        Json_Data = get_api_Data(api_url)
                        if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                            table = False
                        else:
                            table = True
                        data_dict = crawler_content(soup, url, table, route, api_url)
                        logger.success(data_dict)
                        print(data_dict)
                        df_dict = pd.DataFrame(data_dict, index=[0])
                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                    else:
                        print("目前還沒遇到！")
        elif len(menu_dict) == 2:
            dict1 = menu_dict[type_options[0]]
            dict2 = menu_dict[type_options[1]]
            for (key1, value1) in dict1.items():
                for (key2, value2) in dict2.items():
                    if type_options[0] == "stockNo":
                        logger.info(f"股票輸入格！")
                        pass
                    else:
                        logger.info(f"兩個下拉式選單或股票輸入格！")
                        check_route = route+">>"+key1+">>"+key2
                        if check_route in data_df['MAP_ROUTE'].unique():
                            logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                            continue
                        api_url = api_url_generator(data_api, params_of_date, value1, value2)
                        print(api_url)
                        time.sleep(3)
                        try:
                            Json_Data = get_api_Data(api_url)
                            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                table = False
                            else:
                                table = True
                            selectName_Route = key1+">>"+key2
                            data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                        except:
                            random_number = random.randint(1,1999999999999)
                            api_url_res = api_url + f"&response=json&_={random_number}"
                            print(api_url_res)
                            Json_Data = get_api_Data(api_url_res)
                            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                table = False
                            else:
                                table = True
                            selectName_Route = key1+">>"+key2
                            data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
        elif len(menu_dict) == 4:
            logger.info(f"沒有日期選單，四個下拉式選單或股票輸入格！")
            type_options = list(menu_dict.keys())
            dict1 = menu_dict[type_options[0]]
            dict2 = menu_dict[type_options[1]]
            dict3 = menu_dict[type_options[2]]
            dict4 = menu_dict[type_options[3]]
            for (key1, value1) in dict1.items():
                for (key2, value2) in dict2.items():
                    for (key3, value3) in dict3.items():
                        for (key4, value4) in dict4.items():
                            check_route = route+">>"+key1+">>"+key2+">>"+key3+">>"+key4
                            if check_route in data_df['MAP_ROUTE'].unique():
                                logger.debug(f"重複的MAP_ROUTE不處理 -> {check_route}")
                                continue
                            api_url = api_url_generator(data_api, params_of_date, value1, value2, value3, value4)
                            print(api_url)
                            time.sleep(2)
                            Json_Data = get_api_Data(api_url)
                            if Json_Data['status'] == "OK":
                                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                    table = False
                                else:
                                    table = True
                                selectName_Route = key1+">>"+key2+">>"+key3+">>"+key4
                                data_dict = crawler_content(soup, url, table, route, api_url, selectName_Route)
                                logger.success(data_dict)
                                print(data_dict)
                                df_dict = pd.DataFrame(data_dict, index=[0])
                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
    elif date_options == "MWD":
        logger.info(f"總共有三個日期選項 - 月、週、日")
        for (key1, value1) in params_of_date.items():
            api_url = api_url_generator(data_api, value1)
            print(api_url)
            time.sleep(3)
            Json_Data = get_api_Data(api_url)
            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                match_type = re.search(r"type=(day|month|week)", value1)
                calendar_type = match_type.group(1)
                match = re.search(r'Date=(\d+)', value1)
                date_match = match.group(1)
                date_handler = DateHandler(date_match)
                logger.info(f"{date_match}-{key1}無資料")
                if calendar_type == 'day':
                    past = value1.replace(date_match, date_handler.previous_workday())
                elif calendar_type == 'week':
                    past = value1.replace(date_match, date_handler.previous_ww())
                elif calendar_type == 'month':
                    past = value1.replace(date_match, date_handler.previous_mm())

                api_url = api_url_generator(data_api, past)
                print(api_url)
                time.sleep(3)
                Json_Data = get_api_Data(api_url)
                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                    table = False
                else:
                    table = True
                data_dict = crawler_content(soup, url, table, route, api_url, key1)
                logger.success(data_dict)
                print(data_dict)
                df_dict = pd.DataFrame(data_dict, index=[0])
                data_df = pd.concat([data_df, df_dict], ignore_index=True)
            else:
                table = True
                data_dict = crawler_content(soup, url, table, route, api_url, key1)
                logger.success(data_dict)
                print(data_dict)
                df_dict = pd.DataFrame(data_dict, index=[0])
                data_df = pd.concat([data_df, df_dict], ignore_index=True)
    elif date_options == "exception_url":
        logger.info(f"例外處理網頁 -> {url}")
        for (key1, value1) in menu_name_dict.items():
            dict_options = menu_query_dict[key1]
            for (key2, value2) in dict_options.items():
                api_url = api_url_generator(data_api, key1, key2)
                random_number = random.randint(1,1999999999999)
                api_url_res = api_url + f"&response=json&_={random_number}"
                print(api_url_res)
                time.sleep(3)
                Json_Data = get_api_Data(api_url_res)
                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                    table = False
                else:
                    table = True
                data_dict = crawler_content(soup, url, table, route, api_url_res, value1+">>"+value2)
                logger.success(data_dict)
                print(data_dict)
                df_dict = pd.DataFrame(data_dict, index=[0])
                data_df = pd.concat([data_df, df_dict], ignore_index=True)
    else:
        if len(menu_dict) == 0:
            logger.info(f"單一日期，沒有下拉式選單！")
            api_url = api_url_generator(data_api, params_of_date)
            print(api_url)
            time.sleep(2)
            Json_Data = get_api_Data(api_url)
            tab_links = soup.find('div',attrs={'class':'tab-links'})
            if tab_links == None:
                active_text = ''
            else:
                tab_links_items = tab_links.find_all('li')
                active_text = ''.join([item.text for item in tab_links_items if "active" in item.get('class', [])])
            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                match = re.search(r'date=(\d+)', params_of_date)
                date_match = match.group(1)
                date_handler = DateHandler(date_match)
                logger.info(f"{date_match}無資料")
                calendar_type = date_options[-1]
                if calendar_type == 'D':
                    past = params_of_date.replace(date_match, date_handler.previous_workday())
                elif calendar_type == 'W':
                    past = params_of_date.replace(date_match, date_handler.previous_ww())
                elif calendar_type == 'M':
                    past = params_of_date.replace(date_match, date_handler.previous_mm())
                elif calendar_type == 'Y':
                    past = params_of_date.replace(date_match, date_handler.previous_yy())
                elif calendar_type == 'A':
                    past = params_of_date + str(now.year) + "0101"
                api_url = api_url_generator(data_api, past)
                print(api_url)
                Json_Data = get_api_Data(api_url)
                if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                    table = False
                else:
                    table = True
                data_dict = crawler_content(soup, url, table, route, api_url, selectName=active_text)
                logger.success(data_dict)
                print(data_dict)
                df_dict = pd.DataFrame(data_dict, index=[0])
                data_df = pd.concat([data_df, df_dict], ignore_index=True)
            else:
                table = True
                data_dict = crawler_content(soup, url, table, route, api_url, selectName=active_text)
                logger.success(data_dict)
                print(data_dict)
                df_dict = pd.DataFrame(data_dict, index=[0])
                data_df = pd.concat([data_df, df_dict], ignore_index=True)
        elif len(menu_dict) == 1:
            dict1 = menu_dict[type_options[0]]
            for (key1, value1) in dict1.items():
                if type_options[0] == "stockNo":
                    logger.info(f"單一日期迭代股票輸入格！")
                    for stock in coid_list:
                        value_stock = value1 + stock
                        key_stock = key1 + f"{stock}"
                        api_url = api_url_generator(data_api, params_of_date, value_stock)
                        print(api_url)
                        time.sleep(3)
                        Json_Data = get_api_Data(api_url)
                        if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                            match = re.search(r'date=(\d+)', params_of_date)
                            date_match = match.group(1)
                            date_handler = DateHandler(date_match)
                            logger.info(f"{date_match}-{key1}無資料")
                            calendar_type = date_options[-1]
                            if calendar_type == 'D':
                                past = params_of_date.replace(date_match, date_handler.previous_workday())
                            elif calendar_type == 'W':
                                past = params_of_date.replace(date_match, date_handler.previous_ww())
                            elif calendar_type == 'M':
                                past = params_of_date.replace(date_match, date_handler.previous_mm())
                            elif calendar_type == 'Y':
                                past = params_of_date.replace(date_match, date_handler.previous_yy())
                            elif calendar_type == 'A':
                                past = params_of_date + str(now.year) + "0101"
                            api_url = api_url_generator(data_api, past, value_stock)
                            print(api_url)
                            time.sleep(3)
                            Json_Data = get_api_Data(api_url)
                            if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                                table = False
                            else:
                                table = True
                            data_dict = crawler_content(soup, url, table, route, api_url, key_stock)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                        else:
                            table = True
                            data_dict = crawler_content(soup, url, table, route, api_url, key_stock)
                            logger.success(data_dict)
                            print(data_dict)
                            df_dict = pd.DataFrame(data_dict, index=[0])
                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                else:
                    logger.info(f"單一日期迭代下拉式選單！")
                    api_url = api_url_generator(data_api, params_of_date, value1)
                    print(api_url)
                    Json_Data = get_api_Data(api_url)
                    time.sleep(5)
                    if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                        match = re.search(r'date=(\d+)', params_of_date)
                        date_match = match.group(1)
                        date_handler = DateHandler(date_match)
                        logger.info(f"{date_match}-{key1}無資料")
                        calendar_type = date_options[-1]
                        if calendar_type == 'D':
                            past = params_of_date.replace(date_match, date_handler.previous_workday())
                        elif calendar_type == 'W':
                            past = params_of_date.replace(date_match, date_handler.previous_ww())
                        elif calendar_type == 'M':
                            past = params_of_date.replace(date_match, date_handler.previous_mm())
                        elif calendar_type == 'Y':
                            past = params_of_date.replace(date_match, date_handler.previous_yy())
                        elif calendar_type == 'A':
                            past = params_of_date + str(now.year) + "0101"
                        api_url = api_url_generator(data_api, past, value1)
                        print(api_url)
                        Json_Data = get_api_Data(api_url)
                        time.sleep(5)
                        if len(Json_Data['data']) == 0 and len(Json_Data['fields']) == 0:
                            table = False
                        else:
                            table = True
                        data_dict = crawler_content(soup, url, table, route, api_url, key1)
                        logger.success(data_dict)
                        print(data_dict)
                        df_dict = pd.DataFrame(data_dict, index=[0])
                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                    else:
                        table = True
                        data_dict = crawler_content(soup, url, table, route, api_url, key1)
                        logger.success(data_dict)
                        print(data_dict)
                        df_dict = pd.DataFrame(data_dict, index=[0])
                        data_df = pd.concat([data_df, df_dict], ignore_index=True)

def database():
    global data_df
    queue = deque()
    
    get_twse_link()  # 先取得證交所網站地圖首頁的所有網址
    
    link_file = pd.read_excel("../output/link/output_link.xlsx")
    for link, route in zip(link_file["LINK"], link_file["MAP_ROUTE"]):
        queue.append(link)
    # 測試用，將上面讀取excel和取得所有網址註解掉，使用test.txt來測試單個網頁
    # with open('test.txt', 'a+') as file: 
    #     file.seek(0) 
    #     for i in file:
    #         queue.append(i)
    num = 0
    with tqdm(total=len(queue)) as pbar:  # 初始化 tqdm 並設置總數
        while queue:
            time.sleep(2)
            url = queue.popleft()
            url = url.replace('\n', '')
            try:
                num = num + 1
                if num > 10 :
                    num = 0
                    random_number = random.randint(1,5)
                    time.sleep(random_number)

                web_process(url)
                
            except Exception as e : 
                with open('../log_txt/links_special.txt', 'a+') as file:
                    logger.debug("error link is written in links_special.txt")
                    file.write(url+'\n')

                logger.error(f"Error Message {e}")
            
            pbar.update(1)  # 更新進度條

        # today = date.today()
        # root = f'output_{today}.xlsx'
        # api_version_root = f'output_api_{today}.xlsx'
        # data_df.to_excel(api_version_root, index=False, header=True, sheet_name='Sheet1')
        # final_df = data_df.drop(columns=['API_URL'])

        # if not os.path.exists(root):
        #     final_df.to_excel(root, index=False, header=True, sheet_name='Sheet1')
        # else:
        #     with pd.ExcelWriter(root, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        #         final_df.to_excel(writer, index=False, header=True, sheet_name='Sheet1')
    
    pd.set_option('display.unicode.ambiguous_as_wide', True)
    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.width', 100) 
    print(data_df)


def check_file():
    logger.info("Check links_special.txt")
    global data_df

    max_attempts = 5  # 限制最多迴圈次數
    attempt = 0  # 計算迴圈次數

    while attempt < max_attempts:
        queue = deque()

        # 重新讀取 links_special.txt，檢查是否還有網址需要處理
        with open('../log_txt/links_special.txt', 'a+') as file: 
            file.seek(0)
            for i in file:
                queue.append(i)

        if not queue:  # 如果queue為空，說明所有網址都處理完，結束程序
            logger.info("No more URLs to process. Exiting.")
            break

        num = 0
        with tqdm(total=len(queue)) as pbar:  # 初始化 tqdm 並設置總數
            while queue:
                time.sleep(2)
                url = queue.popleft()
                url = url.replace('\n', '')
                try:
                    num = num + 1
                    if num > 10 :
                        num = 0
                        random_number = random.randint(1,5)
                        time.sleep(random_number)

                    web_process(url)

                    # 如果成功，將此網址從 links_special.txt 移除
                    with open('../log_txt/links_special.txt', 'r') as file:
                        lines = file.readlines()

                    # 寫回文件，過濾掉成功處理的網址
                    with open('../log_txt/links_special.txt', 'w') as file:
                        for line in lines:
                            if line.strip() != url:
                                file.write(line)
                    
                except Exception as e : 
                    logger.error(f"Error Message {e}")
                
                pbar.update(1)  # 更新進度條

        attempt += 1  # 增加迴圈次數

    # 如果到達最大迴圈次數，檢查是否還有網址未處理，將其寫入 error_log_main.txt
    if attempt == max_attempts:
        with open('../log_txt/links_special.txt', 'r') as file:
            remaining_urls = [line.strip() for line in file if line.strip()]
        
        if remaining_urls:  # 如果還有剩餘網址
            logger.warning("Reached maximum attempts, writing remaining URLs to error_log_main.txt.")
            with open('../log_txt/error_log_main.txt', 'a') as error_file:
                for url in remaining_urls:
                    error_file.write(url + '\n')
                    logger.debug(f"URL {url} written to error_log_main.txt.")

    pd.set_option('display.unicode.ambiguous_as_wide', True)
    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.width', 180) 
    print(data_df)

if __name__ == "__main__":
    with open('../log_txt/links_special.txt', 'r+') as file1:
        file1.truncate(0)
    with open('../log_txt/error_log_main.txt', 'r+') as file2:
        file2.truncate(0)

    start_time = time.time()
    
    database()
    check_file()

    today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    root = f'../output/table/output_{today}.xlsx'
    api_version_root = f'../output/api/output_api_{today}.xlsx'
    clean_df = data_df.drop_duplicates(subset=['MAP_ROUTE'])
    clean_df.to_excel(api_version_root, index=False, header=True, sheet_name='Sheet1')
    final_df = clean_df.drop(columns=['API_URL'])

    if not os.path.exists(root):
        final_df.to_excel(root, index=False, header=True, sheet_name='Sheet1')
    else:
        with pd.ExcelWriter(root, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            final_df.to_excel(writer, index=False, header=True, sheet_name='Sheet1')

    end_time = time.time()
    execution_time = end_time - start_time
    hours, rem = divmod(execution_time, 3600)
    minutes, seconds = divmod(rem, 60)

    print("execute time : {:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))