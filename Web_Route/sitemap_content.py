data_dict = {'WEBSITE_ID':'', 'MAP_ROUTE':'', 'LINK':'', 'TABLE_FG':'', 'ATTACHMENT_FG':'', 'FORM_FG':'', 'CSV_AND_HTML_BUTTON_FG':'', 'API_URL':''} # 設定dictionary

def crawler_content(soup, url, table, route, api_url, selectName=""):
    if table:
        data_dict['TABLE_FG'] = 'Y'
    else:
        data_dict['TABLE_FG'] = 'N'

    data_dict['WEBSITE_ID'] = '2'
    data_dict['LINK'] = url
    temp_table_attachment_fg = soup.find_all('i', {'data-file-extension': True})  # 判斷頁面中裡有沒有載點
    if len(temp_table_attachment_fg) < 1:
        data_dict['ATTACHMENT_FG'] = 'N'
    else:
        data_dict['ATTACHMENT_FG'] = 'Y'

    temp_csv_and_html_button_fg = soup.find('div',attrs={'class':'rwd-tools'})  # 判斷頁面中有沒有【列印/HTML】與【CSV下載】按鈕
    if temp_csv_and_html_button_fg == None:
        data_dict['CSV_AND_HTML_BUTTON_FG'] = 'N'     

    else:
        data_dict['CSV_AND_HTML_BUTTON_FG'] = 'Y'

    temp_form_fg = soup.find('form',attrs={'id':'form'},recursive = True)  # 判斷有沒有Form
    if temp_form_fg:
        data_dict['FORM_FG'] = 'Y'
    else:
        data_dict['FORM_FG'] = 'N'

    if len(api_url) == 0:
        data_dict['API_URL'] = 'N'
    else:
        data_dict['API_URL'] = api_url

    separator = ">>"
    # crumbs = soup.find('div',attrs={'id':'crumbs'})  # 尋找map_route
    # crumb = crumbs.find_all('li')
    # crumb = crumb[1:len(crumb)]
    # crumb_texts = separator.join(li.text for li in crumb)

    if len(selectName) == 0:
        data_dict['MAP_ROUTE'] = route
    else:
        data_dict['MAP_ROUTE'] = route + separator + selectName

    return data_dict

# 沒有form下拉選單的，就選用這個函數，table可以一起判斷，會用no_form是因為即使沒有下拉選單，但是form這個css selector還是在，會有判斷錯誤的可能
def def_crawler_content_with_table(soup, url, no_form, route, api_url, selectName=""):

    data_dict['WEBSITE_ID'] = '2'
    data_dict['LINK'] = url
    temp_table_attachment_fg = soup.find_all('i', {'data-file-extension': True})  # 判斷頁面中裡有沒有載點
    if len(temp_table_attachment_fg) < 1:
        data_dict['ATTACHMENT_FG'] = 'N'
    else:
        data_dict['ATTACHMENT_FG'] = 'Y'

    temp_csv_and_html_button_fg = soup.find('div',attrs={'class':'rwd-tools'})  # 判斷頁面中有沒有【列印/HTML】與【CSV下載】按鈕
    if temp_csv_and_html_button_fg == None:
        data_dict['CSV_AND_HTML_BUTTON_FG'] = 'N'     

    else:
        data_dict['CSV_AND_HTML_BUTTON_FG'] = 'Y'

    if no_form:                                                               # 判斷有沒有Form
        data_dict['FORM_FG'] = 'N'
    else:
        temp_form_fg = soup.find('form',attrs={'id':'form'},recursive = True)  
        if temp_form_fg:
            data_dict['FORM_FG'] = 'Y'
        else:
            data_dict['FORM_FG'] = 'N'

    temp_table_fg = soup.find_all('table', recursive=True)   # 判斷有沒有Table
    if len(temp_table_fg) < 1:
        data_dict['TABLE_FG'] = 'N'
    else:
        data_dict['TABLE_FG'] = 'Y'

    if len(api_url) == 0:
        data_dict['API_URL'] = 'N'
    else:
        data_dict['API_URL'] = api_url

    separator = ">>"
    # crumbs = soup.find('div',attrs={'id':'crumbs'})   # 尋找map_route
    # crumb = crumbs.find_all('li')
    # crumb = crumb[1:len(crumb)]
    # crumb_texts = separator.join(li.text for li in crumb)

    if len(selectName) == 0:
        data_dict['MAP_ROUTE'] = route
    else:
        data_dict['MAP_ROUTE'] = route + separator + selectName

    return data_dict