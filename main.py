import json
import os
import requests
import ephem
from datetime import datetime, date
from zhdate import ZhDate

# 读取json配置
def load_config():
    with open("config.json", "r", encoding="utf‑8") as f:
        cfg = json.load(f)
    # GitHub Actions环境变量优先覆盖密钥
    if "GAODE_KEY" in os.environ:
        cfg["gaode_key"] = os.environ["GAODE_KEY"]
    if "APP_ID" in os.environ:
        cfg["app_id"] = os.environ["APP_ID"]
    if "APP_SECRET" in os.environ:
        cfg["app_secret"] = os.environ["APP_SECRET"]
    return cfg

config = load_config()

def get_access_token():
    url = (f"https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={config['app_id']}&secret={config['app_secret']}")
    resp = requests.get(url, timeout=12).json()
    return resp["access_token"]

def calc_sunrise_sunset():
    """河东区经纬度计算北京时间日出日落"""
    lon = str(config["longitude"])
    lat = str(config["latitude"])
    observer = ephem.Observer()
    observer.lon = lon
    observer.lat = lat
    observer.date = datetime.utcnow()
    sun = ephem.Sun()
    rise_utc = observer.next_rising(sun).datetime()
    set_utc = observer.next_setting(sun).datetime()
    sunrise = (rise_utc + ephem.hour * 8).strftime("%H:%M")
    sunset = (set_utc + ephem.hour * 8).strftime("%H:%M")
    return sunrise, sunset

def get_gaode_weather():
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": config["gaode_key"],
        "city": config["adcode"],
        "extensions": "all"
    }
    res = requests.get(url, params=params, timeout=12).json()
    if res.get("status") != "1":
        raise Exception("高德天气接口请求失败")
    live = res["lives"][0]
    today_cast = res["forecasts"][0]["casts"][0]
    sunrise, sunset = calc_sunrise_sunset()
    data = {
        "region": config["region_name"],
        "weather": live["weather"],
        "now_temp": live["temperature"],
        "wind_dir": live["winddirection"],
        "temp_low": today_cast["nighttemp"],
        "temp_high": today_cast["daytemp"],
        "sunrise": sunrise,
        "sunset": sunset
    }
    return data

def get_love_day_count():
    start = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    now = date.today()
    return (now - start).days + 1

def check_lunar_birthday(birth_str, name):
    today = date.today()
    if birth_str.startswith("r-"):
        m, d = map(int, birth_str.replace("r-", "").split("-"))
        lunar_now = ZhDate.from_datetime(datetime.now())
        if lunar_now.month == m and lunar_now.day == d:
            return f"🎉今天是{name}的农历生日！"
    return ""

def get_sentence():
    if config["note_ch"] != "" and config["note_en"] != "":
        return config["note_ch"], config["note_en"]
    try:
        r = requests.get("https://api.shadiao.pro/chp", timeout=8).json()
        return r["data"]["text"], "Have a nice‑day."
    except Exception:
        return "今天也要保持好心情", "Wish you happy every day"

def send_one_user(openid, weather_info, access_token):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    ch_text, en_text = get_sentence()
    b1_tip = check_lunar_birthday(config["birthday1"]["birthday"], config["birthday1"]["name"])
    b2_tip = check_lunar_birthday(config["birthday2"]["birthday"], config["birthday2"]["name"])
    body = {
        "touser": openid,
        "template_id": config["template_id"],
        "data": {
            "date": {"value": datetime.now().strftime("%Y‑%m‑%d")},
            "region": {"value": weather_info["region"]},
            "weather": {"value": weather_info["weather"]},
            "temp": {"value": f'{weather_info["temp_low"]}~{weather_info["temp_high"]}℃，当前{weather_info["now_temp"]}℃'},
            "wind_dir": {"value": weather_info["wind_dir"]},
            "sunrise": {"value": weather_info["sunrise"]},
            "sunset": {"value": weather_info["sunset"]},
            "love_day": {"value": get_love_day_count()},
            "birthday1": {"value": b1_tip},
            "birthday2": {"value": b2_tip},
            "note_en": {"value": en_text},
            "note_ch": {"value": ch_text}
        }
    }
    requests.post(url, json=body)

def main():
    weather = get_gaode_weather()
    token = get_access_token()
    for openid in config["user"]:
        send_one_user(openid, weather, token)
    print("✅全部用户推送完毕")

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"❌程序异常：{err}")
