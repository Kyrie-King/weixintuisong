import random
import requests
from datetime import date
from zhdate import ZhDate
import sys

def get_color():
    return "#" + "%06x" % random.randint(0, 0xFFFFFF)

def get_access_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        res = requests.get(url, timeout=10).json()
        return res["access_token"]
    except Exception as e:
        print("❌ 获取token失败：", e)
        sys.exit(1)

def get_weather(city_code, gaode_key):
    try:
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={city_code}&key={gaode_key}&extensions=all"
        data = requests.get(url, timeout=10).json()

        if data["status"] != "1":
            raise Exception("高德接口返回失败")

        forecast = data["forecasts"][0]
        today = forecast["casts"][0]

        weather = today["dayweather"]
        temp = f"{today['daytemp']}℃"
        wind_dir = today["daywind"] + "风"
        min_temp = f"{today['nighttemp']}℃"
        max_temp = f"{today['daytemp']}℃"
        sunrise = "06:00"
        sunset = "18:00"

        return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset
    except Exception as e:
        print("❌ 天气获取失败：", e)
        return "获取失败", "获取失败", "获取失败", "获取失败", "获取失败", "获取失败", "获取失败"

def get_birthday(birthday_str, year, today):
    try:
        if birthday_str.startswith("r"):
            _, m, d = birthday_str.split("-")
            lunar = ZhDate(year, int(m), int(d))
            birthday = lunar.to_datetime().date()
        else:
            _, m, d = birthday_str.split("-")
            birthday = date(year, int(m), int(d))

        if today > birthday:
            birthday = date(year + 1, birthday.month, birthday.day)
        days = (birthday - today).days
        return str(days) if days != 0 else "0"
    except Exception as e:
        print("❌ 生日计算失败：", e)
        return "获取失败"

def get_random_love_words():
    love_words = [
        "我喜欢你，胜于昨日，略匮明朝。",
        "你是我明目张胆的偏爱，众所周知的私心。",
        "一想到能和你共度余生，我就对余生充满期待。",
        "世界那么大，遇见你不容易，我不想错过。",
        "我想把所有温柔和浪漫都给你。"
    ]
    return random.choice(love_words)

def get_random_riddle():
    riddles = [
        ("什么门永远关不上？", "球门"),
        ("什么东西越洗越脏？", "水"),
        ("什么水永远用不完？", "泪水"),
        ("什么路最窄？", "冤家路窄"),
        ("什么瓜不能吃？", "傻瓜")
    ]
    return random.choice(riddles)

def main():
    with open("config.txt", encoding="utf-8") as f:
        config = eval(f.read())

    app_id = config["app_id"]
    app_secret = config["app_secret"]
    template_id = config["template_id"]
    user = config["user"][0]
    love_date = config["love_date"]
    gaode_key = config["gaode_key"]

    access_token = get_access_token(app_id, app_secret)
    today = date.today()
    week = ["日", "一", "二", "三", "四", "五", "六"][today.weekday()]
    date_str = f"{today} 星期{week}"

    # 在一起天数
    try:
        ly, lm, ld = map(int, love_date.split("-"))
        love_days = str((today - date(ly, lm, ld)).days)
    except Exception as e:
        print("❌ 在一起天数计算失败：", e)
        love_days = "获取失败"

    # 天气（带℃单位）
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather("371300", gaode_key)

    # 生日文案
    birthday1 = ""
    if "birthday1" in config:
        days = get_birthday(config["birthday1"]["birthday"], today.year, today)
        if days == "0":
            birthday1 = f"今天是{config['birthday1']['name']}生日！"
        else:
            birthday1 = f"距离{config['birthday1']['name']}生日还有{days}天"

    birthday2 = ""
    if "birthday2" in config:
        days = get_birthday(config["birthday2"]["birthday"], today.year, today)
        if days == "0":
            birthday2 = f"今天是{config['birthday2']['name']}生日！"
        else:
            birthday2 = f"距离{config['birthday2']['name']}生日还有{days}天"

    # 情话和脑筋急转弯
    love_word = get_random_love_words()
    riddle_q, riddle_a = get_random_riddle()

    # 推送数据（和模板字段完全对应）
    data = {
        "touser": user,
        "template_id": template_id,
        "url": "https://github.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": "临沂", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "min_temp": {"value": min_temp, "color": get_color()},
            "max_temp": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": birthday1, "color": get_color()},
            "birthday2": {"value": birthday2, "color": get_color()},
            "love_word": {"value": love_word, "color": get_color()},
            "riddle_q": {"value": riddle_q, "color": get_color()},
            "riddle_a": {"value": riddle_a, "color": get_color()}
        }
    }

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        print("✅ 推送成功：", resp.json())
    except Exception as e:
        print("❌ 推送失败：", e)

if __name__ == "__main__":
    main()
