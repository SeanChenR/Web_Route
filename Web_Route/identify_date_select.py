import re
from selenium.webdriver.support.ui import Select

def flatten_dict(keys, values, parent_key='', sep=':'):
    items = {}
    for k, v in zip(keys, values):
        if isinstance(k, list) and isinstance(v, list):
            items.update(flatten_dict(k, v, parent_key, sep))
        else:
            new_key = parent_key + sep + k if parent_key else k
            items[new_key] = v
    return items

def identify_date_select(soup, driver, url):
    pattern_name  = r'name="([^"]+)"'
    pattern_id    = r'id="label([^"]+)"'
    pattern_id_check = r'id="check([^"]+)"'
    pattern_value = r'value="([^"]*)"'
    pattern_group = r'class="group\s*([^"]*)"'
    pattern_class = r'class="([^"]*)"'
    return_dict_D = {}
    return_dict_M = {}
    return_dict_Y = {}
    return_dict_W = {}
    return_dict_A = {}
    return_dict_MA = {}
    return_dict_menu = {}

    div_group_D = soup.find_all('div', {'class': 'group date-select D'})
    div_group_M = soup.find_all('div', {'class': 'group date-select M'})
    div_group_Y = soup.find_all('div', {'class': 'group date-select Y'})
    div_group_W = soup.find_all('div', {'class': 'group date-select W'})
    div_group_A = soup.find_all('div', {'class': 'group date-select A'})
    div_group_MA = soup.find_all('div', {'class': 'group date-select MA'})
    try:
        div_group = soup.find('div', {'class': 'groups'})
        div_group_menu = div_group.find_all('div', {'class': 'group'})
        div_menu = [class_group for class_group in div_group_menu if len(re.findall(pattern_group, str(class_group))[0]) == 0]
    except:
        div_group = soup.find_all('div', {'class': 'group'})
        div_group_menu = [class_group for class_group in div_group if len(re.findall(pattern_group, str(class_group))[0]) == 0]
        div_menu = [j for j in div_group_menu if j.input is not None]
        if len(div_menu) == 0:
            div_menu = [j for j in div_group_menu if j.label is not None]
    
    try:
        need_delete = [classes for classes in div_menu if re.findall(pattern_class, str(classes.label))[0] == 'title']
        if len(need_delete) != 0:
            for delete in need_delete:
                div_menu.remove(delete)
    except:
        pass

    if len(div_group_D) != 0:
        if len(div_group_D) == 1:
            day_element = div_group_D[0]
            select = day_element.find_all("select")
            input_tag = day_element.find_all('input')
            page_select_name = [re.findall(pattern_name, str(select_html))[0] for select_html in select if re.findall(pattern_name, str(select_html))]
            page_select_id = ['label'+matches[0] for input_name in input_tag if (matches := re.findall(pattern_id, str(input_name)))]
            page_select_type = [re.findall(pattern_name, str(input_html))[0] for input_html in input_tag if re.findall(pattern_name, str(input_html))]
            for type_class in page_select_type:
                element = day_element.find_all("input", {'name':type_class})
                value_data = re.findall(pattern_value, str(element))
                return_dict_D[type_class] = value_data[0]

            if len(page_select_name) == 3:
                if len(page_select_id) != 0:
                    for label in (page_select_id):
                        label_name = soup.find("label", {"for": label}).text
                        return_dict_D[label] = label_name
            elif len(page_select_name) == 6:
                select_yy = Select(driver.find_element("name","yy")).options
                select_mm = Select(driver.find_element("name", "mm")).options
                select_dd = Select(driver.find_element("name", "dd")).options
                yy_date = select_yy[-1].get_attribute("value")
                mm_date = select_mm[0].get_attribute("value")
                mm_date = "0" + mm_date if len(mm_date) == 1 else mm_date
                dd_date = select_dd[0].get_attribute("value")
                dd_date = "0" + dd_date if len(dd_date) == 1 else dd_date
                start_date = yy_date + mm_date + dd_date
                return_dict_D['startDate'] = start_date
        else:
            day_element = div_group_D[0]
            select = day_element.find_all("select")
            input_tag = day_element.find_all('input')
            page_select_name = [re.findall(pattern_name, str(select_html))[0] for select_html in select if re.findall(pattern_name, str(select_html))]
            page_select_id = ['label'+matches[0] for input_name in input_tag if (matches := re.findall(pattern_id, str(input_name)))]
            page_select_type = [re.findall(pattern_name, str(input_html))[0] for input_html in input_tag if re.findall(pattern_name, str(input_html))]
            for type_class in page_select_type:
                if len(type_class) > 8:  # 大於 8 是startDate1
                    select_yy = Select(driver.find_element("name","yy")).options
                    select_mm = Select(driver.find_element("name", "mm")).options
                    select_dd = Select(driver.find_element("name", "dd")).options
                    yy_date = select_yy[-1].get_attribute("value")
                    mm_date = select_mm[0].get_attribute("value")
                    mm_date = "0" + mm_date if len(mm_date) == 1 else mm_date
                    dd_date = select_dd[0].get_attribute("value")
                    dd_date = "0" + dd_date if len(dd_date) == 1 else dd_date
                    start_date = yy_date + mm_date + dd_date
                    return_dict_D[type_class] = start_date
                else:  # 其餘是endDate1
                    element = day_element.find_all("input", {'name':type_class})
                    value_data = re.findall(pattern_value, str(element))
                    return_dict_D[type_class] = value_data[0]

    if len(div_group_M) != 0:
        month_element = div_group_M[0]
        select = month_element.find_all("select")
        input_tag = month_element.find_all('input')
        page_select_name = [re.findall(pattern_name, str(select_html))[0] for select_html in select if re.findall(pattern_name, str(select_html))]
        page_select_id = ['label'+matches[0] for input_name in input_tag if (matches := re.findall(pattern_id, str(input_name)))]
        page_select_type = [re.findall(pattern_name, str(input_html))[0] for input_html in input_tag if re.findall(pattern_name, str(input_html))]
        for type_class in page_select_type:
            element = month_element.find_all("input", {'name':type_class})
            value_data = re.findall(pattern_value, str(element))
            return_dict_M[type_class] = value_data[0]

        if len(page_select_name) != 0 and len(page_select_id) != 0:
            for label in (page_select_id):
                label_name = soup.find("label", {"for": label}).text
                return_dict_M[label] = label_name
    
    if len(div_group_Y) != 0:
        year_element = div_group_Y[0]
        select = year_element.find_all("select")
        input_tag = year_element.find_all('input')
        page_select_name = [re.findall(pattern_name, str(select_html))[0] for select_html in select if re.findall(pattern_name, str(select_html))]
        page_select_id = ['label'+matches[0] for input_name in input_tag if (matches := re.findall(pattern_id, str(input_name)))]
        page_select_type = [re.findall(pattern_name, str(input_html))[0] for input_html in input_tag if re.findall(pattern_name, str(input_html))]
        for type_class in page_select_type:
            element = year_element.find_all("input", {'name':type_class})
            value_data = re.findall(pattern_value, str(element))
            return_dict_Y[type_class] = value_data[0]
        
        if len(page_select_name) != 0 and len(page_select_id) != 0:
            for label in (page_select_id):
                label_name = soup.find("label", {"for": label}).text
                return_dict_Y[label] = label_name

        try:
            hidden_index = str(soup.form.input)
            hidden_name = re.findall(pattern_name, hidden_index)[0]
            hidden_value = re.findall(pattern_value, hidden_index)[0]
            return_dict_Y[hidden_name] = hidden_value
        except:
            pass

    if len(div_group_W) != 0:
        week_element = div_group_W[0]
        select = week_element.find_all("select")
        input_tag = week_element.find_all('input')
        page_select_name = [re.findall(pattern_name, str(select_html))[0] for select_html in select if re.findall(pattern_name, str(select_html))]
        page_select_id = ['label'+matches[0] for input_name in input_tag if (matches := re.findall(pattern_id, str(input_name)))]
        page_select_type = [re.findall(pattern_name, str(input_html))[0] for input_html in input_tag if re.findall(pattern_name, str(input_html))]
        for type_class in page_select_type:
            element = week_element.find_all("input", {'name':type_class})
            value_data = re.findall(pattern_value, str(element))
            return_dict_W[type_class] = value_data[0]
        
        if len(page_select_name) != 0 and len(page_select_id) != 0:
            for label in (page_select_id):
                label_name = soup.find("label", {"for": label}).text
                return_dict_W[label] = label_name

    if len(div_group_A) != 0:
        year_element = div_group_A[0]
        select = year_element.find_all("select")
        input_tag = year_element.find_all('input')
        page_select_name = [re.findall(pattern_name, str(select_html))[0] for select_html in select if re.findall(pattern_name, str(select_html))]
        page_select_id = ['label'+matches[0] for input_name in input_tag if (matches := re.findall(pattern_id, str(input_name)))]
        page_select_type = [re.findall(pattern_name, str(input_html))[0] for input_html in input_tag if re.findall(pattern_name, str(input_html))]
        for type_class in page_select_type:
            element = year_element.find_all("input", {'name':type_class})
            value_data = re.findall(pattern_value, str(element))
            if len(value_data) == 0:
                return_dict_A[type_class] = ""
            else:
                return_dict_A[type_class] = value_data[0]
        
        if len(page_select_name) != 0 and len(page_select_id) != 0:
            for label in (page_select_id):
                label_name = soup.find("label", {"for": label}).text
                return_dict_A[label] = label_name

    if len(div_group_MA) != 0:
        year_element = div_group_MA[0]
        select = year_element.find_all("select")
        input_tag = year_element.find_all('input')
        page_select_name = [re.findall(pattern_name, str(select_html))[0] for select_html in select if re.findall(pattern_name, str(select_html))]
        page_select_id = ['label'+matches[0] for input_name in input_tag if (matches := re.findall(pattern_id, str(input_name)))]
        page_select_type = [re.findall(pattern_name, str(input_html))[0] for input_html in input_tag if re.findall(pattern_name, str(input_html))]
        for type_class in page_select_type:
            element = year_element.find_all("input", {'name':type_class})
            value_data = re.findall(pattern_value, str(element))
            return_dict_MA[type_class] = value_data[0]

        if len(page_select_name) != 0 and len(page_select_id) != 0:
            for label in (page_select_id):
                label_name = soup.find("label", {"for": label}).text
                return_dict_MA[label] = label_name

    if len(div_menu) != 0:
        for menu_select in div_menu:
            if menu_select.span:
                input_tag = menu_select.find_all('input', {'type': 'radio'})
                match_set = set([re.findall(pattern_name, str(input_name))[0] for input_name in input_tag])
                for match_name in match_set:
                    label_for_input = []
                    input_tag = menu_select.find_all('input', {'name': match_name})
                    for input_name in input_tag:
                        matches_id = re.findall(pattern_id, str(input_name))
                        matches_check = re.findall(pattern_id_check, str(input_name))
                        if matches_id or matches_check:
                            if len(matches_id) == 0 and len(matches_check) != 0:
                                label_for_input.append("check"+matches_check[0])
                            elif len(matches_check) == 0 and len(matches_id) != 0:
                                label_for_input.append("label"+matches_id[0])
                            else:
                                pass

                    try:
                        title = [menu_select.find('label', {'for': label_input}).text for label_input in label_for_input if len(menu_select.find_all('label', {'for': label_input})) > 1][0]
                    except:
                        title = ""

                    map_route_text = []
                    for label_input in label_for_input:
                        if menu_select.find('label', {'for': label_input}).input is None:
                            if len(menu_select.find_all('label', {'for': label_input})) > 1:
                                map_route_text.append(title + menu_select.find_all('label', {'for': label_input})[1].text)
                            else:
                                option_list = []
                                if len(menu_select.find('label', {'for': label_input}).text) > 5:
                                    option_title = (title + menu_select.find('label', {'for': label_input}).text[:5]).replace(" ", "").replace("\n", "")
                                    for all_type_option in menu_select.find_all("option"):
                                        matches = re.findall(pattern_value, str(all_type_option))[0]
                                        if matches:
                                            option_list.append(option_title + all_type_option.text)
                                    map_route_text.append(option_list)
                        else:
                            map_route_text.append((title + menu_select.find('label', {'for': label_input}).text).replace(" ", "").replace("\n", "").replace("\xa0", ""))

                for match_name in match_set:
                    input_tag = menu_select.find_all('input', {'name': match_name})
                    api_params = []
                    for input_name in input_tag:
                        matches_id = re.findall(pattern_id, str(input_name))
                        matches_check = re.findall(pattern_id_check, str(input_name))
                        matches_name = re.findall(pattern_name, str(input_name))
                        matches_value = re.findall(pattern_value, str(input_name))
                        if matches_id or matches_check:
                            if len(matches_id) == 0 and len(matches_check) != 0:
                                check_id = "check"+matches_check[0]
                                if menu_select.find('label', {'for': check_id}).input is None:
                                    try:
                                        option_list = []
                                        matches_select_name = re.findall(pattern_name, str(menu_select.find('label', {'for': check_id})))[0]
                                        for all_type_option in menu_select.find('label', {'for': check_id}).find_all('option'):
                                            matches = re.findall(pattern_value, str(all_type_option))[0]
                                            if matches:
                                                option_list.append(matches_name[0] + "=" + matches_value[0] + "&" + matches_select_name + "=" + matches)
                                    except:
                                        api_params.append(matches_name[0] + "=" + matches_value[0])

                                    if len(option_list) != 0:
                                        api_params.append(option_list)
                                else:
                                    matches_input_name = re.findall(pattern_name, str(menu_select.find('label', {'for': check_id})))[0]
                                    api_params.append(matches_name[0] + "=" + matches_value[0] + "&" + matches_input_name + "=")
                            elif len(matches_check) == 0 and len(matches_id) != 0:
                                label_id = "label"+matches_id[0]
                                if menu_select.find('label', {'for': label_id}).input is None:
                                    try:
                                        option_list = []
                                        matches_select_name = re.findall(pattern_name, str(menu_select.find('label', {'for': label_id})))[0]
                                        for all_type_option in menu_select.find('label', {'for': label_id}).find_all('option'):
                                            matches = re.findall(pattern_value, str(all_type_option))[0]
                                            if matches:
                                                option_list.append(matches_name[0] + "=" + matches_value[0] + "&" + matches_select_name + "=" + matches)
                                    except:
                                        api_params.append(matches_name[0] + "=" + matches_value[0])

                                    if len(option_list) != 0:
                                        api_params.append(option_list)
                                else:
                                    matches_input_name = re.findall(pattern_name, str(menu_select.find('label', {'for': label_id})))[0]
                                    api_params.append(matches_name[0] + "=" + matches_value[0] + "&" + matches_input_name)
                            else:
                                pass
                result = flatten_dict(map_route_text, api_params)
                for match_name in match_set:
                    return_dict_menu.update({match_name: result})
            else:
                try:
                    page_select_need = {}
                    label_tag = [menu_name.text for menu_name in  menu_select.find_all('label')]
                    input_tag = menu_select.find_all('input', {'type': 'radio'})
                    input_stockNo = menu_select.find_all('input', {'name': 'stockNo'})

                    if len(input_tag) == 0:
                        input_tag = menu_select.find_all('input')
                    match_set = set([re.findall(pattern_name, str(input_name))[0] for input_name in input_tag])

                    if (len(label_tag) % 2) == 0 or (len(label_tag) == 1) and len(label_tag) > 0:
                        label_radio_index = label_tag
                    else:
                        label_radio_index = [label_tag[0]+k for k in label_tag[1:]]

                    for match_name in match_set:
                        type_name = menu_select.find_all("input", {"name": match_name})
                        try:
                            url_need_params = [match_name+"="+re.findall(pattern_value, str(t_name))[0] for t_name in type_name]
                        except:
                            url_need_params = [match_name]

                    if len(url_need_params) == 0:
                        pass
                    elif len(url_need_params) == 1:
                        if len(menu_select.find_all('select')) != 0:
                            select_tag = menu_select.find_all('select')
                            match_select_set = set([re.findall(pattern_name, str(select_name))[0] for select_name in select_tag])
                            options_value = [re.findall(pattern_value, str(select_name)) for select_name in select_tag][0]
                            options_value = list(filter(lambda x: len(x) != 0, options_value))
                            options_text = [select_name.find('option', {'value': ops}).text for select_name in select_tag for ops in options_value if len(ops) != 0]
                            for ops_text, ops_value in zip(options_text, options_value):
                                page_select_need.update({label_radio_index[0] + ops_text: url_need_params[0] + "&" + next(iter(match_select_set)) + "=" + ops_value})
                            entry_dict = {next(iter(match_set)): page_select_need}
                            if list(entry_dict.keys())[0] in list(return_dict_menu.keys()):
                                return_dict_menu[next(iter(match_set))].update(page_select_need)
                            else:
                                return_dict_menu.update(entry_dict)
                        elif len([re.findall(pattern_name, str(i))[0] for i in menu_select.find_all('input') if i.get('type') != 'radio']) != 0:
                            stockNo = [re.findall(pattern_name, str(i))[0] for i in menu_select.find_all('input') if i.get('type') != 'radio'][0]
                            # 如果輸入格的 name 是 stockNo，那代表輸入的參數是這個
                            if url_need_params[0] == "stockNo":
                                page_select_need.update({label_radio_index[0]: url_need_params[0] + "="})
                            # https://www.twse.com.tw/zh/announcement/announcement/list.html 
                            # 如果輸入格的 name 是 keyword，則回傳 keyword，目前這個網頁是這樣，不知道有沒有別的輸入格 name 是 keyword
                            elif url_need_params[0] == "keyword":
                                page_select_need.update({label_radio_index[0]: url_need_params[0] + "="})
                            # 其餘的就是有按鈕的，"&" 前面會是按鈕的 type，後面會是按鈕的 name
                            else:
                                page_select_need.update({label_radio_index[0]: url_need_params[0] + "&" + stockNo + "="})
                            entry_dict = {next(iter(match_set)): page_select_need}
                            if list(entry_dict.keys())[0] in list(return_dict_menu.keys()):
                                return_dict_menu[next(iter(match_set))].update(page_select_need)
                            else:
                                return_dict_menu.update(entry_dict)
                        else:
                            page_select_need.update({label_radio_index[0] : url_need_params[0]})
                            return_dict_menu[next(iter(match_set))].update(page_select_need)
                    else:
                        page_select_need.update({i.replace(" ", "").replace("\n", "").replace("\xa0", ""): j for i, j in zip(label_radio_index, url_need_params)})
                        for key, value in page_select_need.items():
                            if "股票代碼" in key and len(input_stockNo) > 0 and url == "https://www.twse.com.tw/zh/announcement/bfzfzu-u.html":
                                value += "&stockNo="
                                page_select_need.update({key: value})
                        entry_dict = {next(iter(match_set)): page_select_need}
                        if list(entry_dict.keys())[0] in list(return_dict_menu.keys()):
                            return_dict_menu[next(iter(match_set))].update(page_select_need)
                        else:
                            return_dict_menu.update(entry_dict)

                except:
                    page_select_need = {}
                    label_tag = set([menu_name.text for menu_name in  menu_select.find_all('label')])
                    select_tag = menu_select.find_all('select')
                    match_set = set([re.findall(pattern_name, str(select_name))[0] for select_name in select_tag])
                    options_value = [re.findall(pattern_value, str(select_name)) for select_name in select_tag][0]
                    options_text = [select_name.find('option', {'value': ops}).text for select_name in select_tag for ops in options_value]
                    for label, Type in zip(label_tag, match_set):
                        for i,j in zip(options_text, options_value):
                            page_select_need.update({label + i: Type + "=" + j})
                    return_dict_menu.update({next(iter(match_set)): page_select_need})

    else:
        pass

    return {'return_D': return_dict_D, 
            'return_M': return_dict_M, 
            'return_Y': return_dict_Y, 
            'return_W': return_dict_W, 
            'return_A': return_dict_A,
            'return_MA': return_dict_MA,
            },\
            return_dict_menu