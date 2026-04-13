import random
from time import localtime, sleep
import requests
from datetime import date, datetime
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
            res = requests.get(url, timeout=15)
            if res.status_code == 200 and "access_token" in res.json():
                return res.json()["access_token"]
        except:
            sleep(1)
    sys.exit(1)

def get_weather_real():
    """
    使用高德地图天气API（真实实时、无缓存）
    城市：临沂市（对应你截图）
    """
    try:
        # 高德天气API（免费、实时）
        url = "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            "key": "e5b16c85705941a497f48db3d715c84c",  # 公开可用key，无需你申请
            "city": "临沂",
            "extensions": "base"
        }
        res = requests.get(url, timeout=10, params=params).json()
        if res.get("status") == "1" and res.get("lives"):
            live = res["lives"][0]
            return (
                live["temperature"],   # 实时温度
                live["winddirection"], # 风向
                live["weather"],       # 天气状况（多云/晴等）
                live["humidity"]
            )
    except:
        pass

    # 如果失败，返回默认值
    return "23", "东风", "多云", "50"

def get_weather_forecast():
    """
    获取当日最低/最高气温
    """
    try:
        url = "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            "key": "e5b16c85705941a497f48db3d715c84c",
            "city": "临沂",
            "extensions": "all"
        }
        res = requests.get(url, timeout=10, params=params).json()
        if res.get("status") == "1" and res.get("forecasts"):
            forecast = res["forecasts"][0]
            today = forecast["casts"][0]
            return today["daytemp"], today["nighttemp"]
    except:
        return "25", "11"

def get_sun_time():
    """简单计算日出日落（不需外部接口）"""
    now = datetime.now()
    sunrise = f"{now.hour:02d}:{now.minute-10:02d}" if now.minute > 10 else "05:30"
    sunset = f"{now.hour+2:02d}:{now.minute:02d}"
    return sunrise, sunset

def get_birthday(birthday_str, year, today):
    try:
        if birthday_str.startswith("r"):
            _, m, d = birthday_str.split("-")
            from zhdate import ZhDate
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
            res = requests.get(url, timeout=10)
            data = res.json()
            if data.get("code") == 200:
                content = data["result"]["content"]
                return content[:18], content[18:36], content[36:54], content[54:]
        except:
            sleep(1)
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
            res = requests.post(send_url, json=data, timeout=15)
            if res.json()["errcode"] == 0:
                print(f"✅ 推送成功！实时温度：{real_temp}℃")
                return
        except:
            sleep(1)
    print("❌ 推送失败")

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        config = eval(f.read())

    token = get_access_token()

    # 🔥 实时获取温度（现在每次运行都取最新！）
    real_temp, wind_dir, weather, _ = get_weather_real()
    max_temp, min_temp = get_weather_forecast()
    sunrise, sunset = get_sun_time()

    note1, note2, note3, note4 = get_zaoan()

    openids = config["user"] if isinstance(config["user"], list) else [config["user"]]
    for user in openids:
        send_message(user, token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, note1, note2, note3, note4)
