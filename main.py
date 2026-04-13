import random
from time import localtime, sleep
import requests
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os

# 适配Linux/macOS的暂停函数（替代Windows的pause）
def system_pause():
    if os.name == 'nt':  # Windows系统
        os.system("pause")
    else:  # Linux/macOS系统
        input("\n按回车键退出...")

def get_color():
    """生成随机16进制颜色码"""
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)

def get_access_token():
    """获取微信公众号access_token（增加重试+超时优化）"""
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = (
        "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
        .format(app_id, app_secret)
    )
    # 增加重试机制，最多重试3次
    max_retry = 3
    for i in range(max_retry):
        try:
            # 延长超时时间到20秒，避免网络波动
            response = requests.get(post_url, timeout=20)
            response.raise_for_status()
            access_token = response.json()['access_token']
            return access_token
        except KeyError:
            print("获取access_token失败，请检查app_id和app_secret是否正确")
            system_pause()
            sys.exit(1)
        except Exception as e:
            print(f"第{i+1}次获取access_token失败：{str(e)}")
            if i < max_retry - 1:
                print("2秒后重试...")
                sleep(2)
            else:
                print("重试次数已用完，程序退出")
                system_pause()
                sys.exit(1)

def get_weather(region):
    """修复：和风天气最新接口 + 精准温度/风向/日出日落"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]

    # 【修复】全部使用官方最新 devapi，老接口会数据错乱！
    region_url = f"https://devapi.qweather.com/v7/city/lookup?location={region}&key={key}"

    # 1. 获取城市ID
    try:
        response = requests.get(region_url, headers=headers, timeout=10)
        response.raise_for_status()
        region_data = response.json()

        if region_data.get("code") != "200" or not region_data.get("location"):
            print("地区查询失败，使用默认天气")
            return "晴", "20℃", "东风", "15℃", "28℃", "06:30", "18:30"

        location_id = region_data["location"][0]["id"]

    except Exception as e:
        print(f"获取地区异常：{str(e)}")
        return "晴", "20℃", "东风", "15℃", "28℃", "06:30", "18:30"

    # 2. 实时天气
    now_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
    # 3. 今日高低温
    daily_url = f"https://devapi.qweather.com/v7/weather/3d?location={location_id}&key={key}"
    # 4. 日出日落
    astro_url = f"https://devapi.qweather.com/v7/astronomy/sun?location={location_id}&date={date.today().strftime('%Y-%m-%d')}&key={key}"

    weather = "晴"
    temp = "20℃"
    wind_dir = "东风"
    min_temp = "15℃"
    max_temp = "28℃"
    sunrise = "06:30"
    sunset = "18:30"

    # 实时天气（精准风向）
    try:
        now_data = requests.get(now_url, headers=headers, timeout=10).json()
        if now_data["code"] == "200":
            weather = now_data["now"]["text"]
            temp = f"{now_data['now']['temp']}℃"
            wind_dir = now_data["now"]["windDir"]  # 【修复】正确风向字段
    except:
        pass

    # 高低温（修复）
    try:
        daily_data = requests.get(daily_url, headers=headers, timeout=10).json()
        if daily_data["code"] == "200":
            min_temp = f"{daily_data['daily'][0]['tempMin']}℃"
            max_temp = f"{daily_data['daily'][0]['tempMax']}℃"
    except:
        pass

    # 日出日落
    try:
        astro_data = requests.get(astro_url, headers=headers, timeout=10).json()
        if astro_data["code"] == "200":
            rise_str = astro_data["sunrise"][11:16]
            set_str = astro_data["sunset"][11:16]
            sunrise = rise_str
            sunset = set_str
    except:
        pass

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
        return "未知"

def get_ciba():
    """每日一句"""
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    try:
        ciba_data = requests.get(url, headers=headers, timeout=10).json()
        note_en = ciba_data.get("content", "Keep going")
        note_ch = ciba_data.get("note", "每天都有新的希望")
    except:
        note_en = "Keep going"
        note_ch = "每天都有新的希望"
    return note_ch, note_en

def send_message(to_user, access_token, region, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    """推送模板消息（字段完全匹配你的模板）"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    # 相恋天数
    try:
        love_year, love_month, love_day = map(int, config["love_date"].split("-"))
        love_date = date(love_year, love_month, love_day)
        love_days = str((today - love_date).days)
    except:
        love_days = "0"

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
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

    # 生日2（已修复缺失的 = 号）
    try:
        if "birthday2" in config:
            b2_days = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
            b2_text = f"今天{config['birthday2']['name']}生日🎂！" if b2_days == "0" else f"距离{config['birthday2']['name']}生日还有{b2_days}天"
            data["data"]["birthday2"] = {"value": b2_text, "color": get_color()}
    except:
        pass

    try:
        resp = requests.post(url, json=data, timeout=20)
        if resp.json()["errcode"] == 0:
            print(f"✅ 推送成功：{to_user}")
        else:
            print(f"❌ 推送失败：{resp.json()}")
    except Exception as e:
        print(f"⚠️ 推送异常：{e}")

if __name__ == "__main__":
    # 读取配置
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except:
        print("配置文件错误！")
        system_pause()
        sys.exit()

    # 必备配置检查
    must = ["app_id", "app_secret", "weather_key", "template_id", "user", "region", "love_date"]
    for m in must:
        if m not in config:
            print(f"缺失配置：{m}")
            system_pause()
            sys.exit()

    access_token = get_access_token()
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])
    note_ch, note_en = get_ciba()

    # 批量推送
    for user in config["user"]:
        send_message(user, access_token, config["region"], weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)
