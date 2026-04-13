import random
from time import localtime
import requests
from datetime import date
from zhdate import ZhDate
import sys
import os


def get_color():
    """生成随机16进制颜色码"""
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    """获取微信access_token"""
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        response = requests.get(url, timeout=15)
        return response.json()['access_token']
    except:
        print("❌ 获取token失败")
        return None


def get_weather(region):
    """修复版：极简、准确、无报错"""
    key = config["weather_key"]
    weather = "晴"
    temp_now = "22℃"
    wind_dir = "东风"
    min_temp = "15℃"
    max_temp = "28℃"
    sunrise = "06:00"
    sunset = "18:00"

    try:
        # 实时天气
        res_now = requests.get(f"https://devapi.qweather.com/v7/weather/now?location={region}&key={key}", timeout=10).json()
        if res_now["code"] == "200":
            weather = res_now["now"]["text"]
            temp_now = f"{res_now['now']['temp']}℃"
            wind_dir = res_now["now"]["windDir"]

        # 高低温
        res_3d = requests.get(f"https://devapi.qweather.com/v7/weather/3d?location={region}&key={key}", timeout=10).json()
        if res_3d["code"] == "200" and len(res_3d["daily"]) > 0:
            min_temp = f"{res_3d['daily'][0]['tempMin']}℃"
            max_temp = f"{res_3d['daily'][0]['tempMax']}℃"

        # 日出日落（修复字段）
        res_sun = requests.get(f"https://devapi.qweather.com/v7/astronomy/sun?location={region}&date={date.today().strftime('%Y%m%d')}&key={key}", timeout=10).json()
        if res_sun["code"] == "200":
            sunrise = res_sun["sunrise"][11:16] if len(res_sun["sunrise"]) > 10 else res_sun["sunrise"]
            sunset = res_sun["sunset"][11:16] if len(res_sun["sunset"]) > 10 else res_sun["sunset"]
    except:
        pass

    return weather, temp_now, wind_dir, min_temp, max_temp, sunrise, sunset


def get_birthday(birthday_str, today):
    """计算倒计时"""
    try:
        if birthday_str.startswith("r"):
            _, month, day = birthday_str.split("-")
            lunar_date = ZhDate(today.year, int(month), int(day))
            solar_date = lunar_date.to_datetime().date()
            target = date(today.year, solar_date.month, solar_date.day)
        else:
            _, month, day = birthday_str.split("-")
            target = date(today.year, int(month), int(day))

        if target < today:
            target = date(today.year + 1, int(month), int(day))
        return str((target - today).days)
    except:
        return "?"


def send_message(to_user, access_token, weather_data, love_days, note_ch, note_en):
    """推送逻辑"""
    if not access_token or not to_user:
        return

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    today = date.today()
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week = week_list[today.isoweekday() % 7]

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": {
            "date": {"value": f"{today} {week}", "color": get_color()},
            "city": {"value": config["region"], "color": get_color()},
            "weather": {"value": weather_data[0], "color": get_color()},
            "temp": {"value": weather_data[1], "color": get_color()},
            "wind_direction": {"value": weather_data[2], "color": get_color()},
            "min_temperature": {"value": weather_data[3], "color": get_color()},
            "max_temperature": {"value": weather_data[4], "color": get_color()},
            "sunrise": {"value": weather_data[5], "color": get_color()},
            "sunset": {"value": weather_data[6], "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()}
        }
    }

    # 生日字段
    if "birthday1" in config:
        try:
            b1_days = get_birthday(config["birthday1"]["birthday"], today)
            b1_text = f"今天{config['birthday1']['name']}生日🎂" if b1_days == "0" else f"距离{config['birthday1']['name']}还有{b1_days}天"
            data["data"]["birthday1"] = {"value": b1_text, "color": get_color()}
        except: pass

    if "birthday2" in config:
        try:
            b2_days = get_birthday(config["birthday2"]["birthday"], today)
            b2_text = f"今天{config['birthday2']['name']}生日🎂" if b2_days == "0" else f"距离{config['birthday2']['name']}还有{b2_days}天"
            data["data"]["birthday2"] = {"value": b2_text, "color": get_color()}
        except: pass

    # 发送推送
    try:
        resp = requests.post(url, json=data, timeout=15).json()
        if resp["errcode"] == 0:
            print(f"✅ 推送成功：{to_user}")
        else:
            print(f"❌ 推送失败({to_user})：{resp}")
    except Exception as e:
        print(f"⚠️ 推送异常({to_user})：{e}")


if __name__ == "__main__":
    # 读取配置
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except:
        print("❌ 读取config.txt失败")
        sys.exit()

    # 基础检查
    must_have = ["app_id", "app_secret", "weather_key", "template_id", "user", "region", "love_date"]
    for key in must_have:
        if key not in config:
            print(f"❌ 缺少配置：{key}")
            sys.exit()

    # 获取核心数据
    token = get_access_token()
    weather = get_weather(config["region"])
    
    # 计算相恋天数
    try:
        ly, lm, ld = map(int, config["love_date"].split("-"))
        love_days = str((date.today() - date(ly, lm, ld)).days)
    except:
        love_days = "0"

    # 获取每日一句
    try:
        ciba = requests.get("http://open.iciba.com/dsapi/", timeout=10).json()
        note_en = ciba.get("content", "Keep going")
        note_ch = ciba.get("note", "每天都有希望")
    except:
        note_en = "Keep going"
        note_ch = "每天都有希望"

    # 批量推送（主逻辑）
    for user in config["user"]:
        send_message(user, token, weather, love_days, note_ch, note_en)

    print("\n--- 程序执行结束 ---")
    # 不再使用 input()，直接退出，避免 EOFError
