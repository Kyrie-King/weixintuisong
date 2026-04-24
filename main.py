import random
import requests
from datetime import date
from zhdate import ZhDate
import sys

def get_color():
    return "#" + "%06x" % random.randint(0, 0xFFFFFF)

def get_access_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        res = requests.get(url, timeout=10).json()
        return res["access_token"]
    except Exception as e:
        print("❌ 获取token失败：", e)
        sys.exit(1)

def get_weather():
    return "晴", "24℃", "南风", "11℃", "24℃", "06:00", "18:00"

def get_birthday(birthday_str, year, today):
    try:
        if birthday_str.startswith("r"):
            _, m, d = birthday_str.split("-")
            lunar = ZhDate(year, int(m), int(d))
            birthday = lunar.to_datetime().date()
        else:
            _, m, d = birthday_str.split("-")
            birthday = date(year, int(m), int(d))

        if today > birthday:
            birthday = date(year + 1, birthday.month, birthday.day)
        days = (birthday - today).days
        return str(days) if days != 0 else "0"
    except:
        return "获取失败"

def main():
    with open("config.txt", encoding="utf-8") as f:
        config = eval(f.read())

    app_id = config["app_id"]
    app_secret = config["app_secret"]
    template_id = config["template_id"]
    user = config["user"][0]
    love_date = config["love_date"]

    access_token = get_access_token(app_id, app_secret)
    today = date.today()
    week = ["日", "一", "二", "三", "四", "五", "六"][today.weekday()]
    date_str = f"{today} 星期{week}"

    try:
        ly, lm, ld = map(int, love_date.split("-"))
        love_days = str((today - date(ly, lm, ld)).days)
    except:
        love_days = "获取失败"

    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather()

    birthday1 = ""
    if "birthday1" in config:
        days = get_birthday(config["birthday1"]["birthday"], today.year, today)
        birthday1 = f"今天是{config['birthday1']['name']}生日！" if days == "0" else f"距离{config['birthday1']['name']}生日还有{days}天"

    birthday2 = ""
    if "birthday2" in config:
        days = get_birthday(config["birthday2"]["birthday"], today.year, today)
        birthday2 = f"今天是{config['birthday2']['name']}生日！" if days == "0" else f"距离{config['birthday2']['name']}生日还有{days}天"

    love_word = "我喜欢你，胜于昨日，略匮明朝。"
    riddle_q = "什么门永远关不上？"
    riddle_a = "球门"

    data = {
        "touser": user,
        "template_id": template_id,
        "data": {
            "date": {"value": date_str},
            "city": {"value": "临沂"},
            "weather": {"value": weather},
            "temp": {"value": temp},
            "wind_dir": {"value": wind_dir},
            "min_temp": {"value": min_temp},
            "max_temp": {"value": max_temp},
            "sunrise": {"value": sunrise},
            "sunset": {"value": sunset},
            "love_day": {"value": love_days},
            "birthday1": {"value": birthday1},
            "birthday2": {"value": birthday2},
            "love_word": {"value": love_word},
            "riddle_q": {"value": riddle_q},
            "riddle_a": {"value": riddle_a}
        }
    }

    url = f"https://api.weixin.qq.com/cgi-bin/template/message/send?access_token={access_token}"
    try:
        resp = requests.post(url, json=data, timeout=10)
        print("✅ 推送成功：", resp.json())
    except Exception as e:
        print("❌ 推送失败：", e)

if __name__ == "__main__":
    main()
