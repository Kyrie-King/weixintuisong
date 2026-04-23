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


def get_weather():
    """修复版天气获取，解决温度空值、英文天气/风向问题"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    # 默认值
    weather = "晴"
    temp = "25℃"
    wind_dir = "南风"
    min_temp = "18℃"
    max_temp = "32℃"
    sunrise = "06:00"
    sunset = "18:00"

    # 风向映射表
    wind_map = {
        "N": "北风", "NE": "东北风", "E": "东风", "SE": "东南风",
        "S": "南风", "SW": "西南风", "W": "西风", "NW": "西北风",
        "NNE": "东北偏北风", "ENE": "东北偏东风", "ESE": "东南偏东风", "SSE": "东南偏南风",
        "SSW": "西南偏南风", "WSW": "西南偏西风", "WNW": "西北偏西风", "NNW": "西北偏北风"
    }

    # 天气映射表
    weather_map = {
        "Clear": "晴", "Sunny": "晴", "Partly Cloudy": "多云", "Cloudy": "阴",
        "Overcast": "阴", "Rain": "雨", "Light Rain": "小雨", "Heavy Rain": "大雨",
        "Thunderstorm": "雷阵雨", "Snow": "雪", "Fog": "雾"
    }

    try:
        url = "https://wttr.in/Linyi?format=j1"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # 提取温度（解决空值问题）
        current = data["current_condition"][0]
        temp = f"{current['temp_C']}℃"
        wind_dir = wind_map.get(current["winddir16Point"], current["winddir16Point"])
        weather = weather_map.get(current["weatherDesc"][0]["value"], current["weatherDesc"][0]["value"])
        
        # 提取高低温
        today = data["weather"][0]
        min_temp = f"{today['mintempC']}℃"
        max_temp = f"{today['maxtempC']}℃"
        
        print(f"✅ 天气获取成功：{weather} | 实时温度：{temp} | 风向：{wind_dir}")
    except Exception as e:
        print(f"❌ 获取天气失败，使用默认数据：{str(e)}")

    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset


def get_ciba():
    """获取每日金句"""
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        ciba_data = resp.json()
        note_en = ciba_data.get("content", "Keep going")
        note_ch = ciba_data.get("note", "每天都有新的希望")
    except Exception as e:
        print(f"获取金句失败：{str(e)}")
        note_en = "Keep going"
        note_ch = "每天都有新的希望"
    return note_ch, note_en


def get_random_love_words():
    """随机土味情话"""
    love_words = [
        "我觉得你特别像一款游戏，叫我的世界。",
        "你知道我的缺点是什么吗？是缺点你。",
        "莫文蔚的阴天，孙燕姿的雨天，周杰伦的晴天，都不如你和我聊天。",
        "我想买一块地，什么地？你的死心塌地。",
        "你知道我最喜欢吃什么水果吗？是你这个开心果。",
        "最近有谣言说我喜欢你，我要澄清一下，那不是谣言。"
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


def send_message(to_user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    """推送消息，完整支持所有字段"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"

    try:
        love_year, love_month, love_day = map(int, config["love_date"].split("-"))
        love_date = date(love_year, love_month, love_day)
        love_days = str((today - love_date).days)
    except Exception as e:
        print(f"计算在一起天数异常：{str(e)}")
        sys.exit(1)

    # 获取土味情话和脑筋急转弯
    love_word = get_random_love_words()
    riddle_q, riddle_a = get_random_riddle()

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": date_str, "color": get_color()},
            "region": {"value": "临沂", "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()},
            "city": {"value": "临沂", "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_word": {"value": love_word, "color": get_color()},
            "riddle_q": {"value": riddle_q, "color": get_color()},
            "riddle_a": {"value": riddle_a, "color": get_color()}
        }
    }

    try:
        if "birthday1" in config:
            b1_days = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
            if b1_days == "0":
                b1_text = f"🎉 今天是{config['birthday1']['name']}的生日！祝生日快乐，天天开心，万事顺意！🎂"
            else:
                b1_text = f"距离{config['birthday1']['name']}生日还有{b1_days}天"
            data["data"]["birthday1"] = {"value": b1_text, "color": get_color()}
        
        if "birthday2" in config:
            b2_days = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
            if b2_days == "0":
                b2_text = f"🎉 今天是{config['birthday2']['name']}的生日！祝生日快乐，平安喜乐，岁岁无忧！🎂"
            else:
                b2_text = f"距离{config['birthday2']['name']}生日还有{b2_days}天"
            data["data"]["birthday2"] = {"value": b2_text, "color": get_color()}
    except Exception as e:
        print(f"处理生日数据异常：{str(e)}")
        sys.exit(1)

    try:
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=data, timeout=10)
        resp.raise_for_status()
        resp_data = resp.json()
        if resp_data["errcode"] == 0:
            print(f"向 {to_user} 推送成功！")
        else:
            print(f"推送失败：{resp_data.get('errmsg')}")
    except Exception as e:
        print(f"推送消息异常：{str(e)}")


if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("找不到config.txt文件！")
        sys.exit(1)
    except SyntaxError:
        print("config.txt格式错误，请检查！")
        sys.exit(1)
    except Exception as e:
        print(f"读取配置异常：{str(e)}")
        sys.exit(1)

    must_have = ["app_id", "app_secret", "template_id", "user", "love_date"]
    for key in must_have:
        if key not in config:
            print(f"配置缺失：{key}")
            sys.exit(1)

    access_token = get_access_token()
    users = config["user"]
    if not isinstance(users, list) or len(users) == 0:
        print("user字段必须是非空列表！")
        sys.exit(1)

    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather()

    note_ch = config.get("note_ch", "")
    note_en = config.get("note_en", "")
    if not note_ch or not note_en:
        note_ch, note_en = get_ciba()

    for user in users:
        send_message(user, access_token, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)
