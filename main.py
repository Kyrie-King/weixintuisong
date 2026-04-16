import random
from time import localtime, sleep
import requests
from datetime import date
from zhdate import ZhDate
import sys

def get_color():
    return "#000000"

# 获取微信token
def get_access_token():
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    for _ in range(3):
        try:
            res = requests.get(url, timeout=20)
            data = res.json()
            if "access_token" in data:
                return data["access_token"]
        except:
            sleep(2)
    sys.exit(1)

# 天气
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
    for _ in range(3):
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
        except:
            sleep(1)
    return real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset

# 生日倒计时
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

# 土味情话 两段
def get_love_words():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/saylove/index?key={API_KEY}"
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        if data.get("code") == 200:
            txt = data["result"]["content"]
            mid = len(txt) // 2
            return txt[:mid], txt[mid:]
    except:
        pass
    return "我满眼皆是你，", "岁岁年年都是你。"

# 🔥 核心：脑筋急转弯（问题4段 + 答案2段）
def get_riddle():
    API_KEY = "769e688a2a945817a2b8140e853b78eb"
    url = f"https://apis.tianapi.com/naowan/index?key={API_KEY}&num=1"
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        if data.get("code") == 200:
            item = data["result"]["list"][0]
            question = item.get("quest", "")
            answer = item.get("result", "")

            # 问题均分4段
            def split_four(s):
                l = len(s)
                part1 = s[:l//4]
                part2 = s[l//4 : l//4*2]
                part3 = s[l//4*2 : l//4*3]
                part4 = s[l//4*3:]
                return part1, part2, part3, part4

            # 答案均分2段
            def split_two(s):
                mid = len(s) // 2
                return s[:mid], s[mid:]

            q1, q2, q3, q4 = split_four(question)
            ans1, ans2 = split_two(answer)
            return q1, q2, q3, q4, ans1, ans2
    except:
        pass

    # 兜底
    q = "什么东西只能加不能减，每个人都有"
    a = "年龄只会一年一年变大"
    def split_four(s):
        l = len(s)
        part1 = s[:l//4]
        part2 = s[l//4 : l//4*2]
        part3 = s[l//4*2 : l//4*3]
        part4 = s[l//4*3:]
        return part1, part2, part3, part4
    def split_two(s):
        mid = len(s) // 2
        return s[:mid], s[mid:]
    q1, q2, q3, q4 = split_four(q)
    ans1, ans2 = split_two(a)
    return q1, q2, q3, q4, ans1, ans2

# 发送微信消息（参数完全对齐，无缺失）
def send_message(to_user, access_token, real_temp, min_temp, max_temp, weather, wind_dir, sunrise, sunset,
                 love1, love2,
                 riddle_q1, riddle_q2, riddle_q3, riddle_q4,
                 riddle_ans1, riddle_ans2):

    send_url = f"https://api.weixin.qq.com/cgi-bin/template/send?access_token={access_token}"
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week_list = ["周日","周一","周二","周三","周四","周五","周六"]
    date_str = f"{today} {week_list[today.weekday()]}"

    try:
        love_day = date(*map(int, config["love_date"].split("-")))
        love_days = str((today - love_day).days)
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

            "riddle_q1": {"value": riddle_q1, "color": get_color()},
            "riddle_q2": {"value": riddle_q2, "color": get_color()},
            "riddle_q3": {"value": riddle_q3, "color": get_color()},
            "riddle_q4": {"value": riddle_q4, "color": get_color()},

            "riddle_ans1": {"value": riddle_ans1, "color": get_color()},
            "riddle_ans2": {"value": riddle_ans2, "color": get_color()}
        }
    }

    for _ in range(3):
        try:
            res = requests.post(send_url, json=data, timeout=15)
            if res.json().get("errcode") == 0:
                print(f"✅ 推送成功！")
                return
        except:
            sleep(1)
    print("❌ 推送失败")
    sys.exit(1)

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        config = eval(f.read())

    token = get_access_token()
    wt1, wt2, wt3, wt4, wt5, wt6, wt7 = get_weather("临沂")
    love1, love2 = get_love_words()
    rq1, rq2, rq3, rq4, ra1, ra2 = get_riddle()

    openids = config["user"]
    if not isinstance(openids, list):
        openids = [openids]

    for oid in openids:
        send_message(oid, token, wt1, wt2, wt3, wt4, wt5, wt6, wt7,
                     love1, love2,
                     rq1, rq2, rq3, rq4, ra1, ra2)
