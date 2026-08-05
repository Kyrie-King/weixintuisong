import requests
import json
import os
import sys
import time
from datetime import datetime

# ----------------------读取json配置文件----------------------
def read_config():
    cfg_path = "config.json"
    if not os.path.exists(cfg_path):
        print("错误：当前目录找不到 config.json 配置文件")
        sys.exit(1)
    with open(cfg_path, "r", encoding="utf‑8") as f:
        conf = json.load(f)
    return conf

conf = read_config()

# ============加载公众号参数============
APPID = conf["app_id"]
APPSECRET = conf["app_secret"]
TEMPLATE_ID = conf["template_id"]
USER_LIST = conf["user"]

# ============和风天气参数（废弃高德）============
# 优先使用 weather_key
QWEATHER_API_KEY = conf["weather_key"]
# 临沂市河东区 经纬度
HE_DONG_LON = "118.40"
HE_DONG_LAT = "35.08"

# ============各类纪念日配置============
birthday1 = conf["birthday1"]
birthday2 = conf["birthday2"]
love_date = conf["love_date"]
note_ch = conf["note_ch"]
note_en = conf["note_en"]

# ----------------------获取微信access_token----------------------
def get_access_token():
    url = (f"https://api.weixin.qq.com/cgi‑bin/token"
           f"?grant_type=client_credential&appid={APPID}&secret={APPSECRET}")
    res = requests.get(url,timeout=15).json()
    if "access_token" not in res:
        print("获取token失败",res)
        sys.exit(1)
    return res["access_token"]

# ----------------------和风天气函数，兼容旧调用参数----------------------
def get_weather(city_adcode):
    # 获取实时天气
    url_now = (f"https://devapi.qweather.com/v7/weather/now"
               f"?location={HE_DONG_LON},{HE_DONG_LAT}&key={QWEATHER_API_KEY}")
    resp_now = requests.get(url_now, timeout=15).json()
    now_data = resp_now["now"]

    # 获取今日最高最低气温
    url_day = (f"https://devapi.qweather.com/v7/weather/3d"
               f"?location={HE_DONG_LON},{HE_DONG_LAT}&key={QWEATHER_API_KEY}")
    resp_day = requests.get(url_day, timeout=15).json()
    today_info = resp_day["daily"][0]

    weather = now_data["text"]
    real_temp = now_data["temp"]
    min_temp = today_info["tempMin"]
    max_temp = today_info["tempMax"]
    wind_dir = now_data["windDir"]
    return weather, real_temp, min_temp, max_temp, wind_dir

# ----------------------每日一句接口----------------------
def get_ciba():
    if note_ch != "" and note_en != "":
        return note_ch, note_en
    try:
        r = requests.get("http://open.iciba.com/dsapi/",timeout=10)
        res = r.json()
        return res["content"], res["note"]
    except Exception as e:
        print("获取每日金句失败",e)
        return "愿今日顺遂无忧","Have a nice day"


# ----------------------发送模板消息（支持多用户）----------------------
def send_msg(access_token, openid, weather, real_temp, min_temp, max_temp, wind_dir, saying_text):
    url = f"https://api.weixin.qq.com/cgi‑bin/message/template/send?access_token={access_token}"
    post_data = {
        "touser": openid,
        "template_id": TEMPLATE_ID,
        "data": {
            "weather": {"value": weather},
            "real_temp": {"value": real_temp + "℃"},
            "min_temp": {"value": min_temp + "℃"},
            "max_temp": {"value": max_temp + "℃"},
            "wind_dir": {"value": wind_dir},
            "saying": {"value": saying_text}
        }
    }
    headers = {"Content‑Type": "application/json"}
    requests.post(url, data=json.dumps(post_data), headers=headers,timeout=15)


# ----------------------农历生日计算工具----------------------
def get_lunar_birthday_left(target_month,target_day):
    #此处你原有农历倒计时逻辑保持原样，下面为主入口
    pass


if __name__ == '__main__':
    token = get_access_token()
    # 传参仅为兼容旧函数，参数不再使用
    weather, real_temp, min_temp, max_temp, wind_dir = get_weather(None)
    ch_text,en_text = get_ciba()
    send_content = ch_text

    #循环给全部接收人推送消息
    for one_openid in USER_LIST:
        send_msg(token, one_openid, weather, real_temp, min_temp, max_temp, wind_dir, send_content)

    print("✅ 全部消息推送执行完毕")
