from datetime import datetime, timedelta
from tradeday import get_tradeday

class DateHandler:

    def __init__(self, current_date):
        self.current_date = current_date

    def previous_yy(self):
        current_date_obj = datetime.strptime(self.current_date, '%Y%m%d')        
        one_year_ago = (current_date_obj - timedelta(days=365)).replace(day=1).strftime('%Y%m%d')                    # 往前抓一年
        return one_year_ago

    def previous_mm(self):
        current_date_obj = datetime.strptime(self.current_date, '%Y%m%d')
        one_month_ago = (current_date_obj - timedelta(days=current_date_obj.day)).replace(day=1).strftime('%Y%m%d')  # 往前抓一個月
        return one_month_ago

    def previous_ww(self):
        current_date_obj = datetime.strptime(self.current_date, '%Y%m%d')
        one_week_ago = (current_date_obj - timedelta(weeks=1)).strftime('%Y%m%d')  # 往前抓一周
        return one_week_ago
    
    def previous_dd(self):
        current_date_obj = datetime.strptime(self.current_date, '%Y%m%d')
        one_day_ago = (current_date_obj - timedelta(days=1)).strftime('%Y%m%d')
        return one_day_ago
    
    def previous_workday(self):
        previous_tradeday = self.previous_dd()
        while get_tradeday(previous_tradeday) == 0:
            previous_tradeday = DateHandler(previous_tradeday).previous_dd()
        return previous_tradeday

if __name__ == "__main__":
    date_handler = DateHandler("20240523")
    previous_month = date_handler.previous_mm()  # 抓前一個月的一號 例如：20240325→20240201
    previous_year = date_handler.previous_yy()   # 抓前一年的同個月的一號 例如：20240325→20230301
    previous_week = date_handler.previous_ww()   # 抓前一個週 例如：20240401→20240325
    previous_tradeday = date_handler.previous_workday() # 抓前一個工作日

    print(previous_month, '\n', previous_year, '\n', previous_week, '\n', previous_tradeday)