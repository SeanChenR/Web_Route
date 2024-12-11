import re
import pandas as pd

data_dict = {'WEBSITE_ID':'', 'MAP_ROUTE':'', 'TYPE':'', 'NAME':'', 'OD':'', 'COLUMN_NAME':''} # 設定dictionary

def crawler_columns_info(route, table_name, OD, field):
    field = field.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
    pattern_date = r'(\d{1,3}/\d{1,2})'
    regex_text = re.sub(pattern_date, '', field)
    pattern_yymmdd = r'\d{3,4}年\d{2}月\d{2}日'
    column_name = re.sub(pattern_yymmdd, '', regex_text)
    data_dict['WEBSITE_ID'] = '2'
    data_dict['MAP_ROUTE'] = route
    data_dict['TYPE'] = 'T'
    data_dict['NAME'] = table_name
    data_dict['OD'] = OD
    data_dict['COLUMN_NAME'] = column_name
    return data_dict


def process_tables_columns_info(route, JsonData):
    data_df = pd.DataFrame()
    pattern = r'\d+年\d+月\d+日|\d+年\d+月|\d+年|\d+月\d+日|\d+月|查詢類股\d+|1101|1213|台泥|大飲|：類股期間：\d{2,3}/\d{2}/\d{2}到\d{2,3}/\d{2}/\d{2}|\d{3}/\d{2}/\d{2}至\d{3}/\d{2}/\d{2}|：證券期間：\d{2,3}/\d{2}/\d{2}到\d{2,3}/\d{2}/\d{2}+|：全部上市證券期間：\d{2,3}/\d{2}/\d{2}到\d{2,3}/\d{2}/\d{2}|\d{2,3}/\d{2}|\(\d{2,3}/\d{2}/\d{2}至\d{2,3}/\d{2}/\d{2}\)|資料截至'
    table_count = JsonData['table_count']
    table_names = [JsonData[f'table_name{i+1}'] for i in range(table_count)]
    columns_list = [JsonData[f'columns{i+1}'] for i in range(table_count)]

    for table_name, columns in zip(table_names, columns_list):
        current_od = 0
        for count, field in enumerate(columns):
            table_name = table_name.replace(' ', '')
            clean_table_name = re.sub(pattern, '', table_name)
            clean_table_name = re.sub(r'\s+', ' ', clean_table_name).strip().replace("～", "").replace("~", "").replace("(", "").replace(")", "")
            data_dict = crawler_columns_info(route, clean_table_name, current_od + count + 1, field)
            print(data_dict)
            df_dict = pd.DataFrame(data_dict, index=[0])
            data_df = pd.concat([data_df, df_dict], ignore_index=True)
        current_od += len(columns)
    
    return data_df

data_dict_att = {'WEBSITE_ID':'', 'MAP_ROUTE':'', 'TYPE':'', 'NAME':'', 'OD':'', 'COLUMN_NAME':''} # 設定dictionary
# 若有需要檢視 Link 在把他加進去，輸出的 excel 會有 link 比較好檢視
def attachment_info(name, link, route):
    data_dict_att['WEBSITE_ID'] = '2'
    # data_dict_att['LINK'] = link
    data_dict_att['MAP_ROUTE'] = route
    data_dict_att['TYPE'] = 'A'
    data_dict_att['NAME'] = name
    data_dict_att['OD'] = ""
    data_dict_att['COLUMN_NAME'] = ""
    return data_dict_att