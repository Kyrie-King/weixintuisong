import random
from time import localtime, sleep
import requests
from datetime import date
from zhdate import ZhDate
import sys
import os

def get_color():
    return "#000000"

def get_access_token():
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            if res.status_code == 200 and "access_token" in res.json():
                return res.json()["access_token"]
        except Exception as e:
            sleep(2)
    sys.exit(1)

def get_weather(region):
    city_code = "101120901"
    url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    weather = "晴"
    real_temp = "23"
    min_temp = "15"
    max_temp = "28"
    wind_dir = "南风"
    sunrise = "05:45"
    sunset = "18:32"

    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            data = res.json()
            if data.get("status") == 200:
                today_forecast = data["data"]["forecast"][0]
                real_temp = data["data"]["wendu"]
                weather = today_forecast.get("type", "晴")
                wind_dir = today_forecast.get("fx", "南风")
                min_temp = today_forecast.get("low", "15").replace("低温 ", "").replace("℃", "")
                max_temp = today_forecast.get("high", "28").replace("高温 ", "").replace("℃", "")
                sunrise = today_forecast.get("sunrise", "05:45")
                sunset = today_forecast.get("sunset", "18:32")
                return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset
        except:
            sleep(2)
    return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset

def get_birthday(birthday_str, year, today):
    try:
        if birthday_str.startswith("r"):
            _, m, d = birthday_str.split("-")
            lunar = ZhDate(year, int(m), int(d)).to_datetime().date()
            birthday = date(year, lunar.month, lunar.day)
        else:
            m, d = birthday_str.split("-")
            birthday = date(year, int(m), int(d))
        if today > birthday:
            birthday = date(year + 1, birthday.month, birthday.day)
        return str((birthday - today).days)
    except:
        return "未知"

def get_zaoan():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/zaoan/index?key={API_KEY}"
    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            data = res.json()
            if data.get("code") == 200:
                content = data["result"]["content"]
                return content[:16], content[16:32], content[32:48], content[48:64]
        except:
            sleep(2)
    return "早安", "", "", ""

def send_message(to_user, access_token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, note_ch1, note_ch2, note_ch3, note_ch4):
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    date_str = f"{today} {week_list[today.weekday()]}"
    
    try:
        love = date(*map(int, config["love_date"].split("-")))
        love_days = str((today - love).days)
    except:
        love_days = "未知"

    b1 = get_birthday(config["birthday1"]["birthday"], today.year, today)
    b2 = get_birthday(config["birthday2"]["birthday"], today.year, today)

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str},
            "city": {"value": "临沂市"},
            "weather": {"value": weather},
            "real_temp": {"value": real_temp},
            "min_temperature": {"value": min_temp},
            "max_temperature": {"value": max_temp},
            "wind_direction": {"value": wind_dir},
            "sunrise": {"value": sunrise},
            "sunset": {"value": sunset},
            "love_day": {"value": love_days},
            "birthday1": {"value": f"{config['birthday1']['name']}生日还有{b1}天"},
            "birthday2": {"value": f"{config['birthday2']['name']}生日还有{b2}天"},
            "note_ch": {"value": note_ch1},
            "note_ch2": {"value": note_ch2},
            "note_ch3": {"value": note_ch3},
            "note_ch4": {"value": note_ch4},
        }
    }

    for i in range(3):
        try:
            res = requests.post(send_url, json=data, timeout=30)
            if res.json()["errcode"] == 0:
                print("✅ 推送成功！")
                return
        except:
            sleep(2)
    print("❌ 推送失败")

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        config = eval(f.read())

    token = get_access_token()
    real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset = get_weather(config["region"])
    note1, note2, note3, note4 = get_zaoan()

    openids = config["user"] if isinstance(config["user"], list) else [config["user"]]
    for user in openids:
        send_message(user, token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, note1, note2, note3, note4)
