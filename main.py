import random
from time import localtime
import requests
from datetime import date
from zhdate import ZhDate
import sys
import os

def get_color():
    """生成随机颜色"""
    return "#" + "%06x" % random.randint(0, 0xFFFFFF)

def get_access_token():
    """获取微信token"""
    try:
        app_id = config["app_id"]
        app_secret = config["app_secret"]
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
        return requests.get(url, timeout=10).json()["access_token"]
    except:
        print("❌ 获取access_token失败")
        sys.exit(1)

def get_weather(region):
    """
    ✅ 天气/气温/风向 保持你现在正确的状态
    ✅ 日出日落 100% 精准北京时间（临沂真实时间）
    """
    city_code = "101120901"
    url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    
    weather = "晴"
    temp = "20℃"
    wind_dir = "南风"
    min_temp = "15℃"
    max_temp = "28℃"
    sunrise = "05:45"
    sunset = "18:32"

    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        
        if data.get("status") == 200:
            today_forecast = data["data"]["forecast"][0]
            weather = today_forecast.get("type", "晴")
            temp = data["data"].get("wendu", "20") + "℃"
            wind_dir = today_forecast.get("fx", "南风")
            
            low_temp = today_forecast.get("low", "15℃").replace("低温 ", "")
            high_temp = today_forecast.get("high", "28℃").replace("高温 ", "")
            min_temp = low_temp
            max_temp = high_temp

        # 精准日出日落（北京时间）
        try:
            from datetime import datetime, timedelta
            resp = requests.get("https://api.sunrise-sunset.org/json?lat=35.0519&lng=118.3471&date=today&formatted=0", timeout=5)
            sun_data = resp.json()
            if sun_data["status"] == "OK":
                rise_utc = datetime.fromisoformat(sun_data["results"]["sunrise"].replace("Z", ""))
                set_utc = datetime.fromisoformat(sun_data["results"]["sunset"].replace("Z", ""))
                rise_cn = rise_utc + timedelta(hours=8)
                set_cn = set_utc + timedelta(hours=8)
                sunrise = rise_cn.strftime("%H:%M")
                sunset = set_cn.strftime("%H:%M")
        except:
            pass

    except Exception as e:
        print(f"⚠️ 天气接口异常：{e}")
    
    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset

def get_birthday(birthday_str, year, today):
    """计算生日倒计时"""
    try:
        if birthday_str.startswith("r"):
            _, m, d = birthday_str.split("-")
            lunar = ZhDate(year, int(m), int(d)).to_datetime().date()
            birthday = date(year, lunar.month, lunar.day)
        else:
            _, m, d = birthday_str.split("-")
            birthday = date(year, int(m), int(d))

        if today > birthday:
            birthday = date(year + 1, birthday.month, birthday.day)
        return "0" if today == birthday else str((birthday - today).days)
    except:
        return "未知"

def get_ciba():
    """获取每日金句"""
    try:
        res = requests.get("http://open.iciba.com/dsapi/", timeout=8).json()
        return res["note"], res["content"]
    except:
        return "每天都有新的希望", "Keep going"

# ========================
# 🔥 双字段拆分长句：返回两句，分别对应两个模板字段
# ========================
def get_zaoan():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/zaoan/index?key={API_KEY}"
    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        if data.get("code") == 200:
            content = data["result"]["content"]
            # 按20字拆分，保证每句都在微信单行长度内
            line1 = content[:20]
            line2 = content[20:]
            return line1, line2
    except:
        pass
    return "早安，新的一天也要元气满满～", ""

def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch1, note_ch2, note_en):
    """推送消息"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    week = week_list[today.weekday()]
    date_str = f"{today} {week}"

    # 在一起天数
    try:
        love = date(*map(int, config["love_date"].split("-")))
        love_days = str((today - love).days)
    except:
        love_days = "未知"

    # 推送数据
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": "临沂市", "color": get_color()},
            "region": {"value": "临沂市", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            # 双字段拆分长句，分别对应模板的两个「每日一句」字段
            "note_ch": {"value": note_ch1, "color": get_color()},
            "note_ch2": {"value":note_ch2, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
        }
    }

    # 修复重复「距离」，统一格式
    if "birthday1" in config:
        b1 = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday1"] = {"value": f"{config['birthday1']['name']}生日还有{b1}天" , "color": get_color()}
    if "birthday2" in config:
        b2 = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday2"] = {"value": f"{config['birthday2']['name']}生日还有{b2}天" , "color": get_color()}

    # 发送请求
    try:
        res = requests.post(url, json=data, timeout=10).json()
        if res["errcode"] == 0:
            print(f"✅ 推送成功！")
            print(f"📊 数据预览 -> 城市：临沂市 | 天气：{weather} | 气温：{temp} | 风向：{wind_dir}")
        else:
            print(f"❌ 推送失败：{res.get('errmsg')}")
    except Exception as e:
        print(f"❌ 网络异常：{e}")

if __name__ == "__main__":
    # 读取配置
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = eval(f.read())
    except:
        print("❌ 读取config.txt失败")
        sys.exit()

    # 核心流程
    token = get_access_token()
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])
    # 接收拆分后的两句早安心语
    note_ch1,note_ch2=get_zaoan()
    note_en = "Good morning"

    # 循环推送（过滤空ID）
    for user in config["user"]:
        if user and user.strip():
            send_message(user, token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch1, note_ch2, note_en)
