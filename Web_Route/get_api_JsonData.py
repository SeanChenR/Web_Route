import time
import requests
from fake_useragent import UserAgent

ua = UserAgent()
ua = ua.random
headers = {'user-agent':ua}

def get_api_Data(api_url):
    response = requests.get(api_url, headers=headers)  # 對返回的api_url做requests
    time.sleep(2)
    if response.status_code == 200:                    # 有回傳200再往下繼續
        data = response.json()
        try:  # 不同網頁的json資料stat or status不一定...(三小)
            status = str(data['stat']).strip().upper()
        except:
            status = str(data['status']).strip().upper()
        while True:
            if status == 'OK':
                if 'date=' in api_url or 'Date=' in api_url:
                    try:
                        try:  # api有些會直接有有data欄位，有些包在tables這個list底下，所以寫一個try來判斷
                            return {'data':data['data'], 'status':status, 'fields':[]}
                        except:
                            for table in data['tables']: # data['tables']是一個list，底下的哪個dict有data不一定，所以先用len判斷，但不排除還有別種狀況
                                if len(table) == 0:
                                    pass
                                else:
                                    return {'data':table['data'], 'status':status, 'fields':table['fields']}
                    except:
                        return {'data':data['data'], 'status':status, 'fields':[]}
                else:
                    try:  # api有些會直接有有data欄位，有些包在tables這個list底下，所以寫一個try來判斷
                        return {'data':data['data'], 'status':status, 'fields':[]}
                    except:
                        try:
                            for table in data['tables']: # data['tables']是一個list，底下的哪個dict有data不一定，所以先用len判斷，但不排除還有別種狀況
                                if len(table) == 0:
                                    pass
                                else:
                                    return {'data':table['data'], 'status':status, 'fields':table['fields']}
                        except:  # pdf 檔的頁面
                            return {'data':[], 'status':status, 'fields':[]}
            elif '請重新查詢!' in status:                     # 這是如果超出選取時間範圍的話，會有這段話，所以用這個判斷
                try:
                    return {'status':data['stat'], 'data':[], 'fields':[]}
                except:
                    return {'status':data['status'], 'data':[], 'fields':[]}
            elif '很抱歉' in status:
                return {'data':[], 'status':status, 'fields':[]}
            else:
                continue