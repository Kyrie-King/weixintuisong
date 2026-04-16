import random
from time import localtime, sleep
import requests
from datetime import date
from zhdate import ZhDate
import sys
import os

def get_color():
    return "#000000"

# 🔥 修复access_token获取
def get_access_token():
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    for i in range(3):
        try:
            res = requests.get(url, timeout=20)
            data = res.json()
            if "access_token" in data:
                return data["access_token"]
            else:
                print(f"⚠️ 获取token重试 {i+1}/3: {data}")
        except Exception as e:
            print(f"⚠️ 获取token重试 {i+1}/3: {e}")
            sleep(2)
    print("❌ 3次重试后获取access_token失败")
    sys.exit(1)

def get_weather(region):
    city_code = "101120901"
    url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    
    real_temp = "19"
    min_temp = "13"
    max_temp = "22"
    weather = "小雨"
    wind_dir = "东南风"
    sunrise = "05:33"
    sunset = "18:39"

    for i in range(3):
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            if data.get("status") == 200:
                today_forecast = data["data"]["forecast"][0]
                real_temp = data["data"]["wendu"]
                weather = today_forecast.get("type", "小雨")
                wind_dir = today_forecast.get("fx", "东南风")
                min_temp = today_forecast.get("low", "13").replace("低温 ", "").replace("℃", "")
                max_temp = today_forecast.get("high", "22").replace("高温 ", "").replace("℃", "")
                sunrise = today_forecast.get("sunrise", "05:33")
                sunset = today_forecast.get("sunset", "18:39")
                return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset
        except Exception as e:
            print(f"⚠️ 天气接口重试 {i+1}/3: {e}")
            sleep(1)
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
        return str((birthday - today).days)
    except:
        return "未知"

# 🔥 土味情话：拆成 4 个变量？不，你要两段拆成两个变量（上、下）
# 自动按长度拆分，保证每段不超限
def get_love_words():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/saylove/index?key={API_KEY}"
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        if data.get("code") == 200 and "content" in data.get("result", {}):
            content = data["result"]["content"]
            
            # 按语义拆分，不超过微信限制
            if len(content) <= 18:
                return content, "", "", ""
            elif len(content) <= 36:
                return content[:18], content[18:], "", ""
            elif len(content) <= 54:
                return content[:18], content[18:36], content[36:], ""
            else:
                # 超长自动4段拆分，每段约18字
                return content[:18], content[18:36], content[36:54], content[54:]
    except:
        pass
    
    # 兜底情话
    return "遇见你之前，", "我的世界是单色的；", "遇见你之后，", "世界变得五彩斑斓。"

# 🔥 脑筋急转弯：题目拆成2个变量 + 答案单独1个
# 总共4个变量：riddle_q1, riddle_q2, riddle_ans1, riddle_ans2
def get_riddle():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/naowan/index?key={API_KEY}&num=1"
    
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        
        if data.get("code") == 200:
            result = data.get("result", {})
            riddle_list = result.get("list", [])
            if isinstance(riddle_list, list) and len(riddle_list) > 0:
                item = riddle_list[0]
                question = item.get("quest", "未知问题")
                answer = item.get("result", "未知答案")
                
                # 🔴 题目自动拆成2段，每段都不超限
                q1 = question[:18] if len(question) > 18 else question
                q2 = question[18:] if len(question) > 18 else ""
                
                # 答案也拆成2段（防超长）
                a1 = answer[:18] if len(answer) > 18 else answer
                a2 = answer[18:] if len(answer) > 18 else ""
                
                return q1, q2, a1, a2
    except Exception as e:
        print(f"⚠️ 脑筋急转弯接口异常: {e}")
    
    # 兜底题库
    riddle_pool = [
        ("什么东西越洗越脏？", "水"),
        ("什么东西越热越爱出来？", "汗"),
        ("什么东西有脚却不能走路？", "桌子"),
        ("什么东西打破了才能用？", "鸡蛋"),
        ("警察发现钱包却不上交？", "钱包是警察自己掉的")
    ]
    q, a = random.choice(riddle_pool)
    q1 = q[:18]
    q2 = q[18:]
    a1 = a[:18]
    a2 = a[18:]
    return q1, q2, a1, a2

def send_message(to_user, access_token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset,
               love1, love2, love3, love4, riddle_q1, riddle_q2, riddle_ans1, riddle_ans2):
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
            # 🔥 土味情话4个变量
            "love1": {"value": love1, "color": get_color()},
            "love2": {"value": love2, "color": get_color()},
            "love3": {"value": love3, "color": get_color()},
            "love4": {"value": love4, "color": get_color()},
            # 🔥 脑筋急转弯4个变量
            "riddle_q1": {"value": riddle_q1, "color": get_color()},
            "riddle_q2": {"value": riddle_q2, "color": get_color()},
            "riddle_ans1": {"value": riddle_ans1, "color": get_color()},
            "riddle_ans2": {"value": riddle_ans2, "color": get_color()},
        }
    }

    for i in range(3):
        try:
            res = requests.post(send_url, json=data, timeout=15)
            if res.status_code == 200:
                res_data = res.json()
                if res_data["errcode"] == 0:
                    print(f"✅ 推送成功！")
                    return
        except Exception as e:
            print(f"⚠️ 推送重试 {i+1}/3: {e}")
            sleep(1)
    print("❌ 推送失败")
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
    love1, love2, love3, love4 = get_love_words()
    riddle_q1, riddle_q2, riddle_ans1, riddle_ans2 = get_riddle()

    openids = config["user"] if isinstance(config["user"], list) else [config["user"]]
    for user in openids:
        if user.strip():
            send_message(user, token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset,
                         love1, love2, love3, love4, riddle_q1, riddle_q2, riddle_ans1, riddle_ans2)
