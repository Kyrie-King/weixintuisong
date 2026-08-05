import requests
import json
import os
import sys
from datetime import datetime

# ==========直接粘贴你的全部配置，不再读取外部文件==========
conf = {
    "app_id": "wxe56a269a1ad4ca32",
    "app_secret": "1ecaa3c14689d2a9d232b3dec9c82026",
    "template_id": "CIDOS0Xso8pGa3tvHN1vnsF8dIRQOitbPlAeVuqXXaE",
    "user": ["oWI8T3D6BIR55LSHqDmUu3i91tDU","oWI8T3KwC0WLy_NTI_HEtD5Z43Go"],
    "weather_key": "4115864138f647969ab28d83a463829a",
    "hefeng_key": "2c4595bee21046ec8de24159b74b4d8d",
    "city_code": "101120913",
    "gaode_key": "32b673b0e64f0b215ebd507640a8a474",
    "region": "101120101",
    "birthday1": {"name": "娇娇", "birthday": "r-03-07"},
    "birthday2": {"name": "张喆", "birthday": "r-10-24"},
    "love_date": "2024-06-29",
    "note_ch": "",
    "note_en": ""
}

# ============加载公众号参数============
APPID = conf["app_id"]
APPSECRET = conf["app_secret"]
TEMPLATE_ID = conf["template_id"]
USER_LIST = conf["user"]

# ============和风天气参数，已经废弃高德============
QWEATHER_API_KEY = conf["weather_key"]
# 临沂市河东区经纬度
HE_DONG_LON = "118.40"
HE_DONG_LAT = "35.08"

note_ch = conf["note_ch"]
note_en = conf["note_en"]

# ----------------------获取微信access_token----------------------
def get_access_token():
    url = (f"https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={APPID}&secret={APPSECRET}")
    res = requests.get(url,timeout=15).json()
    if "access_token" not in res:
        print("获取token失败",res)
        sys.exit(1)
    return res["access_token"]

# ----------------------和风天气接口函数----------------------
def get_weather(city_adcode):
    url_now = (f"https://devapi.qweather.com/v7/weather/now"
               f"?location={HE_DONG_LON},{HE_DONG_LAT}&key={QWEATHER_API_KEY}")
    resp_now = requests.get(url_now, timeout=15).json()
    now_data = resp_now["now"]

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

# ----------------------每日一句----------------------
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

# ----------------------发送模板消息----------------------
def send_msg(access_token, openid, weather, real_temp, min_temp, max_temp, wind_dir, saying_text):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
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
    headers = {"Content-Type": "application/json"}
    requests.post(url, data=json.dumps(post_data), headers=headers,timeout=15)


if __name__ == '__main__':
    token = get_access_token()
    weather, real_temp, min_temp, max_temp, wind_dir = get_weather(None)
    ch_text,en_text = get_ciba()

    for one_openid in USER_LIST:
        send_msg(token, one_openid, weather, real_temp, min_temp, max_temp, wind_dir, ch_text)

    print("✅ 全部消息推送执行完毕")
