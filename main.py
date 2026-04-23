import random
from time import localtime
import requests
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os


def get_color():
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}".format(app_id, app_secret))
    try:
        response = requests.get(post_url, timeout=10)
        response.raise_for_status()
        access_token = response.json()['access_token']
    except:
        print("获取access_token失败")
        sys.exit(1)
    return access_token


def get_weather():
    weather = "晴"
    temp = "22℃"
    wind_dir = "南风"
    min_temp = "18℃"
    max_temp = "28℃"
    sunrise = "06:00"
    sunset = "18:00"
    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset


def get_birthday(birthday_str, year, today):
    try:
        if birthday_str.startswith("r"):
            _, month, day = birthday_str.split("-")
            lunar_date = ZhDate(year, int(month), int(day))
            solar_date = lunar_date.to_datetime().date()
            birthday_date = date(year, solar_date.month, solar_date.day)
        else:
            _, month, day = birthday_str.split("-")
            birthday_date = date(year, int(month), int(day))

        if today > birthday_date:
            if birthday_str.startswith("r"):
                next_lunar = ZhDate(year + 1, int(month), int(day))
                next_solar = next_lunar.to_datetime().date()
                birthday_date = date(year + 1, next_solar.month, next_solar.day)
            else:
                birthday_date = date(year + 1, int(month), int(day))
            days = str((birthday_date - today).days)
        elif today == birthday_date:
            days = "0"
        else:
            days = str((birthday_date - today).days)
        return days
    except:
        return "未知"


def get_ciba():
    return "每天都要开心呀", "Every day be happy"


def love_words():
    words = [
        "遇见你，是我最大的幸运。",
        "我的温柔和偏爱，全部都给你。",
        "想和你今年，明年，年年。",
        "你是我疲惫生活里的温柔梦想。",
        "全世界最最最可爱的人，就是你。"
    ]
    return random.choice(words)


def riddle():
    riddles = [
        ("什么门永远关不上？", "球门"),
        ("什么水永远用不完？", "泪水"),
        ("什么东西越洗越脏？", "水"),
        ("什么路最窄？", "冤家路窄"),
        ("什么瓜不能吃？", "傻瓜")
    ]
    return random.choice(riddles)


def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    love_year, love_month, love_day = map(int, config["love_date"].split("-"))
    love_date = date(love_year, love_month, love_day)
    love_days = str((today - love_date).days)

    love_word = love_words()
    riddle_q, riddle_a = riddle()

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": {
            "date": {"value": date_str},
            "city": {"value": "临沂"},
            "weather": {"value": weather},
            "temp": {"value": temp},
            "wind_dir": {"value": wind_dir},
            "min_temperature": {"value": min_temp},
            "max_temperature": {"value": max_temp},
            "sunrise": {"value": sunrise},
            "sunset": {"value": sunset},
            "love_day": {"value": love_days},
            "love_word": {"value": love_word},
            "riddle_q": {"value": riddle_q},
            "riddle_a": {"value": riddle_a},
            "note_ch": {"value": note_ch},
            "note_en": {"value": note_en}
        }
    }

    if "birthday1" in config:
        b1_days = get_birthday(config["birthday1"]["birthday"], today.year, today)
        if b1_days == "0":
            data["data"]["birthday1"] = {"value": f"🎉 今天是{config['birthday1']['name']}生日！"}
        else:
            data["data"]["birthday1"] = {"value": f"距离{config['birthday1']['name']}生日还有{b1_days}天"}

    if "birthday2" in config:
        b2_days = get_birthday(config["birthday2"]["birthday"], today.year, today)
        if b2_days == "0":
            data["data"]["birthday2"] = {"value": f"🎉 今天是{config['birthday2']['name']}生日！"}
        else:
            data["data"]["birthday2"] = {"value": f"距离{config['birthday2']['name']}生日还有{b2_days}天"}

    try:
        requests.post(url, json=data)
        print(f"推送成功：{to_user}")
    except:
        print("推送失败")


if __name__ == "__main__":
    with open("config.txt", encoding="utf-8") as f:
        config = eval(f.read())

    access_token = get_access_token()
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather()
    note_ch, note_en = get_ciba()

    for user in config["user"]:
        send_message(user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)
