import random
from time import localtime, sleep
import requests
from datetime import date
from zhdate import ZhDate
import sys
import os

def get_color():
    return "#000000"

def get_access_token():
    """获取微信接口调用凭证"""
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            res.raise_for_status()  # 抛出HTTP异常
            result = res.json()
            if "access_token" in result:
                return result["access_token"]
            else:
                print(f"获取token失败: {result}")
        except Exception as e:
            print(f"获取token异常({i+1}/3): {e}")
            sleep(2)
    sys.exit("❌ 多次获取access_token失败，退出程序")

def get_weather(region):
    """获取天气数据（替换为和风天气接口，更稳定）"""
    # 和风天气API配置（需要在config.txt里配置weather_key）
    weather_key = config.get("weather_key", "")
    city_code = config.get("city_code", "101120901")  # 临沂的城市编码
    url = f"https://devapi.qweather.com/v7/weather/now?location={city_code}&key={weather_key}"
    # 预报接口（获取最高/最低温、日出日落）
    forecast_url = f"https://devapi.qweather.com/v7/weather/3d?location={city_code}&key={weather_key}"
    
    # 初始化默认值（确保字段都有值）
    real_temp = "未知"
    min_temp = "未知"
    max_temp = "未知"
    weather = "未知"
    wind_dir = "未知"
    sunrise = "未知"
    sunset = "未知"

    # 1. 获取实时天气
    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        now_data = res.json()
        if now_data.get("code") == "200":
            real_temp = now_data["now"]["temp"]  # 实时气温
            weather = now_data["now"]["text"]    # 天气状况
            wind_dir = now_data["now"]["windDir"]  # 风向
    except Exception as e:
        print(f"获取实时天气失败: {e}")

    # 2. 获取预报数据（最高/最低温、日出日落）
    try:
        res = requests.get(forecast_url, timeout=30)
        res.raise_for_status()
        forecast_data = res.json()
        if forecast_data.get("code") == "200":
            today_forecast = forecast_data["daily"][0]
            min_temp = today_forecast["tempMin"]  # 最低温
            max_temp = today_forecast["tempMax"]  # 最高温
            sunrise = today_forecast["sunrise"]   # 日出
            sunset = today_forecast["sunset"]     # 日落
    except Exception as e:
        print(f"获取预报天气失败: {e}")

    return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset

def get_birthday(birthday_str, year, today):
    """计算生日剩余天数（支持农历，前缀r）"""
    try:
        if birthday_str.startswith("r"):
            _, m, d = birthday_str.split("-")
            lunar = ZhDate(year, int(m), int(d)).to_datetime().date()
            birthday = date(year, lunar.month, lunar.day)
        else:
            m, d = birthday_str.split("-")
            birthday = date(year, int(m), int(d))
        if today > birthday:
            birthday = date(year + 1, birthday.month, birthday.day)
        return str((birthday - today).days)
    except Exception as e:
        print(f"计算生日失败: {e}")
        return "未知"

def get_zaoan():
    """获取早安文案（天行数据）"""
    API_KEY = config.get("tianapi_key", "769e688a2a945817a2b8140e853b78eb")
    url = f"https://apis.tianapi.com/zaoan/index?key={API_KEY}"
    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            data = res.json()
            if data.get("code") == 200:
                content = data["result"]["content"]
                # 拆分文案（避免过长）
                content = content.ljust(64)  # 补空格确保长度足够
                return content[:16], content[16:32], content[32:48], content[48:64]
        except Exception as e:
            print(f"获取早安文案异常({i+1}/3): {e}")
            sleep(2)
    return "早安呀～", "今天也要开心✨", "爱你哟❤️", "记得按时吃饭～"

def send_message(to_user, access_token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, note_ch1, note_ch2, note_ch3, note_ch4):
    """发送微信模板消息"""
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    date_str = f"{today} {week_list[today.weekday()]}"
    
    # 计算恋爱天数
    try:
        love = date(*map(int, config["love_date"].split("-")))
        love_days = str((today - love).days)
    except Exception as e:
        print(f"计算恋爱天数失败: {e}")
        love_days = "未知"

    # 计算生日剩余天数
    b1 = get_birthday(config["birthday1"]["birthday"], today.year, today)
    b2 = get_birthday(config["birthday2"]["birthday"], today.year, today)

    # 修正模板字段名（匹配截图里的显示字段）
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": config.get("city_name", "临沂市"), "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "real_temp": {"value": real_temp + "℃", "color": get_color()},  # 实时气温（加单位）
            "min_temperature": {"value": min_temp + "℃", "color": get_color()},  # 最低气温
            "max_temperature": {"value": max_temp + "℃", "color": get_color()},  # 最高气温
            "wind_direction": {"value": wind_dir, "color": get_color()},  # 当前风向
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": f"{config['birthday1']['name']}生日还有{b1}天", "color": get_color()},
            "birthday2": {"value": f"{config['birthday2']['name']}生日还有{b2}天", "color": get_color()},
            "note_ch": {"value": note_ch1, "color": get_color()},
            "note_ch2": {"value": note_ch2, "color": get_color()},
            "note_ch3": {"value": note_ch3, "color": get_color()},
            "note_ch4": {"value": note_ch4, "color": get_color()},
        }
    }

    # 适配模板字段名（如果你的模板里是“当前气温”而不是“real_temp”，需要替换key）
    # 比如：如果模板字段是“当前气温”，就把data里的"real_temp"改成"current_temp"（根据你的模板调整）
    # 以下是兼容处理，根据截图字段名调整：
    template_key_map = {
        "当前气温": "real_temp",
        "最低气温": "min_temperature",
        "最高气温": "max_temperature",
        "当前风向": "wind_direction"
    }
    # 重新构造data（匹配模板字段名）
    final_data = {}
    for template_key, code_key in template_key_map.items():
        final_data[template_key] = data["data"][code_key]
    # 合并其他字段
    for key in ["date", "city", "weather", "sunrise", "sunset", "love_day", "birthday1", "birthday2", "note_ch", "note_ch2", "note_ch3", "note_ch4"]:
        final_data[key] = data["data"][key]
    data["data"] = final_data

    # 发送消息
    for i in range(3):
        try:
            res = requests.post(send_url, json=data, timeout=30)
            res.raise_for_status()
            result = res.json()
            if result["errcode"] == 0:
                print(f"✅ 向 {to_user} 推送成功！")
                return
            else:
                print(f"推送失败: {result['errmsg']}")
        except Exception as e:
            print(f"推送异常({i+1}/3): {e}")
            sleep(2)
    print(f"❌ 向 {to_user} 多次推送失败")

if __name__ == "__main__":
    # 读取配置文件
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = eval(f.read())
    except Exception as e:
        sys.exit(f"❌ 读取config.txt失败: {e}")

    # 核心流程
    try:
        token = get_access_token()
        real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset = get_weather(config.get("region", "临沂"))
        note1, note2, note3, note4 = get_zaoan()

        # 处理多个用户
        openids = config["user"] if isinstance(config["user"], list) else [config["user"]]
        for user in openids:
            send_message(user, token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, note1, note2, note3, note4)
    except Exception as e:
        print(f"程序执行异常: {e}")
        sys.exit(1)
