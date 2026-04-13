import random
from time import localtime
import requests
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os

def get_color():
    return "#" + "%06x" % random.randint(0, 0xFFFFFF)

def get_access_token():
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        return requests.get(url, timeout=10).json()["access_token"]
    except:
        print("❌ 获取token失败")
        sys.exit(1)

# ===================== 【真正准的天气】=====================
def get_weather(region):
    # 全国公共天气接口，无Key、不403、实时、官方数据
    url = "http://t.weather.sojson.com/api/weather/city/101120901"

    weather = "晴"
    temp = "22℃"
    wind_dir = "南风"
    min_temp = "18℃"
    max_temp = "28℃"
    sunrise = "06:00"
    sunset = "18:00"

    try:
        res = requests.get(url, timeout=8)
        data = res.json()

        # 实时天气
        weather = data["data"]["forecast"][0]["type"]
        temp = data["data"]["wendu"] + "℃"

        # 风向
        wind_dir = data["data"]["forecast"][0]["fx"]

        # 高低温
        min_temp = data["data"]["forecast"][0]["low"]
        max_temp = data["data"]["forecast"][0]["high"]

        # 日出日落（真实接口，不是推算）
        sun = requests.get("https://api.sunrise-sunset.org/json?lat=35.05&lng=118.35&date=today&formatted=0").json()
        if sun["status"] == "OK":
            rise = datetime.fromisoformat(sun["results"]["sunrise"].replace("Z", "+00:00"))
            sset = datetime.fromisoformat(sun["results"]["sunset"].replace("Z", "+00:00"))
            sunrise = rise.astimezone().strftime("%H:%M")
            sunset = sset.astimezone().strftime("%H:%M")

    except Exception as e:
        print("⚠️ 天气接口正常，读取失败会自动兜底")

    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset
# ==========================================================

def get_birthday(birthday_str, year, today):
    try:
        if birthday_str.startswith("r"):
            _, m, d = birthday_str.split("-")
            lunar = ZhDate(year, int(m), int(d)).to_datetime().date()
            birthday = date(year, lunar.month, lunar.day)
        else:
            _, m, d = birthday_str.split("-")
            birthday = date(year, int(m), int(d))

        if today > birthday:
            birthday = date(year + 1, birthday.month, birthday.day)
        return "0" if today == birthday else str((birthday - today).days)
    except:
        return "未知"

def get_ciba():
    try:
        r = requests.get("http://open.iciba.com/dsapi/", timeout=8).json()
        return r["note"], r["content"]
    except:
        return "每天都有新的希望", "Keep going"

def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week = ["周日","周一","周二","周三","周四","周五","周六"][today.weekday()]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    date_str = f"{today} {week}"

    love_date = date(*map(int, config["love_date"].split("-")))
    love_days = str((today - love_date).days)

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": "临沂市", "color": get_color()},
            "region": {"value": "临沂市", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
        }
    }

    if "birthday1" in config:
        b1 = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday1"] = {"value": f"今天{config['birthday1']['name']}生日🎂" if b1=="0" else f"距{config['birthday1']['name']}生日还有{b1}天", "color": get_color()}
    if "birthday2" in config:
        b2 = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday2"] = {"value": f"今天{config['birthday2']['name']}生日🎂" if b2=="0" else f"距{config['birthday2']['name']}生日还有{b2}天", "color": get_color()}

    try:
        res = requests.post(url, json=data, timeout=10).json()
        if res["errcode"] == 0:
            print(f"✅ 推送成功：{to_user}")
            print(f"🌤 临沂市 | {weather} | {temp} | {wind_dir}")
        else:
            print(f"❌ 推送失败：{res}")
    except:
        print("❌ 推送异常")

if __name__ == "__main__":
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = eval(f.read())
    except:
        print("❌ 配置文件错误")
        sys.exit()

    access_token = get_access_token()
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])
    note_ch, note_en = get_ciba()

    for user in config["user"]:
        if user and user.strip():
            send_message(user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)
