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

# 改用国内免费的高德天气接口，GitHub Actions 里不会被墙
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

def main():
    with open("config.txt", encoding="utf-8") as f:
        config = eval(f.read())

    must_have = ["app_id", "app_secret", "template_id", "user", "love_date", "gaode_key"]
    for key in must_have:
        if key not in config:
            print(f"❌ 配置缺失：{key}")
            sys.exit(1)

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

    # 临沂的高德城市编码：371300
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather("371300", gaode_key)

    # 生日文本
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

    # 推送数据
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
            "birthday2": {"value": birthday2, "color": get_color()}
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
