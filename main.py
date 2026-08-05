import requests
import time

# ---------------------- 读取配置文件 ----------------------
def read_config():
    config = {}
    with open("config.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        config[k.strip()] = v.strip()
    return config


# ---------------------- 获取微信 AccessToken ----------------------
def get_access_token(appid, secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    res = requests.get(url, timeout=10)
    data = res.json()
    if "access_token" in data:
        return data["access_token"]
    print("获取token失败：", data)
    return None


# ----------------------【重写‑精准和风天气】----------------------
def get_weather_info(hefeng_key, loc_code):
    """返回：实时温度、最高温、最低温、天气状况、体感温度"""
    url = f"https://devapi.qweather.com/v7/weather/now?location={loc_code}&key={hefeng_key}"
    daily_url = f"https://devapi.qweather.com/v7/weather/3d?location={loc_code}&key={hefeng_key}"

    # 失败重试2次
    for i in range(3):
        try:
            now_resp = requests.get(url, timeout=10)
            now_json = now_resp.json()
            daily_resp = requests.get(daily_url, timeout=10)
            daily_json = daily_resp.json()

            now = now_json.get("now", {})
            today = daily_json.get("daily", [{}])[0]

            temp_now = now.get("temp")
            temp_feel = now.get("feelsLike")
            weather_text = now.get("text")
            temp_high = today.get("tempMax")
            temp_low = today.get("tempMin")

            print(f"调试-实时气温:{temp_now}℃ 最高:{temp_high} 最低:{temp_low}")
            return temp_now, temp_high, temp_low, weather_text, temp_feel

        except Exception as e:
            print(f"天气请求失败 第{i+1}次重试,err:{e}")
            time.sleep(2)
    return None, None, None, "获取天气失败", None


# ---------------------- 获取金山词霸每日一句 保留原功能 ----------------------
def get_ciba_sentence():
    try:
        res = requests.get("http://open.iciba.com/dsapi/", timeout=8)
        data = res.json()
        en = data.get("content")
        cn = data.get("note")
        return en, cn
    except Exception as e:
        print("获取每日一句失败", e)
        return "Have a nice day.", "祝你今天一切顺利"


# ---------------------- 发送微信模板消息 ----------------------
def send_wx_msg(access_token, openid_list, template_id, weather, sentence_en, sentence_cn):
    temp_now, temp_high, temp_low, weather_text, feel_temp = weather
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

    # 模板数据，你按照自己公众号模板字段适配即可
    post_data = {
        "touser": "",
        "template_id": template_id,
        "data": {
            "weather": {"value": weather_text},
            "now_temp": {"value": f"{temp_now}℃"},
            "high": {"value": f"{temp_high}℃"},
            "low": {"value": f"{temp_low}℃"},
            "feel": {"value": f"{feel_temp}℃"},
            "english": {"value": sentence_en},
            "chinese": {"value": sentence_cn}
        }
    }

    for openid in openid_list:
        post_data["touser"] = openid
        resp = requests.post(url, json=post_data, timeout=10)
        res_json = resp.json()
        print(f"推送用户{openid} 返回:{res_json}")


def main():
    cfg = read_config()
    appid = cfg["appid"]
    appsecret = cfg["appsecret"]
    template_id = cfg["template_id"]
    openids = cfg["openid"].split(",")
    hf_key = cfg["hefeng_key"]
    area_code = cfg["city_code"]

    token = get_access_token(appid, appsecret)
    if not token:
        input("获取微信token失败，回车退出")
        return

    weather_res = get_weather_info(hf_key, area_code)
    en_text, cn_text = get_ciba_sentence()
    send_wx_msg(token, openids, template_id, weather_res, en_text, cn_text)
    print("全部推送任务执行完毕")
    input("\n按下回车关闭窗口")


if __name__ == '__main__':
    main()
