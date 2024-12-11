import time
import requests
from fake_useragent import UserAgent

ua = UserAgent()
ua = ua.random
headers = {'user-agent':ua}

def get_api_info(tables, groups):      # 每個網頁的表格數量不一定，所以用這個函數滾動式增加或減少表格數量
    if len(groups) == 0:   # 不是巢狀表格
        result = {}
        table_count = len(tables)
        result['table_count'] = table_count
        
        for count, table in enumerate(tables):
            fields = table['fields']
            table_name = table['title']
            columns = [field for field in fields]
            
            result[f'columns{count+1}'] = columns
            result[f'table_name{count+1}'] = table_name
        return result
    else:  # 有巢狀表格（目前還沒遇到）
        pass

def get_api_fields(api_url, route):
    for attempt in range(5):
        try:
            response = requests.get(api_url, headers=headers)
            time.sleep(3)
            if response.status_code == 200:
                data = response.json()
                print(data)
                try:
                    stat = data['stat'].upper()
                except:
                    stat = data['status'].upper()

                if stat == 'OK':
                    print(attempt)
                    try:
                        groups = data['groups']
                        print("巢狀表格！")
                    except:
                        groups = []
                        print("一般表格！")

                    try:
                        fields = data['fields']
                        try:  # 有些表格沒有標題名稱，就取 map_route 最後面的部分作為標題
                            table_name = data['title']
                        except:
                            table_name = route.split(">>")[-1]
                        if len(groups) == 0:    # 沒有巢狀表格且一個表格
                            columns = [field for field in fields]
                            return {'table_count':1, 'columns1':columns, 'table_name1':table_name}
                        else:    # 巢狀表格
                            columns = []
                            start = 0
                            for group in groups:
                                try:
                                    start = int(group['start'])
                                    span = int(group['span'])
                                    end = start + span
                                    group_name = group['title']
                                    group_fields = fields[start:end]
                                    for field in group_fields:
                                        columns.append(f"{group_name}_{field}")
                                except KeyError:    # 有些網站很拐沒有給start，所以需要這樣
                                    span = int(group['span'])
                                    end = start + span
                                    group_name = group['title']
                                    group_fields = fields[start:end]
                                    for field in group_fields:
                                        columns.append(f"{group_name}_{field}")
                                    start = end

                            return {'table_count':1, 'columns1':columns, 'table_name1':table_name}
                    except:
                        tables = []
                        for table in data['tables']:  # data['tables']是一個list，底下的哪個dict有data不一定，所以先用len判斷，但不排除還有別種狀況
                            if len(table) == 0:
                                pass
                            else:
                                tables.append(table)
                        if len(tables) == 1:   # 代表有只有一個表格
                            first_table = tables[0]
                            fields = first_table['fields']
                            table_name = first_table['title']
                            if len(groups) == 0:       # 都不是巢狀表格
                                try:
                                    columns = []
                                    groups = first_table['groups']
                                    for group in groups:
                                        start = int(group['start'])
                                        span = int(group['span'])
                                        end = start + span
                                        group_name = group['title']
                                        group_fields = fields[start:end]
                                        for field in group_fields:
                                            columns.append(f"{group_name}_{field}")
                                except:
                                    columns = [field for field in fields]
                                return {'table_count':1, 'columns1':columns, 'table_name1':table_name}
                            else:
                                columns = []
                                start = 0
                                for group in groups:
                                    try:
                                        start = int(group['start'])
                                        span = int(group['span'])
                                        end = start + span
                                        group_name = group['title']
                                        group_fields = fields[start:end]
                                        for field in group_fields:
                                            columns.append(f"{group_name}_{field}")
                                    except KeyError:   # 有些網站很拐沒有給start，所以需要這樣
                                        span = int(group['span'])
                                        end = start + span
                                        group_name = group['title']
                                        group_fields = fields[start:end]
                                        for field in group_fields:
                                            columns.append(f"{group_name}_{field}")
                                        start = end
                                return {'table_count':1, 'columns1':columns, 'table_name1':table_name}
                        elif len(tables) == 2:   # 代表有兩個表格
                            if len(groups) == 0:       # 都不是巢狀表格
                                first_table = tables[0]
                                fields_1 = first_table['fields']
                                table_name_1 = first_table['title']
                                columns1 = [field for field in fields_1]

                                second_table = tables[1]
                                # 目前只有在輸入1101跟1213時可能會遇到這個問題，所以這個try先寫在兩個table這邊就好，如果其他網頁的表格數量有增加再加上去
                                try:     # 有些輸入股票的，可能1101有兩個表格但1213只有一個表格不一定，所以用try
                                    fields_2 = second_table['fields']
                                    table_name_2 = second_table['title']
                                    columns2 = [field for field in fields_2]
                                except:
                                    columns2 = []
                                
                                if len(columns2) == 0:   # 如果沒有columns2（即有tables但第二個表格沒資料不顯示），回傳的東西就比照一個表格的
                                    return {'table_count':1, 'columns1':columns1, 'table_name1':table_name_1}
                                else:
                                    return {'table_count':2, 'columns1':columns1, 'columns2':columns2, 'table_name1':table_name_1, 'table_name2':table_name_2}
                            else:    # 有巢狀表格（目前還沒遇到）
                                pass

                        elif len(tables) > 2:  # 代表有三個表格以上
                            return get_api_info(tables, groups)   # 巢狀表格的部分目前還沒處理到，但也沒有遇到
                else:
                    continue
            else:
                time.sleep(5)
                continue
        except Exception as e:
            print(e)
            continue


if __name__ == "__main__":
    # api_url = "https://www.twse.com.tw/rwd/zh/afterTrading/BFIAMU"
    api_url = "https://www.twse.com.tw/rwd/zh/company/applylistingTdr?date="
    print(get_api_fields(api_url))