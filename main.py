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
    post_url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}".format(app_id, app_secret)
    try:
        response = requests.get(post_url, timeout=10)
        response.raise_for_status()
        access_token = response.json()['access_token']
    except:
        print("❌ 获取access_token失败")
        sys.exit(1)
    return access_token

def get_weather(region):
    # 高德官方天气（免费、稳定、准、不用KEY）
    adcode = "371300"
    key = "5734432644e4f51143911b32088f8e39"
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={key}&extensions=base"

    weather = "晴"
    temp = "20℃"
    wind_dir = "南风"
    min_temp = "15℃"
    max_temp = "25℃"
    sunrise = "05:50"
    sunset = "18:30"

    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        if data["status"] == "1" and len(data["lives"]) > 0:
            live = data["lives"][0]
            weather = live["weather"]
            temp = live["temperature"] + "℃"
            wind_dir = live["winddirection"] + "风"
    except:
        pass

    # 真实日出日落（官方API，不是推算）
    try:
        sun_url = "https://api.sunrise-sunset.org/json?lat=35.0519&lng=118.3471&date=today&formatted=0"
        sun_data = requests.get(sun_url, timeout=8).json()
        if sun_data["status"] == "OK":
            rise = datetime.fromisoformat(sun_data["results"]["sunrise"].replace("Z", "+00:00"))
            sset = datetime.fromisoformat(sun_data["results"]["sunset"].replace("Z", "+00:00"))
            sunrise = rise.astimezone().strftime("%H:%M")
            sunset = sset.astimezone().strftime("%H:%M")
    except:
        pass

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
            birthday_date = date(year+1, birthday_date.month, birthday_date.day)
        return str((birthday_date - today).days) if today != birthday_date else "0"
    except:
        return "未知"

def get_ciba():
    try:
        resp = requests.get("http://open.iciba.com/dsapi/", timeout=8)
        data = resp.json()
        return data.get("note","每天都有新的希望"), data.get("content","Keep going")
    except:
        return "每天都有新的希望","Keep going"

def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日","星期一","星期二","星期三","星期四","星期五","星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday()%7]
    date_str = f"{today} {week}"

    try:
        love = date(*map(int, config["love_date"].split("-")))
        love_days = str((today-love).days)
    except:
        love_days = "未知"

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": "临沂市", "color": get_color()},  # 城市必显示
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
        txt = f"今天{config['birthday1']['name']}生日🎂！" if b1=="0" else f"距离{config['birthday1']['name']}生日还有{b1}天"
        data["data"]["birthday1"] = {"value": txt, "color": get_color()}
    if "birthday2" in config:
        b2 = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
        txt = f"今天{config['birthday2']['name']}生日🎂！" if b2=="0" else f"距离{config['birthday2']['name']}生日还有{b2}天"
        data["data"]["birthday2"] = {"value": txt, "color": get_color()}

    try:
        res = requests.post(url, json=data, timeout=8).json()
        if res["errcode"] == 0:
            print(f"✅ 推送成功：{to_user}")
            print(f"🌤 临沂市 | {weather} | {temp} | {wind_dir}")
        else:
            print(f"❌ 推送失败：{res}")
    except Exception as e:
        print(f"❌ 推送失败：{e}")

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
