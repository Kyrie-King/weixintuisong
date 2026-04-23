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
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}".format(app_id, app_secret)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()['access_token']
    except:
        print("❌ 获取access_token失败")
        sys.exit(1)


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


def main():
    with open("config.txt", encoding="utf-8") as f:
        config = eval(f.read())

    must_have = ["app_id", "app_secret", "template_id", "user", "love_date"]
    for k in must_have:
        if k not in config:
            print(f"❌ 配置缺失：{k}")
            return

    access_token = get_access_token()
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    love_year, love_month, love_day = map(int, config["love_date"].split("-"))
    love_date = date(love_year, love_month, love_day)
    love_days = str((today - love_date).days)

    # 固定值，保证所有字段不为空
    city = "临沂"
    weather = "晴"
    temp = "22℃"
    min_temp = "18℃"
    max_temp = "28℃"
    wind_dir = "南风"
    sunrise = "06:00"
    sunset = "18:00"

    # 土味情话和脑筋急转弯
    love_words = [
        "我喜欢你，胜于昨日，略匮明朝。",
        "你是我明目张胆的偏爱，众所周知的私心。",
        "一想到能和你共度余生，我就对余生充满期待。",
        "世界那么大，遇见你不容易，我不想错过。",
        "我想把所有温柔和浪漫都给你。"
    ]
    love_word = random.choice(love_words)

    riddles = [
        ("什么门永远关不上？", "球门"),
        ("什么水永远用不完？", "泪水"),
        ("什么东西越洗越脏？", "水"),
        ("什么路最窄？", "冤家路窄"),
        ("什么瓜不能吃？", "傻瓜")
    ]
    riddle_q, riddle_a = random.choice(riddles)

    # 生日
    birthday1_text = ""
    if "birthday1" in config:
        b1_days = get_birthday(config["birthday1"]["birthday"], today.year, today)
        if b1_days == "0":
            birthday1_text = f"今天是{config['birthday1']['name']}生日！"
        else:
            birthday1_text = f"距离{config['birthday1']['name']}生日还有{b1_days}天"

    birthday2_text = ""
    if "birthday2" in config:
        b2_days = get_birthday(config["birthday2"]["birthday"], today.year, today)
        if b2_days == "0":
            birthday2_text = f"今天是{config['birthday2']['name']}生日！"
        else:
            birthday2_text = f"距离{config['birthday2']['name']}生日还有{b2_days}天"

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    headers = {"Content-Type": "application/json"}

    data = {
        "touser": config["user"][0],
        "template_id": config["template_id"],
        "url": "https://github.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": city, "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "min_temp": {"value": min_temp, "color": get_color()},
            "max_temp": {"value": max_temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": birthday1_text, "color": get_color()},
            "birthday2": {"value": birthday2_text, "color": get_color()},
            "love_word": {"value": love_word, "color": get_color()},
            "riddle_q": {"value": riddle_q, "color": get_color()},
            "riddle_a": {"value": riddle_a, "color": get_color()}
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        print(f"✅ 推送成功：{resp.json()}")
    except Exception as e:
        print(f"❌ 推送失败：{e}")


if __name__ == "__main__":
    main()
