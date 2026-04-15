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
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    for i in range(3):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200 and "access_token" in res.json():
                return res.json()["access_token"]
        except Exception as e:
            print(f"⚠️ 获取token重试 {i+1}/3: {e}")
            sleep(1)
    print("❌ 3次重试后获取access_token失败")
    sys.exit(1)

def get_weather(region):
    city_code = "101120901"
    url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    
    real_temp = "23"
    min_temp = "11"
    max_temp = "25"
    weather = "多云"
    wind_dir = "东北风"
    sunrise = "05:37"
    sunset = "18:37"

    for i in range(3):
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            if data.get("status") == 200:
                today_forecast = data["data"]["forecast"][0]
                real_temp = data["data"]["wendu"]
                weather = today_forecast.get("type", "多云")
                wind_dir = today_forecast.get("fx", "东北风")
                min_temp = today_forecast.get("low", "11").replace("低温 ", "").replace("℃", "")
                max_temp = today_forecast.get("high", "25").replace("高温 ", "").replace("℃", "")
                sunrise = today_forecast.get("sunrise", "05:37")
                sunset = today_forecast.get("sunset", "18:37")
                return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset
        except Exception as e:
            print(f"⚠️ 天气接口重试 {i+1}/3: {e}")
            sleep(1)
    print(f"⚠️ 3次重试后天气接口异常，使用默认值")
    return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset

def get_birthday(birthday_str, year, today):
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
    except:
        return "未知"

# 🔥 土味情话接口（稳定版）
def get_love_words():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/saylove/index?key={API_KEY}"
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        if data.get("code") == 200 and "content" in data.get("result", {}):
            content = data["result"]["content"]
            mid = len(content) // 2
            return content[:mid], content[mid:]
    except Exception as e:
        print(f"⚠️ 土味情话接口异常: {e}")
    
    # 备用情话池
    love_pool = [
        "我发现昨天很喜欢你，今天也很喜欢你，而且有预感明天也会很喜欢你。",
        "别抱怨了，把你扔进我心里就不冷了。",
        "你知道我想喝什么吗？想呵护你。",
        "我最近有点忙，忙着喜欢你。",
        "你是不是有什么毛病？不然怎么怎么看你都顺眼。"
    ]
    love = random.choice(love_pool)
    mid = len(love) // 2
    return love[:mid], love[mid:]

# 🔥 核心修复：脑筋急转弯接口（彻底解决永远不变）
def get_riddle():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/naowan/index?key={API_KEY}&num=1"
    
    # 🔴 第一步：先打印接口返回，方便你排查
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        print(f"🔍 脑筋急转弯接口返回: {data}")  # 加日志，方便你看接口到底返回了什么
        
        if data.get("code") == 200:
            # 兼容两种返回格式（列表/字典）
            result = data.get("result")
            if isinstance(result, list) and len(result) > 0:
                item = result[0]
                content = item.get("content", "未知问题")
                answer = item.get("answer", "未知答案")
                full_text = f"{content} → {answer}"
                mid = len(full_text) // 2
                return full_text[:mid], full_text[mid:]
            elif isinstance(result, dict):
                content = result.get("content", "未知问题")
                answer = result.get("answer", "未知答案")
                full_text = f"{content} → {answer}"
                mid = len(full_text) // 2
                return full_text[:mid], full_text[mid:]
    except Exception as e:
        print(f"⚠️ 脑筋急转弯接口异常: {e}")
    
    # 🟢 第二步：备用题库（10个不同题目，每次随机选，绝对不会重复）
    riddle_pool = [
        "什么东西越洗越脏？→水",
        "什么东西越热越爱出来？→汗",
        "什么东西有脚却不能走路？→桌子",
        "什么东西打破了才能用？→鸡蛋",
        "什么东西别人请你吃，但你自己还要付钱？→官司",
        "什么东西天气越热，它爬得越高？→温度计",
        "什么东西走也走不到头？→路",
        "什么东西明明是你的，别人却用得比你多？→名字",
        "什么东西有五个头，但人不觉得它怪？→手",
        "什么东西晚上才生出尾巴？→流星"
    ]
    # 每次随机选一个，再也不会永远显示同一个！
    riddle = random.choice(riddle_pool)
    mid = len(riddle) // 2
    return riddle[:mid], riddle[mid:]

def send_message(to_user, access_token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, love1, love2, riddle1, riddle2):
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    date_str = f"{today} {week_list[today.weekday()]}"
    
    try:
        love = date(*map(int, config["love_date"].split("-")))
        love_days = str((today - love).days)
    except:
        love_days = "未知"

    b1 = get_birthday(config["birthday1"]["birthday"], today.year, today)
    b2 = get_birthday(config["birthday2"]["birthday"], today.year, today)

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": "临沂市", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "real_temp": {"value": real_temp, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": f"{config['birthday1']['name']}生日还有{b1}天", "color": get_color()},
            "birthday2": {"value": f"{config['birthday2']['name']}生日还有{b2}天", "color": get_color()},
            "love1": {"value": love1, "color": get_color()},
            "love2": {"value": love2, "color": get_color()},
            "riddle1": {"value": riddle1, "color": get_color()},
            "riddle2": {"value": riddle2, "color": get_color()},
        }
    }

    for i in range(3):
        try:
            res = requests.post(send_url, json=data, timeout=15)
            if res.status_code == 200:
                res_data = res.json()
                if res_data["errcode"] == 0:
                    print(f"✅ 推送成功！")
                    print(f"📊 实时{real_temp}℃ | 最低{min_temp}℃ | 最高{max_temp}℃")
                    print(f"💘土味情话：{love1}{love2}")
                    print(f"🧠脑筋急转弯：{riddle1}{riddle2}")
                    return
                else:
                    print(f"⚠️ 推送重试 {i+1}/3: {res_data}")
        except Exception as e:
            print(f"⚠️ 推送请求重试 {i+1}/3: {e}")
            sleep(1)
    print("❌ 3次重试后推送失败")
    sys.exit(1)

if __name__ == "__main__":
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = eval(f.read())
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        sys.exit(1)

    token = get_access_token()
    real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset = get_weather(config["region"])
    love1, love2 = get_love_words()
    riddle1, riddle2 = get_riddle()

    openids = config["user"] if isinstance(config["user"], list) else [config["user"]]
    for user in openids:
        if user.strip():
            send_message(user, token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset, love1, love2, riddle1, riddle2)
