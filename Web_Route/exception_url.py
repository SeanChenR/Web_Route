import re
from selenium.webdriver.support.ui import Select

# 函數設計這個名字是用此網頁的title
def Stock_Selection_Criteria(soup, driver):
    pattern_group = r'class="group\s*([^"]*)"'
    pattern_name  = r'name="([^"]+)"'
    div_group = soup.find_all('div', {'class': 'group'})
    div_group_menu = [class_group for class_group in div_group if len(re.findall(pattern_group, str(class_group))[0]) == 0]
    div_menu = [j for j in div_group_menu if j.input is not None]
    if len(div_menu) == 0:
        div_menu = [j for j in div_group_menu if j.label is not None]

    label_tag = [menu_select.find_all('label')[0].text for menu_select in div_menu]
    select_tag = [re.findall(pattern_name, str(menu_select.find_all('select')[0]))[0] for menu_select in div_menu]

    item_type = Select(driver.find_element("name",select_tag[0]))
    item_options = item_type.options
    item_dict = {select_tag[0]+"="+iop.get_attribute('value'): label_tag[0]+iop.text for iop in item_options}
    search_conditions = [iop.get_attribute('value') for iop in item_options]
    query_dict = {}
    for conditions in search_conditions:
        item_type.select_by_value(conditions)
        query_type = Select(driver.find_element("name",select_tag[1]))
        query_options = query_type.options
        query_dict[select_tag[0]+"="+conditions] = {select_tag[1]+"="+qop.get_attribute('value'): label_tag[1]+qop.text for qop in query_options}
    print(item_dict, query_dict)
    return "exception_url", item_dict, query_dict