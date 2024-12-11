import os
import pandas as pd
from datetime import datetime
import pyfiglet

today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

class TWSE_Table_Compare:
    def __init__(self, df1, df2):
        self.df1 = df1
        self.df2 = df2
        self.merged = None

    # 定義變更標誌的函數
    def compare_changes(self, row):
        # 如果是 MAP_ROUTE 不一樣的話，除了 merge 函數設定在 on 的欄位，其他欄位都會有一個是 nan，所以可以使用 LINK_old 或 LINK_new 是不是 nan 來判斷
        # 因為其他欄位如果不一樣的話都有對應的修改編號
        if pd.isna(row['LINK_old']):  # 原本不存在，新增的
            return 'I'
        elif pd.isna(row['LINK_new']):  # 消失的
            return 'D'
        edits = []
        if row['TABLE_FG_old'] != row['TABLE_FG_new']:
            edits.append('T')
        if row['ATTACHMENT_FG_old'] != row['ATTACHMENT_FG_new']:
            edits.append('A')
        if row['FORM_FG_old'] != row['FORM_FG_new']:
            edits.append('F')
        if row['CSV_AND_HTML_BUTTON_FG_old'] != row['CSV_AND_HTML_BUTTON_FG_new']:
            edits.append('C')
        return ''.join(edits) if edits else None

    # 根據 EDITFG 欄位決定保留的欄位
    def keep_columns_based_on_editfg(self, row):
        if row['EDITFG'] == 'D':  # 如果 EDITFG 為 'D'，保留 old 欄位，移除 new 欄位
            columns_to_keep = [col for col in row.index if '_old' in col or col in ['WEBSITE_ID', 'MAP_ROUTE', 'EDITFG']]
        else:  # 如果是 I 或其他狀況，保留 new 欄位，移除 old 欄位
            columns_to_keep = [col for col in row.index if '_new' in col or col in ['WEBSITE_ID', 'MAP_ROUTE', 'EDITFG']]
        
        # 選擇要保留的欄位
        filtered_row = row[columns_to_keep]

        # 將欄位名稱中的 '_old' 或 '_new' 移除
        filtered_row.index = filtered_row.index.str.replace('_old', '').str.replace('_new', '')

        return filtered_row

    # 執行比較和欄位保留操作
    def compare(self):
        print(pyfiglet.figlet_format("table"))

        # 使用 outer merge 找出差異
        self.merged = pd.merge(self.df1, self.df2, on=['WEBSITE_ID', 'MAP_ROUTE'], how='outer', suffixes=('_old', '_new'))

        # 應用變更標誌函數，創建 EDITFG 欄位
        self.merged['EDITFG'] = self.merged.apply(self.compare_changes, axis=1)

        # 移除 EDITFG 為 None 的資料列
        self.merged = self.merged.dropna(subset=['EDITFG'])

        # 應用條件保留欄位
        self.merged = self.merged.apply(self.keep_columns_based_on_editfg, axis=1)

        # 重置 index
        self.merged = self.merged.reset_index(drop=True)
        
        # 新增 BEG_DATE 欄位，填入今天的日期
        self.merged['BEG_DATE'] = today

        return self.merged
    

class TWSE_Columns_Compare:
    def __init__(self, df1, df2):
        self.df1 = df1
        self.df2 = df2
        self.merged = None

    # 定義變更標誌的函數
    def compare_changes(self, row):
        if row['_merge'] == 'right_only':  # 原本不存在，新增的
            return 'I'
        elif row['_merge'] == 'left_only':  # 消失的
            return 'D'

    # 根據 EDITFG 欄位決定保留的欄位
    def keep_columns_based_on_editfg(self, row):
        if row['EDITFG'] == 'D':  # 如果 EDITFG 為 'D'，保留 old 欄位，移除 new 欄位
            columns_to_keep = [col for col in row.index if '_old' in col or col in ['WEBSITE_ID', 'MAP_ROUTE', 'NAME', 'OD', 'COLUMN_NAME', 'EDITFG']]
        else:  # 如果是 I 或其他狀況，保留 new 欄位，移除 old 欄位
            columns_to_keep = [col for col in row.index if '_new' in col or col in ['WEBSITE_ID', 'MAP_ROUTE', 'NAME', 'OD', 'COLUMN_NAME', 'EDITFG']]
        
        # 選擇要保留的欄位
        filtered_row = row[columns_to_keep]

        # 將欄位名稱中的 '_old' 或 '_new' 移除
        filtered_row.index = filtered_row.index.str.replace('_old', '').str.replace('_new', '')

        return filtered_row

    # 執行比較和欄位保留操作
    def compare(self):
        print(pyfiglet.figlet_format("columns"))

        # 比較 COLUMN NAME 欄位不看 TYPE==A 的，因為 A 的部分都沒有 COLUMN NAME
        self.df1 = self.df1[self.df1['TYPE'] != 'A']
        self.df2 = self.df2[self.df2['TYPE'] != 'A']

        # 使用 outer merge 找出差異
        self.merged = pd.merge(self.df1, self.df2, on=['MAP_ROUTE', 'NAME', 'OD', 'COLUMN_NAME'], how='outer', suffixes=('_old', '_new'), indicator=True)

        # 應用變更標誌函數，創建 EDITFG 欄位
        self.merged['EDITFG'] = self.merged.apply(self.compare_changes, axis=1)

        # 移除 EDITFG 為 None 的資料列
        self.merged = self.merged.dropna(subset=['EDITFG'])

        # 應用條件保留欄位
        self.merged = self.merged.apply(self.keep_columns_based_on_editfg, axis=1)
        
        # 新增 BEG_DATE 欄位，填入今天的日期
        self.merged['BEG_DATE'] = today

        # 指定你想要的欄位順序
        desired_column = ['WEBSITE_ID', 'MAP_ROUTE', 'TYPE', 'NAME', 'OD', 'COLUMN_NAME', 'EDITFG', 'BEG_DATE']
        self.merged = self.merged.reindex(columns=desired_column)

        # 依照 MAP_ROUTE 及 OD 進行升冪排序
        self.merged = self.merged.sort_values(by=['MAP_ROUTE', 'OD'], ascending=[True, True])

        # 重置 index
        self.merged = self.merged.reset_index(drop=True)

        return self.merged
    

class TWSE_Attachment_Compare:
    def __init__(self, df1, df2):
        self.df1 = df1
        self.df2 = df2
        self.merged = None

    # 定義變更標誌的函數
    def compare_changes(self, row):
        if row['_merge'] == 'right_only':  # 原本不存在，新增的
            return 'I'
        elif row['_merge'] == 'left_only':  # 消失的
            return 'D'

    # 根據 EDITFG 欄位決定保留的欄位
    def keep_columns_based_on_editfg(self, row):
        if row['EDITFG'] == 'D':  # 如果 EDITFG 為 'D'，保留 old 欄位，移除 new 欄位
            columns_to_keep = [col for col in row.index if '_old' in col or col in ['WEBSITE_ID', 'MAP_ROUTE', 'NAME', 'EDITFG']]
        else:  # 如果是 I 或其他狀況，保留 new 欄位，移除 old 欄位
            columns_to_keep = [col for col in row.index if '_new' in col or col in ['WEBSITE_ID', 'MAP_ROUTE', 'NAME', 'EDITFG']]
        
        # 選擇要保留的欄位
        filtered_row = row[columns_to_keep]

        # 將欄位名稱中的 '_old' 或 '_new' 移除
        filtered_row.index = filtered_row.index.str.replace('_old', '').str.replace('_new', '')

        return filtered_row

    # 執行比較和欄位保留操作
    def compare(self):
        print(pyfiglet.figlet_format("attachment"))

        # 比較 COLUMN NAME 欄位不看 TYPE==A 的，因為 A 的部分都沒有 COLUMN NAME
        self.df1 = self.df1[self.df1['TYPE'] != 'T']
        self.df2 = self.df2[self.df2['TYPE'] != 'T']

        # 使用 outer merge 找出差異
        self.merged = pd.merge(self.df1, self.df2, on=['MAP_ROUTE', 'NAME'], how='outer', suffixes=('_old', '_new'), indicator=True)

        # 應用變更標誌函數，創建 EDITFG 欄位
        self.merged['EDITFG'] = self.merged.apply(self.compare_changes, axis=1)

        # 移除 EDITFG 為 None 的資料列
        self.merged = self.merged.dropna(subset=['EDITFG'])

        # 應用條件保留欄位
        self.merged = self.merged.apply(self.keep_columns_based_on_editfg, axis=1)
        
        # 新增 BEG_DATE 欄位，填入今天的日期
        self.merged['BEG_DATE'] = today

        # 指定你想要的欄位順序
        desired_column = ['WEBSITE_ID', 'MAP_ROUTE', 'TYPE', 'NAME', 'OD', 'COLUMN_NAME', 'EDITFG', 'BEG_DATE']
        self.merged = self.merged.reindex(columns=desired_column)

        # 依照 MAP_ROUTE 及 OD 進行升冪排序
        self.merged = self.merged.sort_values(by=['MAP_ROUTE', 'OD'], ascending=[True, True])

        # 重置 index
        self.merged = self.merged.reset_index(drop=True)

        return self.merged

def find_latest(file_folder):
    folder_path = f'../output/{file_folder}'
    files = [f for f in os.listdir(folder_path) if f.startswith("output_")]
    if len(files) == 0:
        files = [f for f in os.listdir(folder_path) if f.startswith("columns_info_")]
    file_dates = {}
    for file in files:
        if file_folder == 'table':
            try:
                date_str = "_".join(file.split("_")[1:]).replace(".xlsx", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
                today_obj = datetime.now()
                file_dates[file] = file_date
            except:
                print("無檔案")
        else:
            try:
                date_str = "_".join(file.split("_")[2:]).replace(".xlsx", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
                today_obj = datetime.now()
                file_dates[file] = file_date
            except:
                print("無檔案")
    date_diffs = [(file, abs((today_obj - file_date).days)) for file, file_date in file_dates.items()]
    sorted_diffs = sorted(date_diffs, key=lambda x: x[1])
    print(sorted_diffs)

    file_left = sorted_diffs[1]
    file_right = sorted_diffs[0]
    print(f"{file_folder} 資料夾中：left 的檔案是 {file_left[0]}, right 的檔案是 {file_right[0]}")
    return folder_path + "/" + file_left[0], folder_path + "/" + file_right[0]

if __name__ == '__main__':
    table_file_left, table_file_right = find_latest("table")
    ca_file_left, ca_file_right = find_latest("columns_attachment")

    new_folder_path = f'../output/compare/{today}'
    os.makedirs(new_folder_path, exist_ok=True)

    # file_left = input("請輸入舊檔案路徑：")
    # file_right = input("請輸入新檔案路徑：")
    table_left = pd.read_excel(table_file_left)
    table_right = pd.read_excel(table_file_right)
    ca_left = pd.read_excel(ca_file_left)
    ca_right = pd.read_excel(ca_file_right)

    table_result = TWSE_Table_Compare(table_left, table_right).compare()
    table_output = f"../output/compare/{today}/output_table_compare_{today}.xlsx"
    table_result.to_excel(table_output, index=False)
    print(f"結果已輸出到 {table_output}")

    columns_result = TWSE_Columns_Compare(ca_left, ca_right).compare()
    columns_output = f"../output/compare/{today}/column_info_compare_{today}.xlsx"
    columns_result.to_excel(columns_output, index=False)
    print(f"結果已輸出到 {columns_output}")

    attachment_result = TWSE_Attachment_Compare(ca_left, ca_right).compare()
    attachment_output = f"../output/compare/{today}/attachment_compare_{today}.xlsx"
    attachment_result.to_excel(attachment_output, index=False)
    print(f"結果已輸出到 {attachment_output}")