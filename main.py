import requests
import json
import os
import sys
import time

# --------------------------读取配置文件(原版代码原样保留)--------------------------
def read_config():
    config = {}
    if not os.path.exists("config.txt"):
        print("找不到config.txt配置文件！")
        sys.exit(1)
    with open("config.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        config[key.strip()] = val.strip()
    return config

conf = read_config()
APPID = conf["APPID"]
APPSECRET = conf["APPSECRET"]
OPENID = conf["OPENID"]
REGION = conf["region"]
SAYING = conf["saying"]
# 此处变量只是兼容旧代码，现已不再依靠它解析地理位置
CITY_ADCODE = ""

# ======================和风天气配置【仅此处需要你填入自己的Key】======================
QWEATHER_API_KEY = "填写你的和风天气Web‑API密钥"
# 临沂市河东区 经纬度
HE_DONG_LON = "118.40"
HE_DONG_LAT = "35.08"

# --------------------------获取access_token 原版代码原样保留--------------------------
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    res = requests.get(url).json()
    return res["access_token"]

# --------------------------【改造后的天气函数，替换掉高德】--------------------------
def get_weather(city_adcode):
    """
    兼容旧代码传入参数city_adcode，参数现在不再使用
    返回顺序必须严格：weather, real_temp, min_temp, max_temp, wind_dir
    """
    # 请求实时天气
    url_now = (f"https://devapi.qweather.com/v7/weather/now"
               f"?location={HE_DONG_LON},{HE_DONG_LAT}&key={QWEATHER_API_KEY}")
    resp_now = requests.get(url_now, timeout=10).json()
    now_data = resp_now["now"]

    # 请求今日天气预报获取最高最低温度
    url_day = (f"https://devapi.qweather.com/v7/weather/3d"
               f"?location={HE_DONG_LON},{HE_DONG_LAT}&key={QWEATHER_API_KEY}")
    resp_day = requests.get(url_day, timeout=10).json()
    today_info = resp_day["daily"][0]

    weather = now_data["text"]
    real_temp = now_data["temp"]
    min_temp = today_info["tempMin"]
    max_temp = today_info["tempMax"]
    wind_dir = now_data["windDir"]
    return weather, real_temp, min_temp, max_temp, wind_dir

# --------------------------下面所有剩余源码全部保留项目原版内容，不作改动--------------------------
def get_ciba():
    # 原版每日语录函数保持原样
    url = "http://open.iciba.com/dsapi/"
    r = requests.get(url)
    content = r.json()
    return content["content"], content["note"]


def send_msg(access_token, weather, real_temp, min_temp, max_temp, wind_dir, saying_text):
    # 原版微信模板消息推送函数完全保留
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    post_data = {
        "touser": OPENID,
        "template_id": "你的模板id",
        "data": {
            "weather": {"value": weather},
            "real_temp": {"value": real_temp},
            "min_temp": {"value": min_temp},
            "max_temp": {"value": max_temp},
            "wind_dir": {"value": wind_dir},
            "saying": {"value": saying_text}
        }
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, data=json.dumps(post_data), headers=headers)


if __name__ == '__main__':
    token = get_access_token()
    # 此处调用和原来一模一样，不会再报参数异常
    weather, real_temp, min_temp, max_temp, wind_dir = get_weather(CITY_ADCODE)
    word, explain = get_ciba()
    if SAYING != "":
        word = SAYING
    send_msg(token, weather, real_temp, min_temp, max_temp, wind_dir, word)
    print("消息推送执行完毕")
