import tejapi
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

base = config['TEJ']['base']
key = config['TEJ']['key']

tejapi.ApiConfig.api_base = base
tejapi.ApiConfig.api_key = key
tejapi.ApiConfig.ignoretz = True

# 查看日期是否為工作日，如果是0是假日，其他數字都是工作日
def get_tradeday(zdate):
    zdate = zdate[0:4] + "-" + zdate[4:6] + "-" + zdate[6:8]
    tradedata = tejapi.get('TWN/TRADEDAY_TWSE',
                            zdate=zdate)
    return tradedata['tradeday_cno'].iloc[0]