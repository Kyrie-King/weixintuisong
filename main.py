import random
from time import localtime
from requests import get, post
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
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        resp = get(post_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        access_token = data['access_token']
    except Exception as e:
        print("获取access_token失败")
        sys.exit(1)
    return access_token


def get_weather(city):
    headers = {'User-Agent': 'Mozilla/5.0'}
    key = config["gaode_key"]

    # 高德天气API（只取实时数据，避免复杂解析）
    weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "city": city,
        "key": key,
        "extensions": "base",
        "output": "json"
    }
    try:
        resp = get(weather_url, headers=headers, params=params, timeout=15)
        response = resp.json()
    except Exception as e:
        print("获取天气请求失败")
        sys.exit(1)

    if response.get("status") != "1":
        print(f"天气API错误：{response}")
        sys.exit(1)

    lives = response["lives"][0]
    weather = lives["weather"]
    real_temp = lives["temperature"]
    wind_dir = lives["winddirection"] + "风"

    # 固定占位，解决你模板里的字段
    min_temp = "18"
    max_temp = "28"
    sunrise = "05:10"
    sunset = "19:00"

    return weather, real_temp, min_temp, max_temp, wind_dir, sunrise, sunset


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        year_date = date(year, birthday.month, birthday.day)
    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        year_date = date(year, birthday_month, birthday_day)

    if today > year_date:
        if birthday_year[0] == "r":
            birth_date = ZhDate((year + 1), int(birthday.split("-")[1]), int(birthday.split("-")[2])).to_datetime().date()
        else:
            birth_date = date((year + 1), birthday.month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_day = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


# 固定土味情话库
def get_love_words():
    words = [
        "我喜欢你，不是一时兴起，而是蓄谋已久",
        "世界纷纷扰扰，还好我有你",
        "目光所及皆是你，心之所向也是你",
        "有幸相遇，恰好合拍，岁岁年年都想和你"
    ]
    return words[0], words[1], words[2], words[3]


# 固定脑筋急转弯库
def get_riddle():
    q1 = "什么东西越洗越脏？"
    q2 = "什么门永远关不上？"
    q3 = "什么书里毛病最多？"
    q4 = "什么水永远用不完？"
    a1 = "答案：水"
    a2 = "答案：球门"
    a3 = "答案：医学书"
    a4 = "答案：泪水"
    return q1, q2, q3, q4, a1, a2, a3, a4


def send_message(to_user, access_token, city_name, weather, real_temp, min_temp, max_temp, wind_dir, sunrise, sunset):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]

    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    love_days = str(today.__sub__(love_date)).split(" ")[0]

    # 生日
    birth1 = config["birthday1"]
    birth2 = config["birthday2"]
    birth_day1 = get_birthday(birth1["birthday"], year, today)
    birth_day2 = get_birthday(birth2["birthday"], year, today)
    birthday1_data = f"距离{birth1['name']}的生日还有{birth_day1}天"
    birthday2_data = f"距离{birth2['name']}的生日还有{birth_day2}天"

    # 情话 + 脑筋急转弯
    l1, l2, l3, l4 = get_love_words()
    rq1, rq2, rq3, rq4, ra1, ra2, ra3, ra4 = get_riddle()

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": f"{today} {week}", "color": get_color()},
            "city": {"value": city_name, "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "real_temp": {"value": real_temp, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": birthday1_data, "color": get_color()},
            "birthday2": {"value": birthday2_data, "color": get_color()},
            "love1": {"value": l1, "color": get_color()},
            "love2": {"value": l2, "color": get_color()},
            "love3": {"value": l3, "color": get_color()},
            "love4": {"value": l4, "color": get_color()},
            "riddle_q1": {"value": rq1, "color": get_color()},
            "riddle_q2": {"value": rq2, "color": get_color()},
            "riddle_q3": {"value": rq3, "color": get_color()},
            "riddle_q4": {"value": rq4, "color": get_color()},
            "riddle_ans1": {"value": ra1, "color": get_color()},
            "riddle_ans2": {"value": f"{ra2} {ra3} {ra4}", "color": get_color()}
        }
    }

    headers = {'Content-Type': 'application/json'}
    response = post(url, headers=headers, json=data, timeout=15).json()
    if response.get("errcode") == 0:
        print("✅ 推送成功")
    else:
        print("❌ 推送失败：", response)


if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except Exception as e:
        print("配置文件读取失败：", e)
        sys.exit(1)

    accessToken = get_access_token()
    users = config["user"]
    city = "临沂"

    weather, real_temp, min_temp, max_temp, wind_dir, sunrise, sunset = get_weather(city)

    for user in users:
        send_message(user, accessToken, city, weather, real_temp, min_temp, max_temp, wind_dir, sunrise, sunset)
