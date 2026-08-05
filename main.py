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

import requests
import sys

def get_weather():
    # 在这里放入你全部的 api‑key
    key_list = [
        "2c4595bee21046ec8de24159b74b4d8d",
        "4115864138f647969ab28d83a463829a",
        "d9fd4a0ab55d4b14a45ea7ec31ecc5a8"
    ]
    location = "118.85,35.06"  # 临沂 经度,纬度
    
    for api_key in key_list:
        try:
            # 官方 每日天气预报接口
            url = "https://devapi.qweather.com/v7/weather/3d"
            params = {
                "location": location,
                "key": api_key
            }
            resp = requests.get(url, params=params, timeout=15)
            res_json = resp.json()
            
            # 判断接口返回成功码
            if res_json.get("code") == "200":
                now_url = "https://devapi.qweather.com/v7/weather/now"
                now_resp = requests.get(now_url,params=params,timeout=15)
                now_json = now_resp.json()
                
                if now_json.get("code") != "200":
                    continue
                
                today_forecast = res_json["daily"][0]
                now_info = now_json["now"]
                
                weather_data = {
                    "weather": now_info["text"],
                    "temp_now": now_info["temp"],
                    "temp_min": today_forecast["tempMin"],
                    "temp_max": today_forecast["tempMax"],
                    "wind_dir": now_info["windDir"],
                    "sunrise": today_forecast["sunrise"],
                    "sunset": today_forecast["sunset"]
                }
                return weather_data

        except Exception:
            # 请求超时、网络异常则切换下一条密钥
            continue
    
    # 所有密钥全部尝试完毕依旧失败，退出程序，放弃推送
    print("❌ 全部密钥尝试之后依旧异常 code≠200，放弃推送")
    sys.exit(1)


# 调用测试
if __name__ == "__main__":
    data = get_weather()
    print(data)
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
