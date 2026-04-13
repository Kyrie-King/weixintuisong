import random
from time import localtime
import requests
from datetime import datetime, date, timedelta
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

def get_weather(region):
    city_code = "101120901"
    url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    
    weather = "晴"
    temp = "20℃"
    wind_dir = "南风"
    min_temp = "15℃"
    max_temp = "28℃"
    sunrise = "05:45"
    sunset = "18:32"

    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        if data.get("status") == 200:
            today_forecast = data["data"]["forecast"][0]
            weather = today_forecast.get("type", "晴")
            temp = data["data"].get("wendu", "20") + "℃"
            wind_dir = today_forecast.get("fx", "南风")
            
            low = today_forecast.get("low", "15℃").replace("低温 ", "")
            high = today_forecast.get("high", "28℃").replace("高温 ", "")
            min_temp = low if "℃" in low else low + "℃"
            max_temp = high if "℃" in high else high + "℃"

        from datetime import datetime, timedelta
        sun_resp = requests.get("https://api.sunrise-sunset.org/json?lat=35.0519&lng=118.3471&date=today&formatted=0", timeout=5)
        sun_data = sun_resp.json()
        if sun_data.get("status") == "OK":
            rise_utc = datetime.fromisoformat(sun_data["results"]["sunrise"].replace("Z", ""))
            set_utc = datetime.fromisoformat(sun_data["results"]["sunset"].replace("Z", ""))
            rise_cn = rise_utc + timedelta(hours=8)
            set_cn = set_utc + timedelta(hours=8)
            sunrise = rise_cn.strftime("%H:%M")
            sunset = set_cn.strftime("%H:%M")
    except:
        pass
    
    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset

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

# 早安心语（完整显示，不截断、无...）
def get_zaoan():
    API_KEY = "你的TianAPI Key"  # 记得换成你自己的
    url = f"https://apis.tianapi.com/zaoan/index?key={API_KEY}"
    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        if data.get("code") == 200:
            return data["result"]["content"]  # 完整返回，不裁剪
    except:
        pass
    return "早安，新的一天也要元气满满～"

def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch):
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    week = week_list[today.weekday()]
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
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()},
        }
    }

    if "birthday1" in config:
        b1 = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday1"] = {"value": f"距离{config['birthday1']['name']}生日还有{b1}天", "color": get_color()}
    if "birthday2" in config:
        b2 = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday2"] = {"value": f"距离{config['birthday2']['name']}生日还有{b2}天", "color": get_color()}

    try:
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
        res = requests.post(url, json=data, timeout=10).json()
        if res["errcode"] == 0:
            print(f"✅ 推送成功！")
        else:
            print(f"❌ 推送失败：{res}")
    except Exception as e:
        print(f"❌ 推送异常：{e}")

if __name__ == "__main__":
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = eval(f.read())
    except:
        print("❌ 配置文件错误")
        sys.exit()

    access_token = get_access_token()
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])
    note_ch = get_zaoan()

    for user in config["user"]:
        if user and user.strip():
            send_message(user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch)
