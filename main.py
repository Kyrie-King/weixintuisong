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
    except Exception as e:
        print(f"获取access_token失败：{e}")
        sys.exit(1)
    return access_token


def get_weather():
    """直接返回固定值，避免API异常导致空值"""
    weather = "晴"
    temp = "22℃"  # 强制写死，不会空
    wind_dir = "南风"
    min_temp = "18℃"
    max_temp = "28℃"
    sunrise = "06:00"
    sunset = "18:00"
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
        print(f"生日计算异常：{e}")
        return "未知"


def get_random_love_words():
    """随机土味情话"""
    love_words = [
        "我喜欢你，胜于昨日，略匮明朝。",
        "你是我明目张胆的偏爱，众所周知的私心。",
        "一想到能和你共度余生，我就对余生充满期待。",
        "世界那么大，遇见你不容易，我不想错过。",
        "我想把所有温柔和浪漫都给你。"
    ]
    return random.choice(love_words)


def get_random_riddle():
    """随机脑筋急转弯"""
    riddles = [
        {"q": "什么东西越洗越脏？", "a": "水"},
        {"q": "什么门永远关不上？", "a": "球门"},
        {"q": "什么东西明明是你的，别人却用得比你多？", "a": "你的名字"},
        {"q": "什么动物最容易摔倒？", "a": "狐狸，因为它很狡猾（脚滑）"},
        {"q": "什么东西有五个头，但人不觉得它怪？", "a": "手和脚"}
    ]
    riddle = random.choice(riddles)
    return riddle["q"], riddle["a"]


def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset):
    """推送消息，完全匹配你的模板字段"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    # 计算在一起天数
    try:
        love_year, love_month, love_day = map(int, config["love_date"].split("-"))
        love_date = date(love_year, love_month, love_day)
        love_days = str((today - love_date).days)
    except Exception as e:
        print(f"在一起天数计算异常：{e}")
        love_days = "未知"

    # 获取情话和脑筋急转弯
    love_word = get_random_love_words()
    riddle_q, riddle_a = get_random_riddle()

    # 模板字段和你推送完全对应
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "city": {"value": "临沂", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "min_temp": {"value": min_temp, "color": get_color()},
            "max_temp": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": "", "color": get_color()},
            "birthday2": {"value": "", "color": get_color()},
            "love_word": {"value": love_word, "color": get_color()},
            "riddle_q": {"value": riddle_q, "color": get_color()},
            "riddle_a": {"value": riddle_a, "color": get_color()}
        }
    }

    # 生日处理
    try:
        if "birthday1" in config:
            b1_days = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
            if b1_days == "0":
                data["data"]["birthday1"]["value"] = f"今天是{config['birthday1']['name']}生日！"
            else:
                data["data"]["birthday1"]["value"] = f"距离{config['birthday1']['name']}生日还有{b1_days}天"
        
        if "birthday2" in config:
            b2_days = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
            if b2_days == "0":
                data["data"]["birthday2"]["value"] = f"今天是{config['birthday2']['name']}生日！"
            else:
                data["data"]["birthday2"]["value"] = f"距离{config['birthday2']['name']}生日还有{b2_days}天"
    except Exception as e:
        print(f"生日数据处理异常：{e}")

    # 发送请求
    try:
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=data, timeout=10)
        resp.raise_for_status()
        resp_data = resp.json()
        if resp_data["errcode"] == 0:
            print(f"✅ 推送成功！")
        else:
            print(f"❌ 推送失败：{resp_data.get('errmsg')}")
    except Exception as e:
        print(f"❌ 推送异常：{e}")


if __name__ == "__main__":
    # 读取配置
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except Exception as e:
        print(f"读取配置异常：{e}")
        sys.exit(1)

    # 检查必要配置
    must_have = ["app_id", "app_secret", "template_id", "user", "love_date"]
    for key in must_have:
        if key not in config:
            print(f"配置缺失：{key}")
            sys.exit(1)

    # 获取access_token
    access_token = get_access_token()

    # 获取天气（固定值，不会空）
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather()

    # 推送
    for user in config["user"]:
        send_message(user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset)
