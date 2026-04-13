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
        input("按回车退出")
        sys.exit(1)
    except Exception as e:
        print(f"获取access_token异常：{str(e)}")
        input("按回车退出")
        sys.exit(1)
    return access_token


def get_weather(region):
    """已全部改为 api.qweather.com 正式接口"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]

    location_id = "101120901"

    now_url = f"https://api.qweather.com/v7/weather/now?location={location_id}&key={key}"
    daily_url = f"https://api.qweather.com/v7/weather/3d?location={location_id}&key={key}"
    astro_url = f"https://api.qweather.com/v7/astronomy/sun?location={location_id}&date={date.today().strftime('%Y%m%d')}&key={key}"

    weather = "获取失败"
    temp = "获取失败"
    wind_dir = "获取失败"
    min_temp = "获取失败"
    max_temp = "获取失败"
    sunrise = "获取失败"
    sunset = "获取失败"

    try:
        resp = requests.get(now_url, headers=headers, timeout=10)
        resp.raise_for_status()
        now_data = resp.json()
        if now_data.get("code") == "200":
            weather = now_data["now"]["text"]
            temp = f"{now_data['now']['temp']}℃"
            wind_dir = now_data["now"]["windDir"]
    except Exception as e:
        print(f"获取实时天气失败：{str(e)}")

    try:
        resp = requests.get(daily_url, headers=headers, timeout=10)
        resp.raise_for_status()
        daily_data = resp.json()
        if daily_data.get("code") == "200" and daily_data.get("daily"):
            today_daily = daily_data["daily"][0]
            min_temp = f"{today_daily['tempMin']}℃"
            max_temp = f"{today_daily['tempMax']}℃"
    except Exception as e:
        print(f"获取高低温失败：{str(e)}")

    try:
        resp = requests.get(astro_url, headers=headers, timeout=10)
        resp.raise_for_status()
        astro_data = resp.json()
        if astro_data.get("code") == "200" and astro_data.get("sun"):
            sunrise = astro_data["sun"][0]["rise"]
            sunset = astro_data["sun"][0]["set"]
    except Exception as e:
        print(f"获取日出日落失败：{str(e)}")

    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset


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
                next_lunar = ZhDate(year+1, int(month), int(day))
                next_solar = next_lunar.to_datetime().date()
                birthday_date = date(year+1, next_solar.month, next_solar.day)
            else:
                birthday_date = date(year+1, int(month), int(day))
            days = str((birthday_date - today).days)
        elif today == birthday_date:
            days = "0"
        else:
            days = str((today - birthday_date).days)
        return days
    except:
        return "未知"


def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        res = r.json()
        note_en = res["content"]
        note_ch = res["note"]
        return note_ch, note_en
    except:
        return "加油！", "Come on!"


def send_message(to_user, access_token, region_name, weather, temperature, wind_direction, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]

    love_date = date(*map(int, config["love_date"].split("-")))
    love_days = str((today - love_date).days)

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": "{} {}".format(today, week), "color": get_color()},
            "region": {"value": region_name, "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temperature, "color": get_color()},
            "wind_dir": {"value": wind_direction, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
        }
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result["errcode"] == 0:
            print(f"推送成功：{to_user}")
        else:
            print(f"推送失败：{result}")
    except Exception as e:
        print(f"发送消息异常：{e}")


if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except:
        print("配置文件读取错误！")
        input("按回车退出")
        sys.exit()

    try:
        access_token = get_access_token()
        users = config["user"]
        region = config["region"]
        weather, temperature, wind_direction, min_temp, max_temp, sunrise, sunset = get_weather(region)
        note_ch, note_en = get_ciba()

        for user in users:
            send_message(user, access_token, "临沂市", weather, temperature, wind_direction, min_temp, max_temp, sunrise, sunset, note_ch, note_en)
    except Exception as e:
        print(f"运行异常：{e}")

    input("运行完毕，按回车退出")
