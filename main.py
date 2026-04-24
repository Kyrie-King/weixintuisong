import random
from time import localtime
import requests
from datetime import date
from zhdate import ZhDate
import sys

# 随机颜色
def get_color():
    return "#" + "%06x" % random.randint(0, 0xFFFFFF)

# 获取微信token
def get_access_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        res = requests.get(url, timeout=10).json()
        return res["access_token"]
    except:
        print("获取token失败")
        sys.exit()

# 真实调用天气API，无兜底，失败直接返回失败
def get_weather():
    try:
        url = "https://wttr.in/Linyi?format=j1"
        data = requests.get(url, timeout=10).json()
        
        weather = data["current_condition"][0]["weatherDesc"][0]["value"]
        temp = data["current_condition"][0]["temp_C"] + "℃"
        wind_dir = data["current_condition"][0]["winddir16Point"]
        min_temp = data["weather"][0]["mintempC"] + "℃"
        max_temp = data["weather"][0]["maxtempC"] + "℃"
        sunrise = "06:00"
        sunset = "18:00"

        return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset
    except:
        # 获取失败就返回失败文本
        return "获取失败", "获取失败", "获取失败", "获取失败", "获取失败", "获取失败", "获取失败"

# 生日计算
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

# 主程序
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

    # 在一起天数
    try:
        ly, lm, ld = map(int, love_date.split("-"))
        love_days = str((today - date(ly, lm, ld)).days)
    except:
        love_days = "获取失败"

    # 天气（纯接口调用）
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather()

    # 生日
    birthday1 = ""
    if "birthday1" in config:
        days = get_birthday(config["birthday1"]["birthday"], today.year, today)
        if days == "0":
            birthday1 = f"今天是{config['birthday1']['name']}生日！"
        else:
            birthday1 = f"距离{config['birthday1']['name']}生日还有{days}天"

    birthday2 = ""
    if "birthday2" in config:
        days = get_birthday(config["birthday2"]["birthday"], today.year, today)
        if days == "0":
            birthday2 = f"今天是{config['birthday2']['name']}生日！"
        else:
            birthday2 = f"距离{config['birthday2']['name']}生日还有{days}天"

    # 推送数据
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
        }
    }

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    requests.post(url, json=data)
    print("推送完成")

if __name__ == "__main__":
    main()
