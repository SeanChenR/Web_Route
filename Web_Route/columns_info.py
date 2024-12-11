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

import tejapi
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

base = config['TEJ']['base']
key = config['TEJ']['key']

tejapi.ApiConfig.api_base = base
tejapi.ApiConfig.api_key = key
tejapi.ApiConfig.ignoretz = True

now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
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
data_dict = {'WEBSITE_ID':'', 'MAP_ROUTE':'', 'TYPE':'', 'NAME':'', 'OD':'', 'COLUMN_NAME':''} # 設定dictionary
data_list=[]
data_df = pd.DataFrame(columns=['WEBSITE_ID', 'MAP_ROUTE', 'TYPE', 'NAME', 'OD', 'COLUMN_NAME'])

from get_api_JsonFields import get_api_fields
from columns_content import process_tables_columns_info
from handle_api import api_url_generator, get_api
from get_file_data import get_file_data, get_latest_api_file

api_file_path = get_latest_api_file()

if api_file_path:
    pass
else:
    api_file_path = input("請輸入api檔案的絕對路徑：")

data = pd.read_excel(api_file_path)
data_table = data[data['TABLE_FG'] == 'Y']

def get_columns_info(api_url, link):
    global data_df
    route = data_table[data_table['API_URL'] == api_url]['MAP_ROUTE'].iloc[0]
    # 這個網頁資料量太大，會發生載入太久的問題，所以另外拉出來
    if link == "https://www.twse.com.tw/zh/products/sbl/disclosures/t13sa710.html":
        match = re.search(r'tradeType=([^&]*)', api_url)
        if match:
            tradeType = match.group(1)
            print(tradeType)
            if tradeType == 'F':
                print("日期區間拉最大")
                print(route)
                print(api_url)
                JsonData = get_api_fields(api_url, route)
                print(JsonData)
                table_data = process_tables_columns_info(route, JsonData)
                data_df = pd.concat([data_df, table_data], ignore_index=True)
            else:
                print("拉 2024 年年初")
                print(route)
                api_url = api_url.replace('19900101', '20240101')
                print(api_url)
                JsonData = get_api_fields(api_url, route)
                print(JsonData)
                table_data = process_tables_columns_info(route, JsonData)
                data_df = pd.concat([data_df, table_data], ignore_index=True)
    else:
        if api_url == 'N':
            route = data_table[data_table['LINK'] == link]['MAP_ROUTE'].iloc[0]
            print(route)
            try:
                data_api = get_api(link)
                api_url = api_url_generator(data_api)
                print(api_url)
                JsonData = get_api_fields(api_url, route)
                table_data = process_tables_columns_info(route, JsonData)
                data_df = pd.concat([data_df, table_data], ignore_index=True)
            except:
                print("沒有API_URL，暫時不處理！")
                # with open('links_NoApi.txt', 'a+') as file:
                #     file.write(link+'\n')
        else:
            print(route)
            print(api_url)
            JsonData = get_api_fields(api_url, route)
            print(JsonData)
            table_data = process_tables_columns_info(route, JsonData)
            data_df = pd.concat([data_df, table_data], ignore_index=True)

def database():
    global data_df
    queue_link = deque()
    queue_api = deque()
    data = pd.read_excel(api_file_path)
    data_table = data[data['TABLE_FG'] == 'Y']
    for api_url, link in zip(data_table['API_URL'], data_table['LINK']):
        queue_link.append(link)
        queue_api.append(api_url)
    num = 0
    with tqdm(total=len(data_table)) as pbar:
        while queue_link:
            link = queue_link.popleft()
            api_url = queue_api.popleft()
            try:
                num += 1
                if num > 10:
                    num = 0
                    random_number = random.randint(1, 5)
                    time.sleep(random_number)
                get_columns_info(api_url, link)
                file_data = get_file_data(api_url, link, 'try')
            except Exception as e:
                print(f"Error with URL: {api_url} - {e}")
                # append 的概念，重複加上
                with open("../log_txt/web_special.txt", "a") as file:
                    file.write(f"{api_url}, {link}\n")
            pbar.update(1)
    data_df = pd.concat([data_df, file_data], ignore_index=True)


def check_file():
    file_data = pd.DataFrame()
    global data_df
    queue = deque()
    with open('../log_txt/web_special.txt', 'r') as file:
        content = file.read()
        if content:
            file.seek(0)
            for i in file:
                queue.append(i)
    with tqdm(total=len(queue)) as pbar:
        while queue:
            try:
                link = queue.popleft()
                link = link.replace('\n', '').replace(' ', '').split(',')
                api_url = link[0]
                link = link[1]
                try:
                    get_columns_info(api_url, link)
                except Exception as e:
                    print(f"Error with URL: {api_url} - {e}")
                try:
                    attachment_file = get_file_data(api_url, link, 'error')
                    file_data = pd.concat([file_data, attachment_file], ignore_index=True)
                except Exception as e:
                    print(f"Error with URL: {api_url} - {e}")
            except Exception as e:
                print(f"Error with URL: {api_url} - {e}")
            pbar.update(1)
    if not file_data.empty:
        data_df = pd.concat([data_df, file_data], ignore_index=True)
    else:
        pass

if __name__ == '__main__':
    with open('../log_txt/web_special.txt', 'r+') as file:
        file.truncate(0)
        
    start_time = time.time()
    database()
    check_file()
    file_name = f"../output/columns_attachment/columns_info_{now.strftime('%Y-%m-%d')}.xlsx"
    data_df.to_excel(file_name, index=False)
    print(data_df)
    print(f"輸出檔案：{file_name}")
    end_time = time.time()
    execution_time = end_time - start_time
    hours, rem = divmod(execution_time, 3600)
    minutes, seconds = divmod(rem, 60)

    print("execute time : {:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))