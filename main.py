import json
import requests
from datetime import datetime
import ephem

# ========== 加载配置文件 强制调试打印 ==========
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print("读取config.json失败！", e)
    exit()

WX_APPID = config["app_id"]
WX_SECRET = config["app_secret"]
TEMPLATE_ID = config["template_id"]
USER_OPENID_LIST = config["user"]
GAODE_KEY = config["gaode_key"]
ADCODE = config["adcode"]
REGION = config["region"]

# 关键调试：打印读取到的公众号AppID
print(f"【调试信息】已读取到 app_id = {WX_APPID}")


# ========== 获取微信access_token ==========
def get_access_token():
    url = (f"https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={WX_APPID}&secret={WX_SECRET}")
    res = requests.get(url, timeout=15).json()
    print("微信token返回：", res)
    if "access_token" in res:
        return res["access_token"]
    else:
        raise Exception(f"获取token失败:{res}")


# ========== 获取高德天气 ==========
def get_weather():
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={ADCODE}&key={GAODE_KEY}"
    resp = requests.get(url, timeout=15).json()
    print("高德返回数据：", resp)
    today_info = resp["forecasts"][0]["casts"][0]
    weather_data = {
        "region": REGION,
        "weather": today_info["dayweather"],
        "temp_low": today_info["nighttemp"],
        "temp_high": today_info["daytemp"],
        "wind_dir": f'{today_info["daywind"]}风 {today_info["daypower"]}级'
    }
    # 临沂经纬度计算日出日落
    observer = ephem.Observer()
    observer.lat, observer.lon = '35.06', '118.33'
    sun = ephem.Sun()
    sunrise = observer.next_rising(sun).datetime().strftime("%H:%M")
    sunset = observer.next_setting(sun).datetime().strftime("%H:%M")
    weather_data["sunrise"] = sunrise
    weather_data["sunset"] = sunset
    return weather_data


# ========== 发送微信模板消息 ==========
def send_wx_template(access_token, openid, weather):
    api_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    post_data = {
        "touser": openid,
        "template_id": TEMPLATE_ID,
        "data": {
            "region": {"value": weather["region"]},
            "weather": {"value": weather["weather"]},
            "temp": {"value": f'{weather["temp_low"]}~{weather["temp_high"]}℃'},
            "wind": {"value": weather["wind_dir"]},
            "rise": {"value": weather["sunrise"]},
            "set": {"value": weather["sunset"]}
        }
    }
    result = requests.post(api_url, json=post_data).json()
    print(f"推送用户{openid}返回结果：{result}")


# ========== 主入口 ==========
if __name__ == "__main__":
    try:
        token = get_access_token()
        weather_info = get_weather()
        for openid in USER_OPENID_LIST:
            send_wx_template(token, openid, weather_info)
        print("✅ 微信模板消息推送完毕")
    except Exception as err:
        print(f"❌程序异常：{err}")

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
