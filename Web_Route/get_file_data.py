import os
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import re
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import time
from fake_useragent import UserAgent
from pathlib import Path
import pandas as pd
from columns_content import attachment_info

def get_latest_api_file():
    # 設定資料夾路徑
    folder_path = "../output/api/"
    
    # 取得資料夾內所有檔案名稱
    files = os.listdir(folder_path)

    # 篩選符合 output_api_{日期}.xlsx 格式的檔案
    xlsx_files = [f for f in files if f.startswith('output_api_') and f.endswith('.xlsx')]

    # 初始化變數儲存最新檔案
    latest_file = None
    latest_date = None

    # 逐一檢查檔案名稱中的日期
    for file in xlsx_files:
        # 提取日期部分 output_api_{日期}.xlsx -> {日期}
        try:
            date_str = file.replace("output_api_", "").replace(".xlsx", "")  # 10 表示 'output_api_' 的長度, -5 表示去掉 '.xlsx'
            file_date = datetime.strptime(date_str, '%Y-%m-%d_%H-%M-%S')  # 假設日期格式為 YYYY-MM-DD_HHMMSS
            
            # 比較並更新最新的日期和檔案
            if latest_date is None or file_date > latest_date:
                latest_date = file_date
                latest_file = file
        except ValueError:
            # 如果日期格式錯誤，則跳過該檔案
            continue

    # 顯示最新檔案
    if latest_file:
        latest = folder_path + latest_file
        print(f"最新檔案為: {latest}")
        return latest
    else:
        print("無法找到符合格式的檔案")

api_file_path = get_latest_api_file()

if api_file_path:
    pass
else:
    api_file_path = input("請輸入api檔案的絕對路徑：")

data_df = pd.DataFrame(columns=['WEBSITE_ID', 'MAP_ROUTE', 'TYPE', 'NAME', 'OD', 'COLUMN_NAME'])
data = pd.read_excel(api_file_path)
data_attachment = data[data['ATTACHMENT_FG'] == 'Y']
data_attachment.reset_index(inplace=True)
data_attachment = data_attachment.drop(columns=['index'])

ua = UserAgent()
ua = ua.random
headers = {'user-agent':ua}

chrome_options = Options() # 設定自動開瀏覽器的方法
chrome_options.add_argument("--start-maximized")  # 可選：最大化瀏覽器窗口
chrome_options.add_argument("--headless") # 無頭模式,不打開瀏覽器視窗
chrome_options.add_argument("--proxy-pac-url") # 設定proxy,但好像沒用
chrome_options.add_argument(f"--user-agent={ua}")
driver = webdriver.Chrome(options=chrome_options)

date_pattern = r'(\d{3,4}年\d{1,2}月\d{1,2}日)|(\d{3,4}/\d{1,2}/\d{1,2})'

def get_file_data(api_url, link, log):
    global data_df
    # 如果是抓取 error_log.txt，先將原本的 DataFrame 清空
    if log == 'error':
        data_df = pd.DataFrame(columns=['WEBSITE_ID', 'MAP_ROUTE', 'TYPE', 'NAME', 'OD', 'COLUMN_NAME'])
    matched_row = data_attachment[
        (data_attachment['LINK'] == link) &
        (data_attachment['API_URL'] == api_url)
    ]
    try:
        if not matched_row.empty:
            # print(f"找到匹配的行: {matched_row}")
            print(f'處理 link: {link}, api_url: {api_url}')
            route = data_attachment[data_attachment['API_URL'] == api_url]['MAP_ROUTE'].iloc[0]
            # if link == 'https://www.twse.com.tw/zh/listed/foreign/qa.html':
            #     print(f"此網址不抓: {link}")
            # else:
            if api_url == 'N':
                route = data_attachment[data_attachment['LINK'] == link]['MAP_ROUTE'].iloc[0]
                driver.get(link)
                time.sleep(3)
                res = driver.page_source
                soup = BeautifulSoup(res, 'lxml')
                # 這個網頁比較特別，不規則的表格型態
                if link == "https://www.twse.com.tw/zh/indices/indices/series.html":
                    print("不規則表格網頁")
                    series = [index.a.text for body in soup.find("tbody").find_all('tr') for index in body.find_all('td', align='left') if index.a and index.a.text != '問答集']
                    for name in series:
                        print(name)
                        data_dict = attachment_info(name, link, route)
                        df_dict = pd.DataFrame(data_dict, index=[0])
                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                else:
                    try:
                        tables = soup.find_all("table")
                        print(f"此頁有 {len(tables)} 個表格")
                        if len(tables) == 1:
                            header = [th.text for th in soup.find('table').find_all('th')]
                            content = soup.find('table').find_all('td')
                            slices = [content[i:i+len(header)] for i in range(0, len(content), len(header))]
                            print(slices)
                            for row in slices:
                                try:
                                    file_type = row[-1].find('i')['data-file-extension'].upper()
                                except:
                                    file_type = '無載點'
                                if file_type != '無載點':
                                    if '文件名稱' in header:
                                        position = header.index('文件名稱')
                                        name = row[position].text
                                        print(name)
                                        data_dict = attachment_info(name, link, route)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    elif '報表名稱' in header:
                                        position = header.index('報表名稱')
                                        name = row[position].text
                                        print(name)
                                        data_dict = attachment_info(name, link, route)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    elif '主旨' in header:
                                        position = header.index('主旨')
                                        name = row[position].text
                                        print(name)
                                        data_dict = attachment_info(name, link, route)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    else:
                                        position = 0
                                        name = row[position].text
                                        match = re.match(date_pattern, name)
                                        if match:
                                            position = 1
                                            try:
                                                name = row[position].text
                                            except:
                                                name = str(row[position])
                                            try:
                                                only_date_and_download = row[-1].find('i')['data-file-extension'].text
                                            except:
                                                only_date_and_download = str(row[-1].find('i')['data-file-extension'])
                                            if name == only_date_and_download: # 欄位只有日期跟載點 直接用日期當表格
                                                print("進入判斷式")
                                                name = row[0].text
                                                data_dict = attachment_info(name, link, route)
                                                df_dict = pd.DataFrame(data_dict, index=[0])
                                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                            else:
                                                print(name)
                                                data_dict = attachment_info(name, link, route)
                                                df_dict = pd.DataFrame(data_dict, index=[0])
                                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                        else:
                                            print(name)
                                            data_dict = attachment_info(name, link, route)
                                            df_dict = pd.DataFrame(data_dict, index=[0])
                                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                else:
                                    print(f'{link} 是 {file_type}，所以不用抓')
                        elif len(tables) == 2:
                            for table in tables:
                                header = [th.text for th in table.find_all('th')]
                                content = table.find_all('td')
                                slices = [content[i:i+len(header)] for i in range(0, len(content), len(header))]
                                for row in slices:
                                    try:
                                        file_type = row[-1].find('i')['data-file-extension'].upper()
                                    except:
                                        file_type = '無載點'
                                    if file_type != '無載點':
                                        if '文件名稱' in header:
                                            position = header.index('文件名稱')
                                            name = row[position].text
                                            print(name)
                                            data_dict = attachment_info(name, link, route)
                                            df_dict = pd.DataFrame(data_dict, index=[0])
                                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                        elif '報表名稱' in header:
                                            position = header.index('報表名稱')
                                            name = row[position].text
                                            print(name)
                                            data_dict = attachment_info(name, link, route)
                                            df_dict = pd.DataFrame(data_dict, index=[0])
                                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                        elif '主旨' in header:
                                            position = header.index('主旨')
                                            name = row[position].text
                                            print(name)
                                            data_dict = attachment_info(name, link, route)
                                            df_dict = pd.DataFrame(data_dict, index=[0])
                                            data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                        else:
                                            position = 0
                                            name = row[position].text
                                            match = re.match(date_pattern, name)
                                            if match:
                                                position = 1
                                                name = row[position].text
                                                print(name)
                                                data_dict = attachment_info(name, link, route)
                                                data_df = pd.concat([data_df, data_dict], ignore_index=True)
                                            else:
                                                print(name)
                                                data_dict = attachment_info(name, link, route)
                                                df_dict = pd.DataFrame(data_dict, index=[0])
                                                data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    else:
                                        print(f'{link} 是 {file_type}，所以不用抓')
                        else:
                            print("你是他媽的要有幾個表格")

                    except Exception as e:
                        print(e, link)
            else:
                res = requests.get(api_url, headers=headers)
                time.sleep(2)
                res.encoding = 'utf-8'
                if res.status_code == 200:
                    json_data = res.json()
                    try:
                        stat = json_data['stat'].upper()
                    except:
                        stat = json_data['status'].upper()

                    if stat == 'OK':
                        fields = json_data['fields']
                        data = json_data['data']
                        if '文件名稱' in fields:
                            position = fields.index('文件名稱')
                            for row in data:
                                if len(row[position+1]) == 0:
                                    print("此報表無下載檔案！")
                                    continue
                                else:
                                    file_path = Path(row[position+1])
                                    file_extension = file_path.suffix.replace('.', '').upper()
                                    if len(file_extension) > 0:
                                        name = row[position]
                                        print(name)
                                        data_dict = attachment_info(name, link, route)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    else:
                                        name = row[position]
                                        print(f'{link} 中 {name}{file_type}，所以不用抓')
                        elif '報表名稱' in fields:
                            position = fields.index('報表名稱')
                            for row in data:
                                if len(row[position+1]) == 0:
                                    print("此報表無下載檔案！")
                                    continue
                                else:
                                    file_path = Path(row[position+1])
                                    file_extension = file_path.suffix.replace('.', '').upper()
                                    if len(file_extension) > 0:
                                        name = row[position]
                                        print(name)
                                        data_dict = attachment_info(name, link, route)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    else:
                                        name = row[position]
                                        print(f'{link} 中 {name}{file_type}，所以不用抓')
                        elif '主旨' in fields:
                            position = fields.index('主旨')
                            for row in data:
                                if len(row[position+1]) == 0:
                                    print("此報表無下載檔案！")
                                    continue
                                else:
                                    file_path = Path(row[position+1])
                                    file_extension = file_path.suffix.replace('.', '').upper()
                                    if len(file_extension) > 0:
                                        name = row[position]
                                        print(name)
                                        data_dict = attachment_info(name, link, route)
                                        df_dict = pd.DataFrame(data_dict, index=[0])
                                        data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                    else:
                                        name = row[position]
                                        print(f'{link} 中 {name}{file_type}，所以不用抓')
                        else:
                            position = 0
                            for row in data:
                                file_path = Path(row[-1])
                                file_extension = file_path.suffix.replace('.', '').upper()
                                if len(file_extension) > 0:
                                    name = row[position]
                                    print(name)
                                    data_dict = attachment_info(name, link, route)
                                    df_dict = pd.DataFrame(data_dict, index=[0])
                                    data_df = pd.concat([data_df, df_dict], ignore_index=True)
                                else:
                                    name = row[position]
                                    print(f'{link} 中 {name}{file_type}，所以不用抓')
        else:
            print(f"未找到匹配的行，跳過處理: link={link}, api_url={api_url}")
    except requests.exceptions.RequestException as e:
        print(f"Error with URL: {api_url} - {e}")
        # 記錄下來有問題的 URL 和錯誤信息
        with open("../log_txt/error_log.txt", "a") as f:
            f.write(f"{api_url}, {link}: {e}\n")
        return pd.DataFrame()

    if data_df.empty:
        return pd.DataFrame()
    else:
        return data_df