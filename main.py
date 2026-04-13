import random
from time import localtime, sleep
import requests
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os


def system_pause():
    if os.name == 'nt':
        os.system("pause")
    else:
        input("\n按回车退出……")


def get_color():
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = (
        "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
        .format(app_id, app_secret)
    )
    try:
        response = requests.get(post_url, timeout=15)
        response.raise_for_status()
        access_token = response.json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret")
        system_pause()
        sys.exit(1)
    except Exception as e:
        print(f"获取access_token异常：{e}")
        system_pause()
        sys.exit(1)
    return access_token


def get_weather(region):
    key = config["weather_key"]

    # 实时天气
    try:
        url_now = f"https://devapi.qweather.com/v7/weather/now?location={region}&key={key}"
        res_now = requests.get(url_now, timeout=10).json()
    except:
        res_now = {"code": "400"}

    # 今日预报（高低温）
    try:
        url_3d = f"https://devapi.qweather.com/v7/weather/3d?location={region}&key={key}"
        res_3d = requests.get(url_3d, timeout=10).json()
    except:
        res_3d = {"code": "400"}

    # 日出日落
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        url_sun = f"https://devapi.qweather.com/v7/astronomy/sun?location={region}&date={today_str}&key={key}"
        res_sun = requests.get(url_sun, timeout=10).json()
    except:
        res_sun = {"code": "400"}

    # 默认值，防止接口崩掉
    weather = "晴"
    temp_now = "22℃"
    wind_dir = "东风"
    min_temp = "15℃"
    max_temp = "28℃"
    sunrise = "06:00"
    sunset = "18:00"

    if res_now.get("code") == "200":
        weather = res_now["now"]["text"]
        temp_now = res_now["now"]["temp"] + "℃"
        wind_dir = res_now["now"]["windDir"]

    if res_3d.get("code") == "200" and len(res_3d["daily"]) > 0:
        min_temp = res_3d["daily"][0]["tempMin"] + "℃"
        max_temp = res_3d["daily"][0]["tempMax"] + "℃"

    if res_sun.get("code") == "200":
        try:
            sunrise = res_sun["sunrise"][11:16]
            sunset = res_sun["sunset"][11:16]
        except:
            pass

    return weather, temp_now, wind_dir, min_temp, max_temp, sunrise, sunset


def get_birthday(birthday_str, year, today):
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
                next_lunar = ZhDate(year + 1, int(month), int(day))
                next_solar = next_lunar.to_datetime().date()
                birthday_date = date(year + 1, next_solar.month, next_solar.day)
            else:
                birthday_date = date(year + 1, int(month), int(day))
            days = str((birthday_date - today).days)
        elif today == birthday_date:
            days = "0"
        else:
            days = str((birthday_date - today).days)
        return days
    except:
        return "?"


def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    try:
        ciba_data = requests.get(url, timeout=10).json()
        note_en = ciba_data.get("content", "Good day")
        note_ch = ciba_data.get("note", "今天也要开心呀")
    except:
        note_en = "Good day"
        note_ch = "今天也要开心呀"
    return note_ch, note_en


def send_message(to_user, access_token, region, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    try:
        love_year, love_month, love_day = map(int, config["love_date"].split("-"))
        love_date = date(love_year, love_month, love_day)
        love_days = str((today - love_date).days)
    except:
        love_days = "0"

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": region, "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()}
        }
    }

    # 生日1
    try:
        if "birthday1" in config:
            b1_days = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
            b1_text = f"今天{config['birthday1']['name']}生日🎂！" if b1_days == "0" else f"距离{config['birthday1']['name']}生日还有{b1_days}天"
            data["data"]["birthday1"] = {"value": b1_text, "color": get_color()}
    except:
        pass

    # 生日2
    try:
        if "birthday2" in config:
            b2_days = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
            b2_text = f"今天{config['birthday2']['name']}生日🎂！" if b2_days == "0" else f"距离{config['birthday2']['name']}生日还有{b2_days}天"
            data["data"]["birthday2"] = {"value": b2_text, "color": get_color()}
    except:
        pass

    try:
        resp = requests.post(url, json=data, timeout=15)
        result = resp.json()
        if result["errcode"] == 0:
            print(f"推送成功：{to_user}")
        else:
            print(f"推送失败：{result}")
    except Exception as e:
        print(f"推送异常：{e}")


if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except:
        print("config.txt 读取错误！")
        system_pause()
        sys.exit()

    must = ["app_id", "app_secret", "weather_key", "template_id", "user", "region", "love_date"]
    for key in must:
        if key not in config:
            print(f"缺少配置：{key}")
            system_pause()
            sys.exit()

    access_token = get_access_token()
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])
    note_ch, note_en = get_ciba()

    for user in config["user"]:
        send_message(user, access_token, config["region"], weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)

    print("\n执行完毕")
    system_pause()
