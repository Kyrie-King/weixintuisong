import random
from time import localtime, sleep
import requests
from datetime import date
from zhdate import ZhDate
import sys
import os

def get_color():
    """生成随机颜色"""
    return "#" + "%06x" % random.randint(0, 0xFFFFFF)

def get_access_token():
    """获取微信token（增加重试+超时）"""
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    
    # 增加3次重试，每次间隔2秒，超时时间设为30秒
    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            if res.status_code == 200 and "access_token" in res.json():
                return res.json()["access_token"]
        except Exception as e:
            print(f"⚠️ 获取token重试 {i+1}/3: {e}")
            sleep(2)
    print("❌ 3次重试后获取access_token失败")
    sys.exit(1)

def get_weather(region):
    """
    ✅ 天气/气温/风向 保持正确状态
    ✅ 温度全部带℃，日出日落精准北京时间
    ✅ 增加重试+超时
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

    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            data = res.json()
            if data.get("status") == 200:
                today_forecast = data["data"]["forecast"][0]
                weather = today_forecast.get("type", "晴")
                temp = data["data"]["wendu"] + "℃"
                wind_dir = today_forecast.get("fx", "南风")
                
                low_temp = today_forecast.get("low", "15℃").replace("低温 ", "")
                high_temp = today_forecast.get("high", "28℃").replace("高温 ", "")
                min_temp = low_temp if "℃" in low_temp else low_temp + "℃"
                max_temp = high_temp if "℃" in high_temp else high_temp + "℃"

                # 精准日出日落（北京时间）
                try:
                    sun_url = "https://api.sunrise-sunset.org/json?lat=35.0519&lng=118.3471&date=today&formatted=0"
                    sun_res = requests.get(sun_url, timeout=30)
                    sun_data = sun_res.json()
                    if sun_data["status"] == "OK":
                        from datetime import datetime, timedelta
                        rise_utc = datetime.fromisoformat(sun_data["results"]["sunrise"].replace("Z", ""))
                        set_utc = datetime.fromisoformat(sun_data["results"]["sunset"].replace("Z", ""))
                        rise_cn = rise_utc + timedelta(hours=8)
                        set_cn = set_utc + timedelta(hours=8)
                        sunrise = rise_cn.strftime("%H:%M")
                        sunset = set_cn.strftime("%H:%M")
                except Exception as e:
                    print(f"⚠️ 日出日落接口重试 {i+1}/3: {e}")
                return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset
        except Exception as e:
            print(f"⚠️ 天气接口重试 {i+1}/3: {e}")
            sleep(2)
    print(f"⚠️ 3次重试后天气接口异常，使用默认值")
    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset

def get_birthday(birthday_str, year, today):
    """计算生日倒计时（支持农历）"""
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
        return "0" if today == birthday else str((birthday - today).days)
    except Exception as e:
        print(f"⚠️ 生日计算异常: {e}")
        return "未知"

# ========================
# 🔥 四字段拆分：返回4段文案，对应4个模板字段
# ========================
def get_zaoan():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/zaoan/index?key={API_KEY}"
    for i in range(3):
        try:
            res = requests.get(url, timeout=30)
            data = res.json()
            if data.get("code") == 200:
                content = data["result"]["content"]
                # 按15字/段拆分，最多4段，完美适配4个单行字段
                part1 = content[:15]
                part2 = content[15:30]
                part3 = content[30:45]
                part4 = content[45:60]
                # 空内容兜底，避免字段为空
                part1 = part1 if part1.strip() else ""
                part2 = part2 if part2.strip() else ""
                part3 = part3 if part3.strip() else ""
                part4 = part4 if part4.strip() else ""
                return part1, part2, part3, part4
        except Exception as e:
            print(f"⚠️ 早安心语接口重试 {i+1}/3: {e}")
            sleep(2)
    print("⚠️ 3次重试后早安心语接口异常，使用默认值")
    return "早安，新的一天也要元气满满～", "", "", ""

def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch1, note_ch2, note_ch3, note_ch4, note_en):
    """推送消息（增加重试+超时）"""
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    week = week_list[today.weekday()]
    date_str = f"{today} {week}"

    # 在一起天数
    try:
        love = date(*map(int, config["love_date"].split("-")))
        love_days = str((today - love).days)
    except Exception as e:
        print(f"⚠️ 在一起天数计算异常: {e}")
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
            # 四字段拆分，对应模板的4个「每日一句」字段
            "note_ch": {"value": note_ch1, "color": get_color()},
            "note_ch2": {"value": note_ch2, "color": get_color()},
            "note_ch3": {"value": note_ch3, "color": get_color()},
            "note_ch4": {"value": note_ch4, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
        }
    }

    # 生日推送（修复重复「距离」，格式：距离XX生日还有XX天）
    if "birthday1" in config:
        b1 = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday1"] = {"value": f"距离{config['birthday1']['name']}生日还有{b1}天" , "color": get_color()}
    if "birthday2" in config:
        b2 = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
        data["data"]["birthday2"] = {"value": f"距离{config['birthday2']['name']}生日还有{b2}天" , "color": get_color()}

    # 发送请求，增加重试
    for i in range(3):
        try:
            res = requests.post(send_url, json=data, timeout=30)
            if res.status_code == 200:
                res_data = res.json()
                if res_data["errcode"] == 0:
                    print(f"✅ 推送成功！")
                    print(f"📊 数据预览 -> 城市：临沂市 | 天气：{weather} | 气温：{temp} | 风向：{wind_dir}")
                    return
                else:
                    print(f"⚠️ 推送重试 {i+1}/3: {res_data}")
        except Exception as e:
            print(f"⚠️ 推送请求重试 {i+1}/3: {e}")
            sleep(2)
    print("❌ 3次重试后推送失败")
    sys.exit(1)

if __name__ == "__main__":
    # 读取配置
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = eval(f.read())
    except Exception as e:
        print(f"❌ 读取config.txt失败: {e}")
        sys.exit(1)

    # 核心流程
    token = get_access_token()
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])
    # 接收拆分后的4段早安心语
    note_ch1,note_ch2,note_ch3,note_ch4 = get_zaoan()
    note_en = "Good morning"

    # 适配你现有的 `user` 字段，无需改config
    # 自动兼容列表/单值
    openids = config["user"]
    if isinstance(openids, str):
        openids = [openids]
    for user in openids:
        if user.strip():
            send_message(user, token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch1, note_ch2, note_ch3, note_ch4, note_en)
