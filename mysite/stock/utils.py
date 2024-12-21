import chinese_calendar as calendar
from datetime import datetime, timedelta


def is_future_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date() > datetime.today().date()


def get_date_list(start_date_str='',
                  end_date_str=datetime.today().strftime('%Y-%m-%d')):

    if not start_date_str:
        return [end_date_str]

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    date_list = []
    while start_date <= end_date:
        date_list.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)

    return date_list


def is_weekend_or_holiday(date_str):

    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

    if date_obj.isoweekday() > 5:
        error_msg = f"{date_str} is a weekend! {date_obj.strftime('%a')}"
        return True, error_msg

    on_holiday, holiday_name = calendar.get_holiday_detail(date_obj)
    if on_holiday:
        holiday_name == calendar.Holiday.labour_day.value
        error_msg = f"{date_str} is a holiday! {holiday_name}"
        return True, error_msg

    return False, ''
