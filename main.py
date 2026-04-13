import random
from time import localtime, sleep
import requests
from datetime import date
from zhdate import ZhDate
import sys
import os

def get_color():
    return "#" + "%06x" % random.randint(0, 0xFFFFFF)

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
            print(f"⚠️ 获取token重试 {i+1}/3: {e}")
            sleep(2)
    print("❌ 3次重试后获取access_token失败")
    sys.exit(1)

def get_weather(region):
    city_code = "101120901"
    url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    
    weather = "晴"
    real_temp = "23"   # 实时温度
    min_temp = "11"    # 最低温
    max_temp = "25"    # 最高温
    wind_dir = "南风"
    sunrise = "05:45"
    sunset = "18:32"

    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            data = res.json()
            if data.get("status") == 200:
                today_forecast = data["data"]["forecast"][0]
                # 🔥 核心：正确获取实时温度、最低温、最高温
                real_temp = data["data"]["wendu"]  # 实时温度
                weather = today_forecast.get("type", "晴")
                wind_dir = today_forecast.get("fx", "南风")
                # 处理最低温/最高温，去掉℃符号
                min_temp = today_forecast.get("low", "11").replace("低温 ", "").replace("℃", "")
                max_temp = today_forecast.get("high", "25").replace("高温 ", "").replace("℃", "")
                return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset
        except Exception as e:
            print(f"⚠️ 天气接口重试 {i+1}/3: {e}")
            sleep(2)
    print(f"⚠️ 3次重试后天气接口异常，使用默认值")
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
        return "0" if today == birthday else str((birthday - today).days)
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
                part1 = content[:16]
                part2 = content[16:32]
                part3 = content[32:48]
                part4 = content[48:64]
                return part1, part2, part3, part4
        except Exception as e:
            print(f"⚠️ 早安心语接口重试 {i+1}/3: {e}")
            sleep(2)
    return "早安，新的一天也要元气满满～", "", "", ""

def send_message(to_user, access_token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, note_ch1, note_ch2, note_ch3, note_ch4, note_en):
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    week = week_list[today.weekday()]
    date_str = f"{today} {week}"
    
    try:
        love = date(*map(int, config["love_date"].split("-")))
        love_days = str((today - love).days)
    except:
        love_days = "未知"

    # 生日文案
    b1 = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
    birthday1_text = f"{config['birthday1']['name']}生日还有{b1}天"
    b2 = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
    birthday2_text = f"{config['birthday2']['name']}生日还有{b2}天"

    # 🔥 核心：给所有字段传正确的值，包括real_temp
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": "临沂市", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "real_temp": {"value": real_temp, "color": get_color()},  # ✅ 给real_temp传值！
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": birthday1_text, "color": get_color()},
            "birthday2": {"value": birthday2_text, "color": get_color()},
            "note_ch": {"value": note_ch1, "color": get_color()},
            "note_ch2": {"value": note_ch2, "color": get_color()},
            "note_ch3": {"value": note_ch3, "color": get_color()},
            "note_ch4": {"value": note_ch4, "color": get_color()},
        }
    }

    for i in range(3):
        try:
            res = requests.post(send_url, json=data, timeout=30)
            if res.status_code == 200 and res.json()["errcode"] == 0:
                print(f"✅ 推送成功！")
                print(f"📊 实时{real_temp}℃ | 最低{min_temp}℃ | 最高{max_temp}℃")
                return
        except Exception as e:
            print(f"⚠️ 推送重试 {i+1}/3: {e}")
            sleep(2)
    print("❌ 推送失败")
    sys.exit(1)

if __name__ == "__main__":
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = eval(f.read())
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        sys.exit(1)

    token = get_access_token()
    real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset = get_weather(config["region"])
    note_ch1, note_ch2, note_ch3, note_ch4 = get_zaoan()
    note_en = "Good morning"

    openids = config["user"]
    if isinstance(openids, str):
        openids = [openids]
    for user in openids:
        if user.strip():
            send_message(user, token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, note_ch1, note_ch2, note_ch3, note_ch4, note_en)
