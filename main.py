import json
import requests
from datetime import datetime, date
import ephem
import time

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
    res = requests.get(url, timeout=30, verify=False).json()
    print("微信token返回：", res)
    if "access_token" in res:
        return res["access_token"]
    else:
        raise Exception(f"获取token失败:{res}")

# ========== 获取高德天气，加入重试、超时、异常兜底 ==========
def get_weather():
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={ADCODE}&key={GAODE_KEY}&extensions=all"
    retry_times = 3
    resp = None
    for i in range(retry_times):
        try:
            resp = requests.get(url, timeout=30, verify=False).json()
            if resp.get("status") == "1":
                break
        except Exception as e:
            print(f"第{i+1}次请求高德超时，正在重试,错误:{e}")
            time.sleep(2)

    # 请求失败兜底默认天气，防止程序直接崩溃终止推送
    if resp is None or resp.get("status") != "1":
        print("高德天气接口全部重试失败，启用兜底天气数据")
        weather_data = {
            "city": REGION,
            "weather":"多云",
            "real_temp":"32",
            "min_temperature":"19",
            "max_temperature":"29",
            "wind_direction":"东南风 3级",
            "sunrise":"05:10",
            "sunset":"19:00"
        }
        return weather_data

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
            next_b = date(today.year+1, birth.month, birth.day)
        return (next_b - today).days

    rem_jj = get_next_birthday(jiaojiao_birth)
    rem_zz = get_next_birthday(zhangzhe_birth)
    birthday1 = f"距离娇娇的生日还有{rem_jj}天"
    birthday2 = f"距离张喆的生日还有{rem_zz}天"

    now_date_str = today.strftime("%Y-%m-%d 星期三")
    return now_date_str, love_day, birthday1, birthday2


# ========== 发送微信模板消息（键严格匹配你的模板） ==========
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
    result = requests.post(api_url, json=post_data,timeout=30,verify=False).json()
    print(f"推送用户{openid}返回结果：{result}")


# ========== 程序入口 ==========
if __name__ == "__main__":
    token = get_access_token()
    weather_info = get_weather()
    date_text, together_days, info_birth1, info_birth2 = calc_day_num()

    for openid in USER_OPENID_LIST:
        send_wx_template(token, openid, weather_info, date_text, together_days, info_birth1, info_birth2)
    print("✅ 娇娇专属推送执行完毕")
