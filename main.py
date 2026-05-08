import random
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os


def get_color():
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        resp = get(post_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        access_token = data['access_token']
    except Exception as e:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        print(f"错误：{e}")
        if 'resp' in locals():
            print(f"返回：{resp.text}")
        sys.exit(1)
    return access_token


def get_weather(region):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    }
    key = config["weather_key"]
    location_id = "101120101"  # 临沂固定ID

    weather_url = "https://devapi.qweather.com/v7/weather/now"
    params = {
        "location": location_id,
        "key": key
    }
    try:
        print(f"请求天气接口：{weather_url}")
        print(f"参数：location={location_id}, key={key[:8]}******")
        resp = get(weather_url, headers=headers, params=params, timeout=15)
        print(f"HTTP状态码：{resp.status_code}")
        print(f"完整返回：{resp.text}")
        response = resp.json()
    except Exception as e:
        print("获取天气请求失败")
        print(f"错误：{e}")
        if 'resp' in locals():
            print(f"返回内容：{resp.text}")
        sys.exit(1)

    # 处理API错误返回
    if response.get("code") != "200":
        print(f"和风天气API错误：code={response.get('code')}, message={response.get('message')}")
        sys.exit(1)

    # 处理KeyError
    if "now" not in response:
        print("错误：返回JSON中没有'now'字段")
        print(f"完整返回：{response}")
        sys.exit(1)

    weather = response["now"]["text"]
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
    wind_dir = response["now"]["windDir"]
    print(f"获取天气成功：{weather}, {temp}, {wind_dir}")
    return weather, temp, wind_dir


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        try:
            birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            sys.exit(1)
        birthday_month = birthday.month
        birthday_day = birthday.day
        year_date = date(year, birthday_month, birthday_day)

    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        year_date = date(year, birthday_month, birthday_day)

    if today > year_date:
        if birthday_year[0] == "r":
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        r = get(url, headers=headers, timeout=10)
        note_en = r.json()["content"]
        note_ch = r.json()["note"]
    except:
        note_ch = "今日句子加载失败"
        note_en = "Failed to load today's sentence"
    return note_ch, note_en


def send_message(to_user, access_token, region_name, weather, temp, wind_dir, note_ch, note_en):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]

    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    love_days = str(today.__sub__(love_date)).split(" ")[0]

    birthdays = {}
    for k, v in config.items():
        if k.startswith("birth"):
            birthdays[k] = v

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": get_color()
            },
            "region": {
                "value": region_name,
                "color": get_color()
            },
            "weather": {
                "value": weather,
                "color": get_color()
            },
            "temp": {
                "value": temp,
                "color": get_color()
            },
            "wind_dir": {
                "value": wind_dir,
                "color": get_color()
            },
            "love_day": {
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            }
        }
    }

    for key, value in birthdays.items():
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = f"今天{value['name']}生日哦，祝{value['name']}生日快乐！"
        else:
            birthday_data = f"距离{value['name']}的生日还有{birth_day}天"
        data["data"][key] = {"value": birthday_data, "color": get_color()}

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = post(url, headers=headers, json=data, timeout=15).json()
    except Exception as e:
        print("发送消息失败：", e)
        return

    if response.get("errcode") == 0:
        print("推送消息成功")
    else:
        print("推送失败：", response)


if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except Exception as e:
        print("配置文件读取失败：", e)
        sys.exit(1)

    print("=== 开始运行 ===")
    accessToken = get_access_token()
    users = config["user"]
    region = config["region"]

    weather, temp, wind_dir = get_weather(region)
    note_ch = config["note_ch"]
    note_en = config["note_en"]
    if not note_ch and not note_en:
        note_ch, note_en = get_ciba()

    for user in users:
        send_message(user, accessToken, region, weather, temp, wind_dir, note_ch, note_en)
