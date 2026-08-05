import json
import requests
from datetime import datetime, date
import ephem

# ========== 加载配置文件 config.json ==========
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

print(f"【调试信息】已读取到 app_id = {WX_APPID}")

# ---------------------- 配置纪念日、生日 ----------------------
love_start_date = date(2024, 6, 5)      # 相恋起始日期
jiaojiao_birth = date(2004, 12, 5)     # 娇娇生日
zhangzhe_birth = date(2004, 10, 12)    # 张喆生日

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

# ========== 获取高德实时天气+预报天气 ==========
def get_weather():
    # extensions=all 返回实况 + 多天预报
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={ADCODE}&key={GAODE_KEY}&extensions=all"
    resp = requests.get(url, timeout=15).json()
    print("高德返回数据：", resp)
    
    live_info = resp["lives"][0]          # 实时天气
    forecast_today = resp["forecasts"][0]["casts"][0] # 今日预报

    # 临沂经纬度计算日出日落
    observer = ephem.Observer()
    observer.lat, observer.lon = '35.06', '118.33'
    sun = ephem.Sun()
    sunrise = observer.next_rising(sun).datetime().strftime("%H:%M")
    sunset = observer.next_setting(sun).datetime().strftime("%H:%M")

    weather_data = {
        "city": REGION,
        "weather": forecast_today["dayweather"],
        "real_temp": live_info["temperature"],
        "min_temperature": forecast_today["nighttemp"],
        "max_temperature": forecast_today["daytemp"],
        "wind_direction": f"{forecast_today['daywind']}风 {forecast_today['daypower']}级",
        "sunrise": sunrise,
        "sunset": sunset
    }
    return weather_data

# ========== 计算相恋天数、生日剩余天数 ==========
def calc_day_num():
    today = date.today()
    # 在一起天数
    love_day = (today - love_start_date).days

    # 获取下一次生日倒计时
    def get_next_birthday(birth):
        try:
            next_b = date(today.year, birth.month, birth.day)
            if next_b < today:
                next_b = date(today.year + 1, birth.month, birth.day)
        except ValueError:
            # 处理2‑29闰年
            next_b = date(today.year+1, birth.month, birth.day)
        return (next_b - today).days

    rem_jj = get_next_birthday(jiaojiao_birth)
    rem_zz = get_next_birthday(zhangzhe_birth)
    birthday1 = f"距离娇娇的生日还有{rem_jj}天"
    birthday2 = f"距离张喆的生日还有{rem_zz}天"

    now_date_str = today.strftime("%Y-%m-%d 星期三")
    return now_date_str, love_day, birthday1, birthday2


# ========== 发送微信模板消息（键完全匹配你的模板） ==========
def send_wx_template(access_token, openid, weather, date_str, love_day, b1, b2):
    api_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    post_data = {
        "touser": openid,
        "template_id": TEMPLATE_ID,
        "data": {
            "date": {"value": date_str},
            "city": {"value": weather["city"]},
            "weather": {"value": weather["weather"]},
            "real_temp": {"value": weather["real_temp"]},
            "min_temperature": {"value": weather["min_temperature"]},
            "max_temperature": {"value": weather["max_temperature"]},
            "wind_direction": {"value": weather["wind_direction"]},
            "sunrise": {"value": weather["sunrise"]},
            "sunset": {"value": weather["sunset"]},
            "love_day": {"value": love_day},
            "birthday1": {"value": b1},
            "birthday2": {"value": b2}
        }
    }
    result = requests.post(api_url, json=post_data).json()
    print(f"推送用户{openid}返回结果：{result}")


# ========== 程序入口 ==========
if __name__ == "__main__":
    token = get_access_token()
    weather_info = get_weather()
    date_text, together_days, info_birth1, info_birth2 = calc_day_num()

    for openid in USER_OPENID_LIST:
        send_wx_template(token, openid, weather_info, date_text, together_days, info_birth1, info_birth2)
    print("✅ 娇娇专属推送执行完毕")


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
