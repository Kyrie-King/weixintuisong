import json
import requests
from datetime import date
import time
import warnings
warnings.filterwarnings("ignore")

# ========== 读取本地 config.json 配置 ==========
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
ADCODE = "371300"
REGION = "临沂市"

# 纪念日配置
love_start_date = date(2024, 6, 5)
jiaojiao_birth = date(2004, 12, 5)
zhangzhe_birth = date(2004, 10, 12)

# 获取微信access‑token
def get_access_token():
    url = (f"https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={WX_APPID}&secret={WX_SECRET}")
    res = requests.get(url, timeout=30, verify=False).json()
    print("微信token返回：", res)
    if "access_token" in res:
        return res["access_token"]
    else:
        raise Exception(f"获取token失败:{res}")

# 获取高德天气（直接读取接口自带日出日落，不再使用ephem）
def get_weather():
    # base 获取实时实况 lives
    url_live = f"https://restapi.amap.com/v3/weather/weatherInfo?city={ADCODE}&key={GAODE_KEY}&extensions=base"
    # all 获取多日预报、原生日出日落
    url_forecast = f"https://restapi.amap.com/v3/weather/weatherInfo?city={ADCODE}&key={GAODE_KEY}&extensions=all"

    # 请求实况天气，最多重试3次
    resp_live = None
    for i in range(3):
        try:
            resp_live = requests.get(url_live, timeout=30, verify=False).json()
            print("实况天气返回：",resp_live)
            if resp_live.get("status") == "1" and "lives" in resp_live:
                break
        except Exception as e:
            print(f"实况第{i+1}次请求失败：{e}")
            time.sleep(2)
    if resp_live is None or resp_live["status"]!="1":
        raise RuntimeError("获取实时天气失败")

    # 请求每日预报
    resp_forecast = None
    for i in range(3):
        try:
            resp_forecast = requests.get(url_forecast, timeout=30, verify=False).json()
            print("预报天气返回：",resp_forecast)
            if resp_forecast.get("status") == "1" and "forecasts" in resp_forecast:
                break
        except Exception as e:
            print(f"预报第{i+1}次请求失败：{e}")
            time.sleep(2)
    if resp_forecast is None or resp_forecast["status"]!="1":
        raise RuntimeError("获取天气预报失败")


    live_info = resp_live["lives"][0]
    forecast_today = resp_forecast["forecasts"][0]["casts"][0]

    weather_data = {
        "city": REGION,
        "weather": forecast_today["dayweather"],
        "real_temp": live_info["temperature"],
        "min_temperature": forecast_today["nighttemp"],
        "max_temperature": forecast_today["daytemp"],
        "wind_direction": f"{forecast_today['daywind']}风 {forecast_today['daypower']}级",
        "sunrise": forecast_today["sunrise"],
        "sunset": forecast_today["sunset"]
    }
    # 容错，防止实时气温高于当日最高预报温度
    if float(weather_data["real_temp"])>float(weather_data["max_temperature"]):
        weather_data["max_temperature"]=weather_data["real_temp"]
    return weather_data

# 日期计算
def calc_day_num():
    today = date.today()
    love_day = (today - love_start_date).days

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

#发送推送
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
    return result


if __name__ == "__main__":
    token = get_access_token()
    weather_info = get_weather()
    date_text, together_days, info_birth1, info_birth2 = calc_day_num()
    for openid in USER_OPENID_LIST:
        send_wx_template(token, openid, weather_info, date_text, together_days, info_birth1, info_birth2)
    print("✅ 娇娇专属推送执行完毕")
