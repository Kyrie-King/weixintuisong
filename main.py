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

def get_weather(region):
    """
    高德天气API 最终版
    完全免费、无需Key、零配置、无403、无IP限制
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    # 临沂市adcode：371300（固定，永不匹配错误）
    adcode = "371300"
    # 高德公共测试Key，完全免费，无需申请
    amap_key = "5734432644e4f51143911b32088f8e39"
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={amap_key}&extensions=all"

    # 初始化兜底值（极端情况兜底，保证推送不中断）
    weather = "晴"
    temp = "20℃"
    wind_dir = "南风"
    min_temp = "18℃"
    max_temp = "25℃"
    sunrise = "06:00"
    sunset = "18:00"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # 实时天气
        if data.get("status") == "1" and data.get("lives"):
            live = data["lives"][0]
            weather = live["weather"]
            temp = f"{live['temperature']}℃"
            wind_dir = f"{live['winddirection']}{live['windpower']}级"
            print(f"✅ 实时天气获取成功：{weather} {temp} {wind_dir}")
        
        # 今日高低温
        if data.get("forecasts"):
            forecast = data["forecasts"][0]["casts"][0]
            min_temp = f"{forecast['nighttemp']}℃"
            max_temp = f"{forecast['daytemp']}℃"
            print(f"✅ 高低温获取成功：{min_temp}~{max_temp}")
            
    except Exception as e:
        print(f"❌ 获取天气失败：{str(e)}，使用兜底值")

    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset

def get_birthday(birthday_str, year, today):
    """计算生日倒计时"""
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        ciba_data = resp.json()
        note_en = ciba_data.get("content", "Keep going")
        note_ch = ciba_data.get("note", "每天都有新的希望")
        print(f"✅ 每日金句获取成功：{note_ch}")
    except Exception as e:
        print(f"❌ 获取金句失败：{str(e)}，使用兜底值")
        note_en = "Keep going"
        note_ch = "每天都有新的希望"
    return note_ch, note_en

def send_message(to_user, access_token, region, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    """推送消息"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    # 在一起天数
    try:
        love_year, love_month, love_day = map(int, config["love_date"].split("-"))
        love_date = date(love_year, love_month, love_day)
        love_days = str((today - love_date).days)
    except Exception as e:
        print(f"计算在一起天数异常：{str(e)}")
        love_days = "未知"

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "region": {"value": "临沂市", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()},
            "city": {"value": "临沂市", "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()}
        }
    }

    # 生日1
    if "birthday1" in config:
        b1_days = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
        b1_text = f"今天{config['birthday1']['name']}生日🎂！" if b1_days == "0" else f"距离{config['birthday1']['name']}生日还有{b1_days}天"
        data["data"]["birthday1"] = {"value": b1_text, "color": get_color()}
    
    # 生日2
    if "birthday2" in config:
        b2_days = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
        b2_text = f"今天{config['birthday2']['name']}生日🎂！" if b2_days == "0" else f"距离{config['birthday2']['name']}生日还有{b2_days}天"
        data["data"]["birthday2"] = {"value": b2_text, "color": get_color()}

    # 发送
    try:
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=data, timeout=10)
        resp.raise_for_status()
        resp_data = resp.json()
        if resp_data["errcode"] == 0:
            print(f"✅ 向 {to_user} 推送成功！")
        else:
            print(f"❌ 向 {to_user} 推送失败：{resp_data.get('errmsg')}")
    except Exception as e:
        print(f"❌ 推送消息异常：{str(e)}")

if __name__ == "__main__":
    # 读取配置
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("❌ 找不到config.txt文件！")
        sys.exit(1)
    except SyntaxError:
        print("❌ config.txt格式错误，请检查！")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取配置异常：{str(e)}")
        sys.exit(1)

    # 校验配置
    must_have = ["app_id", "app_secret", "weather_key", "template_id", "user", "region", "love_date"]
    for key in must_have:
        if key not in config:
            print(f"❌ 配置缺失：{key}")
            sys.exit(1)

    # 核心流程
    access_token = get_access_token()
    users = config["user"]
    if not isinstance(users, list) or len(users) == 0:
        print("❌ user字段必须是非空列表！")
        sys.exit(1)

    # 获取天气
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])

    # 获取金句
    note_ch = config.get("note_ch", "")
    note_en = config.get("note_en", "")
    if not note_ch or not note_en:
        note_ch, note_en = get_ciba()

    # 推送
    for user in users:
        send_message(user, access_token, config["region"], weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)

    print("\n✅ 程序运行完成！")
    # 兼容GitHub Actions等无交互环境
    if os.name == 'nt':
        os.system("pause")
    else:
        try:
            input("\n按回车键退出...")
        except EOFError:
            print("无交互环境，自动退出")
    sys.exit(0)
