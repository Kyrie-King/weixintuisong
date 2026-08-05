import json
import os
import requests
import ephem
from datetime import datetime, date
from zhdate import ZhDate

# ----------------------配置----------------------
GAODE_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

def get_weather():
    """获取临沂天气，兼容无lives实时天气兜底"""
    params = {
        "key": os.getenv("GAODE_KEY"),
        "city": "371300",
        "extensions": "all"
    }
    resp = requests.get(GAODE_WEATHER_URL, params=params, timeout=15)
    res = resp.json()
    print("高德返回数据：", res)

    if "lives" in res and len(res["lives"]) > 0:
        live_data = res["lives"][0]
        weather_text = (
            f"📍{live_data['city']}\n"
            f"☁天气：{live_data['weather']}\n"
            f"🌡温度：{live_data['temperature']}℃\n"
            f"💨风向：{live_data['winddirection']} 风级{live_data['windpower']}\n"
            f"💧湿度：{live_data['humidity']}%"
        )
    else:
        today = res["forecasts"][0]["casts"][0]
        weather_text = (
            f"📍临沂市(今日预报)\n"
            f"☁天气：{today['dayweather']}\n"
            f"🌡白天温度：{today['daytemp']}℃\n"
            f"🌙夜间温度：{today['nighttemp']}℃\n"
            f"💨风向：{today['daywind']} 风级{today['daypower']}"
        )
    return weather_text


def send_wechat_message(content):
    """微信推送消息"""
    token = os.getenv("WECHAT_TOKEN")
    user_id = os.getenv("WECHAT_UID")
    url = f"https://sctapi.ftqq.com/{token}.send"
    data = {
        "title": "每日天气提醒",
        "desp": content,
        "openid": user_id
    }
    requests.post(url, data=data, timeout=15)


if __name__ == "__main__":
    try:
        weather_msg = get_weather()
        send_wechat_message(weather_msg)
        print("✅天气推送成功")
    except Exception as e:
        print(f"❌程序异常：{e}")

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
