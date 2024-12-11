def get_date_interval(calendar_dict):
    params_dict = {}
    for date_option, date_dictionary in calendar_dict.items():
        if len(date_dictionary) == 0:
            continue
        elif len(date_dictionary) == 1:
            date_options = date_option
            for date, event in date_dictionary.items():
                params_of_date = date+"="+event
        elif len(date_dictionary) == 3:
            date_options = "MWD"   # Month, Week, Day
            for count, (date, event) in enumerate(date_dictionary.items()):
                if count == 0:
                    params_of_date = date+"="+event+"&"
                elif count == 2:
                    params_dict[event] = params_of_date
                else:
                    params_of_date += date+"="+event
        else:
            date_options = "interval"
            for count, (date, event) in enumerate(date_dictionary.items()):
                if count == 0:
                    params_of_date = date+"="+event+"&"
                else:
                    params_of_date += date+"="+event
    try:
        if params_dict:
            return params_dict, date_options
        elif params_of_date:
            return params_of_date, date_options
    except:
        params_of_date = ""
        date_options = "none"
        return params_of_date, date_options