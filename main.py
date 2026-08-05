import json
import os
import requests
import ephem
from datetime import datetime, date
from zhdate import ZhDate

# ===================== 配置区，请自行修改参数 =====================
config = {
    "love_date": "2024-01-01",        # 相恋起始日期
    "template_id": "你的微信模板ID",
    "user": ["接收人openid"],
    "birthday1": {
        "name": "娇娇",
        "birthday": "r-12-5"            # r‑代表农历 月‑日
    },
    "birthday2": {
        "name": "自己",
        "birthday": "r-10-24"
    },
    "note_ch": "",
    "note_en": ""
}

GAODE_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

def get_weather():
    """获取临沂天气，返回结构化字典，适配微信模板读取"""
    params = {
        "key": os.getenv("GAODE_KEY"),
        "city": "371300",
        "extensions": "all"
    }
    resp = requests.get(GAODE_WEATHER_URL, params=params, timeout=15)
    res = resp.json()
    print("高德返回数据：", res)

    weather_dict = {
        "region": "临沂市",
        "weather": "未知",
        "temp_low": "",
        "temp_high": "",
        "now_temp": "",
        "wind_dir": ""
    }

    if "lives" in res and len(res["lives"]) > 0:
        live_data = res["lives"][0]
        weather_dict["weather"] = live_data['weather']
        weather_dict["now_temp"] = live_data['temperature']
        weather_dict["wind_dir"] = f"{live_data['winddirection']} 风级{live_data['windpower']}"

    today_forecast = res["forecasts"][0]["casts"][0]
    weather_dict["weather"] = today_forecast['dayweather']
    weather_dict["temp_low"] = today_forecast['nighttemp']
    weather_dict["temp_high"] = today_forecast['daytemp']
    weather_dict["wind_dir"] = f"{today_forecast['daywind']} 风级{today_forecast['daypower']}"

    # ephem库计算临沂日出日落
    linyi = ephem.Observer()
    linyi.lat = '35.06'
    linyi.lon = '118.33'
    today_ephem = datetime.now().date()
    sunrise = linyi.next_rising(ephem.Sun(today_ephem)).datetime().strftime("%H:%M")
    sunset = linyi.next_setting(ephem.Sun(today_ephem)).datetime().strftime("%H:%M")
    weather_dict["sunrise"] = sunrise
    weather_dict["sunset"] = sunset

    return weather_dict


def send_wechat_message(content):
    """server酱简易推送（你原先顶部入口）"""
    token = os.getenv("WECHAT_TOKEN")
    user_id = os.getenv("WECHAT_UID")
    url = f"https://sctapi.ftqq.com/{token}.send"
    data = {
        "title": "每日天气提醒",
        "desp": content,
        "openid": user_id
    }
    requests.post(url, data=data, timeout=15)


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


def get_access_token():
    appid = os.getenv("app_id")
    secret = os.getenv("app_secret")
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
    res = requests.get(url,timeout=15).json()
    print("微信token返回：",res) #打印返回信息查看错误
    if "access_token" in res:
        return res['access_token']
    else:
        raise Exception(f"获取token失败:{res}")


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
    weather = get_weather()
    token = get_access_token()
    for openid in config["user"]:
        send_one_user(openid, weather, token)
    print("✅全部用户推送完毕")


# 只保留唯一程序入口，不会重复执行
if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"❌程序异常：{err}")
