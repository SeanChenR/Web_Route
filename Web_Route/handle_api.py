import re
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

ua = UserAgent()
ua = ua.random
headers = {'user-agent':ua}

def get_api(url): # 找到api的網址
    res = requests.get(url, headers=headers)
    time.sleep(3)
    soup = BeautifulSoup(res.text, 'lxml')
    data_api_raw = soup.find('form', attrs={'id':'form'}, recursive=True)
    pattern = r'data-api="([^"]+)"'
    match = re.search(pattern, str(data_api_raw))
    data_api = match.group(1)   # 取出api的那段
    return data_api

def api_url_generator(data_api, *args):
    api_url = f"https://www.twse.com.tw/rwd/zh{data_api}"
    for count, arg in enumerate(args):
        if count == 0:
            api_url += f"?{arg}"
        else:
            api_url += f"&{arg}"
    return api_url