import os
import time
from urllib.parse import urljoin, urlsplit, urlunsplit
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup, Tag
import re
from collections import deque
import random
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook

chrome_options = Options() # 設定自動開瀏覽器的方法
chrome_options.add_argument("--headless") # 無頭模式,不打開瀏覽器視窗
chrome_options.add_argument("--proxy-pac-url") # 設定proxy,但好像沒用
data_dict = {'WEBSITE_ID':'', 'MAP_ROUTE':'', 'LINK':'', 'TABLE_FG':'', 'ATTACHMENT_FG':'', 'FORM_FG':'', 'CSV_AND_HTML_BUTTON_FG':''} # 設定dictionary
data_list=[]

def process_href(href, map_route, data, link):
    href_route_dict = {'LINK':'', 'MAP_ROUTE':''}
    parts = link.split('/')
    full_link = ''
    print(href, map_route)
    if href.startswith("https://www.twse.com.tw/TIB/") or href.startswith("https://www.twse.com.tw/CSR/zh/") or href.startswith("https://reportingbox.twse.com.tw") or  href.startswith("/downloads/") or re.search(r"\.(docx?|pdf|txt)$", href) or href.startswith("http") or href.startswith("https") or href=="/zh/index.html" or href == "" or href=="https://www.twse.com.tw/zh/sitemap.html" or href=="./sitemap.html" or href.startswith("/CSR/zh") or href.startswith("//reportingbox.twse.com.tw") or href.startswith("/TIB/zh/") or href.startswith("/IFRS/") or href.startswith("/market_insights/zh/") or href.startswith("./sitmap.html"):
        # 特殊網址處理
        # with open('linksa_special.txt', 'a+') as file:
        print("有補完寫入")
            # full_link = href if href.startswith("http") else "https://www.twse.com.tw" + href
            # file.write(full_link + '\n')
    elif href.startswith("/zh/") or href.startswith("../../") or (href.startswith("./") and not href.startswith("./TIB/")):
        # 只要 http 開頭都是其他網站
        if href.startswith("./"):  # 去除小數點，重抓網址
            href = href.lstrip("./")
            
        if href.startswith("/zh"):
            href = href.lstrip("/zh")

        if href.startswith("../../"):
            href = href.lstrip("../../")

        full_link = "https://www.twse.com.tw/zh/" + href  # 補全網址
    else:
        full_link = link.replace(parts[-1], href)
    
    print(full_link)
    # 確定 LINK 的網址沒有重複
    if full_link != '' and not any(d['LINK'] == full_link for d in data):
        href_route_dict['LINK'] = full_link
        href_route_dict['MAP_ROUTE'] = map_route
        data.append(href_route_dict)
    else:
        print("重複網址或無用網址" + full_link, map_route)

def find_href(data): # 找網站地圖中的網址m
    #----------------------打開網站----------------------#
    queue = deque()
    queue.append('https://www.twse.com.tw/zh/sitemap.html')
    print(f"Queue:{queue}")
    while queue:
        try:
            url = queue.popleft()
            browser = webdriver.Chrome(options=chrome_options)
            browser.get(url)
            res = browser.page_source
            browser.quit()

            soups = BeautifulSoup(res, 'lxml')
            soups_div = soups.find('div', attrs={'class':'body active'})
            first_route_tag = soups_div.find_all('ul',recursive=False)
            for first in first_route_tag:
                ff = first.find_all('li',recursive=False)
                for f in ff:
                    first_route = f.find('a').text
                    soup_div = f.find_all('li', {'class': 'grid-item'})
                    filtered_soup_div = [tag for tag in soup_div if not any(cls.startswith('hide') for cls in tag.get('class', []))]
                    # filtered_soup_div = []
                    # for tag in soup_div:
                    #     classes = tag.get('class', [])
                    #     if not any(cls.startswith('hide') for cls in classes):
                    #         a_tag = tag.find('a')
                    #         if a_tag and a_tag.text.strip() == "上市證券種類":
                    #             filtered_soup_div.append(tag)
                    for soup in filtered_soup_div:
                        second_route = ""
                        third_route = ""
                        href = ""
                        second_route_tag = soup.find_all('a', recursive=False)
                        if second_route_tag:
                            second_route_tag = second_route_tag[0]  # 只取第一個<a>標籤
                            if second_route_tag and second_route_tag.get('href'):
                                second_route = second_route_tag.text
                                map_route = first_route + '>>' + second_route
                                href = second_route_tag.get('href')
                                # 處理第二層超連結
                                if href:
                                    process_href(href, map_route, data, url)
                            else:
                                # 儲存 second_route
                                second_route = second_route_tag.text.strip()
                                contents = soup.find_all('li')
                                for content in contents:
                                    third_route_tag = content.find('a')
                                    if third_route_tag and third_route_tag.get('href'):
                                        third_route = third_route_tag.text
                                        map_route = first_route + '>>' + second_route + '>>' + third_route
                                        href = third_route_tag.get('href')
                                        if href:
                                            process_href(href, map_route, data, url)
        except Exception as e : 
            print(f"----------------Map route error-------------------{e}")
            queue.append('https://www.twse.com.tw/zh/sitemap.html')

def find_sidebar_links(data): # 找<navigation>中衍生的網址
    pattern = r"\w+\.html$" # .html結尾，避免錨點網址
    pattern_file = r"\.(docx?|pdf|txt)$" # 避免文件結尾

    #------------------------讀初始網址-------------------
    queue = deque()
    for entry in data:
        queue.append(entry['LINK'])

    visited_links = set()  # 建立一個set
    count = 0
    while queue: #queue非空值,則繼續
        url = queue.popleft().strip()  # pop下一個URL
        if url in visited_links:
            continue           # 訪過就pass

        visited_links.add(url)
        print(f"爬取連結：{url}")

        #------------------------打開網頁---------------------------------------------
        try:
            browser = webdriver.Chrome(options=chrome_options)
            time.sleep(2)
            browser.get(url)

            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'nav[role="navigation"]'))
            )

            WebDriverWait(browser, 20).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )

            time.sleep(5)

            res = browser.page_source
            browser.quit()
            soup = BeautifulSoup(res, 'lxml')
            count = count +1

        #------------------------Navigation find sidebar------------------------------
            sidebar = soup.find(['div','div','div','aside','section','nav'], attrs={'role': 'navigation'})
            sidebar_exists = sidebar.find('ul')
            sidebar_exists_f_li = sidebar_exists.find_all('li', recursive=False)
            print(sidebar_exists_f_li)

            # 匯入data資料
            for entry in data:
                if entry['LINK'] == url:
                    map_route = entry['MAP_ROUTE']
                    link = entry['LINK']
                    break
            # #------------------------Find links in sidebar--------------------------------
            if sidebar_exists_f_li != None:
                for li in sidebar_exists_f_li:
                    fourth_route = map_route + '>>' + li.find(string=True)
                    sidebar_exists_fifth_has_sub = li.find_all('li',{'class':'has-sub'})
                    sidebar_exists_fifth = li.find_all('li')
            #         # print(sidebar_exists_fifth)
                    # print(sidebar_exists_fifth_has_sub)
                    if sidebar_exists_fifth_has_sub:
                        for fifth in sidebar_exists_fifth_has_sub:
                            sidebar_exists_sixth_ul = fifth.find('ul')
                            # print(sidebar_exists_sixth_ul)
                            if fifth not in sidebar_exists_sixth_ul:
                                fifth_route = fourth_route + '>>' + fifth.find('a').text
                                href = fifth.find('a').get('href')
                                if href != None:
                                    # print(fifth_route, href)
                                    process_href(href, fifth_route, data, link)
                            if sidebar_exists_sixth_ul:
                                sidebar_exists_sixth = sidebar_exists_sixth_ul.find_all('li')
                                for sixth in sidebar_exists_sixth:
                                    href = sixth.find('a').get('href')
                                    sixth_route = fifth_route + '>>' + sixth.find('a').text
                                    # print(sixth_route, href)
                                    process_href(href, sixth_route, data, link)

    #                 # 最後一層has-sub內的li
                    # else:
                    #     for fifth in li.find_all('li'):
                    #         print(fifth.find('a').text, fifth.find('a').get('href'))
                    if sidebar_exists_fifth:
                        non_has_sub_fifths = [f for f in sidebar_exists_fifth if 'has-sub' not in f.get('class', [])]
                        for fifth in non_has_sub_fifths:
                            fifth_route = fourth_route + '>>' + fifth.find('a').text
                            href = fifth.find('a').get('href')
                            # print(fifth_route, href)
                            process_href(href, fifth_route, data, link)
                    else:
                        href = li.find('a',href=True).get('href')
                        # print(fourth_route, href)
                        process_href(href, fourth_route, data, link)

    # # ---------------------------------Find Links in Main--------------------------
            fourth_route_tag_ul = soup.find('ul',{'class':'dot'})
            fourth_route_tag_li = fourth_route_tag_ul.find_all('li')
            for li in fourth_route_tag_li:
                fourth_route = map_route + '>>' + li.text
                href = li.find('a').get('href')
                process_href(href, fourth_route, data, link)
        except :
            queue.append(url)
            continue
    print(f"訪問連結:{visited_links}")

def get_twse_link():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    data = []
    find_href(data)
    find_sidebar_links(data)
    df = pd.DataFrame(data)
    df.to_excel('../output/link/output_link.xlsx', index=False)
    df.to_excel(f'../output/link/output_link_{now}.xlsx', index=False)