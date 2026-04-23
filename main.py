import random
from time import localtime
import requests
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os


def get_color():
    """生成随机16进制颜色码"""
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    """获取微信公众号access_token"""
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = (
        "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
        .format(app_id, app_secret)
    )
    try:
        response = requests.get(post_url, timeout=10)
        response.raise_for_status()
        access_token = response.json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        sys.exit(1)
    except Exception as e:
        print(f"获取access_token异常：{str(e)}")
        sys.exit(1)
    return access_token


def get_weather():
    """固定获取临沂天气，改用免费无风控的API"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    # 临沂固定信息，避免API调用失败
    weather = "多云"
    temp = "25℃"
    wind_dir = "南风"
    min_temp = "18℃"
    max_temp = "32℃"
    sunrise = "06:00"
    sunset = "18:00"

    # 用免费的公共天气API兜底，也可以用和风天气备用
    try:
        url = "https://wttr.in/Linyi?format=j1"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        weather = data["current_condition"][0]["weatherDesc"][0]["value"]
        temp = f"{data['current_condition'][0]['temp_C']}℃"
        wind_dir = data["current_condition"][0]["winddir16Point"]
        min_temp = f"{data['weather'][0]['mintempC']}℃"
        max_temp = f"{data['weather'][0]['maxtempC']}℃"
        print(f"✅ 天气获取成功：{weather} {temp}")
    except Exception as e:
        print(f"❌ 获取天气失败，使用默认数据：{str(e)}")

    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset


def get_birthday(birthday_str, year, today):
    """计算生日倒计时 + 生日当天自动发送祝福"""
    try:
        if birthday_str.startswith("r"):
            _, month, day = birthday_str.split("-")
            lunar_date = ZhDate(year, int(month), int(day))
            solar_date = lunar_date.to_datetime().date()
            birthday_date = date(year, solar_date.month, solar_date.day)
        else:
            _, month, day = birthday_str.split("-")
            birthday_date = date(year, int(month), int(day))

        if today > birthday_date:
            if birthday_str.startswith("r"):
                next_lunar = ZhDate(year+1, int(month), int(day))
                next_solar = next_lunar.to_datetime().date()
                birthday_date = date(year+1, next_solar.month, next_solar.day)
            else:
                birthday_date = date(year+1, int(month), int(day))
            days = str((birthday_date - today).days)
        elif today == birthday_date:
            days = "0"
        else:
            days = str((birthday_date - today).days)
        return days
    except Exception as e:
        print(f"计算生日天数异常：{str(e)}")
        return "未知"


def get_ciba():
    """获取每日金句"""
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        ciba_data = resp.json()
        note_en = ciba_data.get("content", "Keep going")
        note_ch = ciba_data.get("note", "每天都有新的希望")
    except Exception as e:
        print(f"获取金句失败：{str(e)}")
        note_en = "Keep going"
        note_ch = "每天都有新的希望"
    return note_ch, note_en


def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    """推送消息，城市固定显示临沂"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    try:
        love_year, love_month, love_day = map(int, config["love_date"].split("-"))
        love_date = date(love_year, love_month, love_day)
        love_days = str((today - love_date).days)
    except Exception as e:
        print(f"计算在一起天数异常：{str(e)}")
        sys.exit(1)

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "region": {"value": "临沂", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()},
            "city": {"value": "临沂", "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()}
        }
    }

    try:
        if "birthday1" in config:
            b1_days = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
            if b1_days == "0":
                b1_text = f"🎉 今天是{config['birthday1']['name']}的生日！祝生日快乐，天天开心，万事顺意！🎂"
            else:
                b1_text = f"距离{config['birthday1']['name']}生日还有{b1_days}天"
            data["data"]["birthday1"] = {"value": b1_text, "color": get_color()}
        
        if "birthday2" in config:
            b2_days = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
            if b2_days == "0":
                b2_text = f"🎉 今天是{config['birthday2']['name']}的生日！祝生日快乐，平安喜乐，岁岁无忧！🎂"
            else:
                b2_text = f"距离{config['birthday2']['name']}生日还有{b2_days}天"
            data["data"]["birthday2"] = {"value": b2_text, "color": get_color()}
    except Exception as e:
        print(f"处理生日数据异常：{str(e)}")
        sys.exit(1)

    try:
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=data, timeout=10)
        resp.raise_for_status()
        resp_data = resp.json()
        if resp_data["errcode"] == 0:
            print(f"向 {to_user} 推送成功！")
        else:
            print(f"推送失败：{resp_data.get('errmsg')}")
    except Exception as e:
        print(f"推送消息异常：{str(e)}")


if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("找不到config.txt文件！")
        sys.exit(1)
    except SyntaxError:
        print("config.txt格式错误，请检查！")
        sys.exit(1)
    except Exception as e:
        print(f"读取配置异常：{str(e)}")
        sys.exit(1)

    must_have = ["app_id", "app_secret", "template_id", "user", "love_date"]
    for key in must_have:
        if key not in config:
            print(f"配置缺失：{key}")
            sys.exit(1)

    access_token = get_access_token()
    users = config["user"]
    if not isinstance(users, list) or len(users) == 0:
        print("user字段必须是非空列表！")
        sys.exit(1)

    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather()

    note_ch = config.get("note_ch", "")
    note_en = config.get("note_en", "")
    if not note_ch or not note_en:
        note_ch, note_en = get_ciba()

    for user in users:
        send_message(user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)
