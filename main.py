import requests
import json
import sys
from datetime import datetime

conf = {
    "app_id": "wxe56a269a1ad4ca32",
    "app_secret": "1ecaa3c14689d2a9d232b3dec9c82026",
    "template_id": "CIDOS0Xso8pGa3tvHN1vnsF8dIRQOitbPlAeVuqXXaE",
    "user": ["oWI8T3D6BIR55LSHqDmUu3i91tDU","oWI8T3KwC0WLy_NTI_HEtD5Z43Go"],
    "weather_key": "2c4595bee21046ec8de24159b74b4d8d",
    "birthday1": {"name": "娇娇", "birthday": "03-07"},
    "birthday2": {"name": "张喆", "birthday": "10-24"},
    "love_date": "2024-06-29",
}

QWEATHER_API_KEY = conf["weather_key"]
LON, LAT = "118.40", "35.08"

def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={conf['app_id']}&secret={conf['app_secret']}"
    res = requests.get(url,timeout=15).json()
    if "access_token" not in res:
        print("❌ Token获取失败，终止推送", res)
        sys.exit(1)
    return res["access_token"]

def get_weather_all():
    url_now = f"https://devapi.qweather.com/v7/weather/now?location={LON},{LAT}&key={QWEATHER_API_KEY}"
    resp_now = requests.get(url_now, timeout=15).json()
    url_3d = f"https://devapi.qweather.com/v7/weather/3d?location={LON},{LAT}&key={QWEATHER_API_KEY}"
    resp_3d = requests.get(url_3d, timeout=15).json()

    # 两个接口必须全部正常返回200，缺少任意字段直接退出
    if resp_now.get("code") != "200" or resp_3d.get("code") != "200":
        print("❌ 天气接口返回异常 code≠200，放弃推送")
        sys.exit(1)

    now = resp_now["now"]
    today = resp_3d["daily"][0]
    # 校验所有必填字段，不存在就终止
    need_keys_now = ["text", "temp", "windDir"]
    need_keys_daily = ["tempMin", "tempMax", "sunrise", "sunset"]
    for k in need_keys_now:
        if k not in now:
            print(f"❌ 实时天气缺失字段:{k}")
            sys.exit(1)
    for k in need_keys_daily:
        if k not in today:
            print(f"❌ 预报天气缺失字段:{k}")
            sys.exit(1)

    return {
        "weather": now["text"],
        "temp_now": now["temp"],
        "temp_min": today["tempMin"],
        "temp_max": today["tempMax"],
        "wind_dir": now["windDir"],
        "sunrise": today["sunrise"],
        "sunset": today["sunset"]
    }

def calc_day_count(start_date):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        now = datetime.now()
        return str((now - start).days + 1)
    except Exception as e:
        print("❌ 恋爱天数计算失败", e)
        sys.exit(1)

def get_birthday_left(birth_month_day):
    try:
        month, day = map(int, birth_month_day.split("-"))
        today = datetime.now()
        target_year = today.year
        target = datetime(target_year, month, day)
        if target < today:
            target = datetime(target_year + 1, month, day)
        return str((target - today).days)
    except Exception as e:
        print("❌ 生日倒计时计算失败", e)
        sys.exit(1)

def send_msg(token, openid, weather_data, love_days, day1_left, day2_left):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    payload = {
        "touser": openid,
        "template_id": conf["template_id"],
        "data": {
            "date": {"value": datetime.now().strftime("%Y-%m-%d %A")},
            "city": {"value": "临沂"},
            "weather": {"value": weather_data["weather"]},
            "temp_now": {"value": weather_data["temp_now"] + "℃"},
            "temp_min": {"value": weather_data["temp_min"] + "℃"},
            "temp_max": {"value": weather_data["temp_max"] + "℃"},
            "wind": {"value": weather_data["wind_dir"]},
            "sunrise": {"value": weather_data["sunrise"]},
            "sunset": {"value": weather_data["sunset"]},
            "love_days": {"value": love_days},
            "birth1": {"value": day1_left},
            "birth2": {"value": day2_left}
        }
    }
    resp = requests.post(url, json=payload, timeout=15).json()
    if resp.get("errcode") != 0:
        print(f"❌ 推送失败 openid:{openid}", resp)
    else:
        print(f"✅ 推送成功 openid:{openid}")

if __name__ == '__main__':
    access_token = get_access_token()
    weather_info = get_weather_all()
    together_days = calc_day_count(conf["love_date"])
    jiao_left = get_birthday_left(conf["birthday1"]["birthday"])
    zhang_left = get_birthday_left(conf["birthday2"]["birthday"])

    for open_id in conf["user"]:
        send_msg(access_token, open_id, weather_info, together_days, jiao_left, zhang_left)
