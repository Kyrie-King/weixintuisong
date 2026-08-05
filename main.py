import random
from requests import get, post
from datetime import datetime, date, timedelta
from zhdate import ZhDate
import sys
import os
import json


def get_color():
    """随机颜色"""
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    """获取微信 access_token"""
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        resp = get(post_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        access_token = data['access_token']
    except Exception as e:
        print(f"获取access_token失败：{e}")
        sys.exit(1)
    return access_token


def get_weather(city_adcode):
    """
    获取天气数据（实时 + 今日预报）
    返回：天气状况、实时温度、最低温、最高温、风向
    最低/最高温从高德预报接口真实获取，不再写死
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    key = config["gaode_key"]
    weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"

    # ===== 1. 实时天气 =====
    params_base = {
        "city": city_adcode,
        "key": key,
        "extensions": "base",
        "output": "json"
    }
    try:
        resp = get(weather_url, headers=headers, params=params_base, timeout=15)
        response = resp.json()
    except Exception as e:
        print(f"实时天气请求失败：{e}")
        sys.exit(1)

    if response.get("status") != "1":
        print(f"天气API错误：{response}")
        sys.exit(1)

    lives = response["lives"][0]
    weather = lives["weather"]
    real_temp = lives["temperature"]
    wind_dir = lives["winddirection"] + "风"

    # ===== 2. 今日预报（真实高低温）=====
    try:
        params_all = {
            "city": city_adcode,
            "key": key,
            "extensions": "all",
            "output": "json"
        }
        resp_all = get(weather_url, headers=headers, params=params_all, timeout=15)
        all_data = resp_all.json()
        if all_data.get("status") != "1" or not all_data.get("forecasts"):
            raise Exception(f"预报API返回异常：{all_data}")
        today_cast = all_data["forecasts"][0]["casts"][0]
        min_temp = today_cast["nighttemp"]
        max_temp = today_cast["daytemp"]
    except Exception as e:
        print(f"❌ 获取预报天气失败：{e}")
        sys.exit(1)

    return weather, real_temp, min_temp, max_temp, wind_dir


def get_sunrise_sunset(city_adcode):
    """
    获取日出日落时间（真实数据）
    先用高德地理编码拿经纬度，再调用 sunrise-sunset.org 计算
    """
    key = config["gaode_key"]

    # 1. 地理编码获取经纬度
    try:
        geo_url = "https://restapi.amap.com/v3/geocode/geo"
        params = {"address": city_adcode, "key": key, "output": "json"}
        resp = get(geo_url, params=params, timeout=15)
        geo_data = resp.json()
        if geo_data.get("status") != "1" or not geo_data.get("geocodes"):
            raise Exception(f"地理编码返回异常：{geo_data}")
        location = geo_data["geocodes"][0]["location"]
        lng, lat = location.split(",")
    except Exception as e:
        print(f"❌ 地理编码失败：{e}")
        sys.exit(1)

    # 2. 调用日出日落API
    try:
        ss_url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&formatted=0&date=today"
        ss_resp = get(ss_url, timeout=15)
        ss_data = ss_resp.json()
        if ss_data.get("status") != "OK":
            raise Exception(f"日出日落API返回异常：{ss_data}")

        sunrise_utc = ss_data["results"]["sunrise"]
        sunset_utc = ss_data["results"]["sunset"]

        sunrise_dt = datetime.fromisoformat(sunrise_utc.replace("Z", "+00:00"))
        sunset_dt = datetime.fromisoformat(sunset_utc.replace("Z", "+00:00"))
        sunrise_bj = sunrise_dt + timedelta(hours=8)
        sunset_bj = sunset_dt + timedelta(hours=8)

        sunrise = sunrise_bj.strftime("%H:%M")
        sunset = sunset_bj.strftime("%H:%M")
        return sunrise, sunset
    except Exception as e:
        print(f"❌ 获取日出日落失败：{e}")
        sys.exit(1)


def get_birthday(birthday_str, today):
    """生日倒计时计算，支持公历和农历（r-开头）"""
    if birthday_str.startswith("r-"):
        parts = birthday_str.split("-")
        month = int(parts[1])
        day = int(parts[2])
        birth_date = ZhDate(today.year, month, day).to_datetime().date()
        if birth_date < today:
            birth_date = ZhDate(today.year + 1, month, day).to_datetime().date()
    else:
        birth_parts = birthday_str.split("-")
        month = int(birth_parts[1])
        day = int(birth_parts[2])
        birth_date = date(today.year, month, day)
        if birth_date < today:
            birth_date = date(today.year + 1, month, day)
    days_left = (birth_date - today).days
    return days_left


def get_love_words():
    """
    从多个接口动态拉取情话/优美句子，失败直接报错退出
    返回4条不重复的情话
    """
    words = []

    # 多个API源，依次尝试，凑够4条为止
    api_list = [
        # 1. 一言（综合类，句子质量高）
        {
            "url": "https://v1.hitokoto.cn/?c=i&encode=json",
            "count": 3,  # 尝试取3次不同的
            "path": ["hitokoto"]
        },
        # 2. uomg 土味情话
        {
            "url": "https://api.uomg.com/api/rand.qinghua?format=json",
            "count": 2,
            "path": ["content"]
        },
        # 3. lovelive 甜言蜜语
        {
            "url": "https://api.lovelive.tools/api/SweetNothings/1/Serialization/Json",
            "count": 2,
            "path": ["returnObj", 0, "content"]
        },
        # 4. 一言（文学类兜底）
        {
            "url": "https://v1.hitokoto.cn/?c=d&encode=json",
            "count": 1,
            "path": ["hitokoto"]
        },
    ]

    def get_val(data, path):
        val = data
        for k in path:
            if isinstance(k, int) and isinstance(val, list):
                val = val[k] if k < len(val) else None
            elif isinstance(val, dict):
                val = val.get(k)
            else:
                val = None
            if val is None:
                break
        return val if isinstance(val, str) and len(val.strip()) > 2 else None

    for api in api_list:
        if len(words) >= 4:
            break
        for _ in range(api["count"]):
            if len(words) >= 4:
                break
            try:
                resp = get(api["url"], timeout=10)
                resp.raise_for_status()
                data = resp.json()
                val = get_val(data, api["path"])
                if val and val not in words:
                    words.append(val)
            except Exception:
                # 单个请求失败不退出，继续试其他的
                pass

    # 所有API都拉不到4条 → 报错退出
    if len(words) < 4:
        print(f"❌ 情话获取失败，仅获得 {len(words)} 条，需要4条")
        sys.exit(1)

    return words[0], words[1], words[2], words[3]


def get_riddle():
    """
    从接口动态拉取脑筋急转弯，失败直接报错退出
    返回：4个问题 + 4个答案
    """
    questions = []
    answers = []

    # 多个API源，依次尝试，凑够4道为止
    api_list = [
        # 1. 阿皮呀 - 脑筋急转弯
        {
            "url": "https://api.aytwl.cn/api/nqjzw.php",
            "q_path": ["title"],
            "a_path": ["answer"]
        },
        # 2. UOMG - 谜语（脑筋急转弯类）
        {
            "url": "https://api.uomg.com/api/rand.miyu?format=json",
            "q_path": ["miyu"],
            "a_path": ["dianji"]
        },
        # 3. 天行数据API免费接口（谜语）
        {
            "url": "http://api.tianapi.com/miyu/index?key=094a7dd1e3a49c32e0c0b6e4f3a5c7d3&num=1",
            "q_path": ["newslist", 0, "content"],
            "a_path": ["newslist", 0, "answer"]
        },
    ]

    def get_val(data, path):
        val = data
        for k in path:
            if isinstance(k, int) and isinstance(val, list):
                val = val[k] if k < len(val) else None
            elif isinstance(val, dict):
                val = val.get(k)
            else:
                val = None
            if val is None:
                break
        return val if isinstance(val, str) and len(val.strip()) > 0 else None

    # 每个API最多尝试取几次，总共凑够4道
    max_attempts = 20
    attempts = 0

    while len(questions) < 4 and attempts < max_attempts:
        attempts += 1
        api = api_list[attempts % len(api_list)]
        try:
            resp = get(api["url"], timeout=10)
            resp.raise_for_status()
            data = resp.json()

            q = get_val(data, api["q_path"])
            a = get_val(data, api["a_path"])

            if q and a and q not in questions:
                questions.append(q)
                answers.append("答案：" + a)
        except Exception:
            pass  # 单个请求失败继续试

    if len(questions) < 4:
        print(f"❌ 脑筋急转弯获取失败，仅获得 {len(questions)} 道，需要4道")
        sys.exit(1)

    return questions[0], questions[1], questions[2], questions[3], \
           answers[0], answers[1], answers[2], answers[3]


def send_message(to_user, access_token, city_name, weather, real_temp,
                 min_temp, max_temp, wind_dir, sunrise, sunset):
    """发送微信模板消息"""
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date.today()
    week = week_list[today.isoweekday() % 7]

    # 相恋天数
    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    love_days = (today - love_date).days

    # 生日倒计时
    birth1 = config["birthday1"]
    birth2 = config["birthday2"]
    birth_day1 = get_birthday(birth1["birthday"], today)
    birth_day2 = get_birthday(birth2["birthday"], today)
    birthday1_data = f"距离{birth1['name']}的生日还有{birth_day1}天"
    birthday2_data = f"距离{birth2['name']}的生日还有{birth_day2}天"

    # 情话 + 脑筋急转弯
    l1, l2, l3, l4 = get_love_words()
    rq1, rq2, rq3, rq4, ra1, ra2, ra3, ra4 = get_riddle()

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {"value": f"{today} {week}", "color": get_color()},
            "city": {"value": city_name, "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "real_temp": {"value": real_temp, "color": get_color()},
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "wind_direction": {"value": wind_dir, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()},
            "love_day": {"value": love_days, "color": get_color()},
            "birthday1": {"value": birthday1_data, "color": get_color()},
            "birthday2": {"value": birthday2_data, "color": get_color()},
            "love1": {"value": l1, "color": get_color()},
            "love2": {"value": l2, "color": get_color()},
            "love3": {"value": l3, "color": get_color()},
            "love4": {"value": l4, "color": get_color()},
            "riddle_q1": {"value": rq1, "color": get_color()},
            "riddle_q2": {"value": rq2, "color": get_color()},
            "riddle_q3": {"value": rq3, "color": get_color()},
            "riddle_q4": {"value": rq4, "color": get_color()},
            "riddle_ans1": {"value": ra1, "color": get_color()},
            "riddle_ans2": {"value": f"{ra2} {ra3} {ra4}", "color": get_color()},
        }
    }

    headers = {'Content-Type': 'application/json'}
    try:
        response = post(url, headers=headers, json=data, timeout=15).json()
        if response.get("errcode") == 0:
            print(f"✅ 推送给 {to_user} 成功")
        else:
            print(f"❌ 推送给 {to_user} 失败：{response}")
    except Exception as e:
        print(f"❌ 推送异常：{e}")


def load_config():
    """从环境变量加载配置，不再依赖 config.txt"""
    required = ["APP_ID", "APP_SECRET", "TEMPLATE_ID", "GAODE_KEY",
                "USER", "LOVE_DATE", "BIRTHDAY1_NAME", "BIRTHDAY1_DATE",
                "BIRTHDAY2_NAME", "BIRTHDAY2_DATE"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"❌ 缺少环境变量：{', '.join(missing)}")
        sys.exit(1)

    # user 字段是 JSON 数组
    try:
        user_list = json.loads(os.environ["USER"])
    except Exception:
        print("❌ USER 环境变量格式错误，应为 JSON 数组，如 [\"openid1\", \"openid2\"]")
        sys.exit(1)

    return {
        "app_id": os.environ["APP_ID"],
        "app_secret": os.environ["APP_SECRET"],
        "template_id": os.environ["TEMPLATE_ID"],
        "gaode_key": os.environ["GAODE_KEY"],
        "user": user_list,
        "love_date": os.environ["LOVE_DATE"],
        "birthday1": {
            "name": os.environ["BIRTHDAY1_NAME"],
            "birthday": os.environ["BIRTHDAY1_DATE"]
        },
        "birthday2": {
            "name": os.environ["BIRTHDAY2_NAME"],
            "birthday": os.environ["BIRTHDAY2_DATE"]
        }
    }


if __name__ == "__main__":
    # 从环境变量加载配置（GitHub Actions / 本地都用环境变量）
    config = load_config()

    accessToken = get_access_token()
    users = config["user"]

    # 临沂市河东区 adcode
    CITY_ADCODE = "371312"
    CITY_NAME = "临沂市河东区"

    # 获取天气
    weather, real_temp, min_temp, max_temp, wind_dir = get_weather(CITY_ADCODE)
    sunrise, sunset = get_sunrise_sunset(CITY_ADCODE)

    print(f"📍 {CITY_NAME}")
    print(f"🌤 {weather}  🌡 {real_temp}°C（{min_temp}~{max_temp}°C）")
    print(f"💨 {wind_dir}  🌅 日出 {sunrise}  🌇 日落 {sunset}")

    # 推送
    for user in users:
        send_message(user, accessToken, CITY_NAME, weather, real_temp,
                     min_temp, max_temp, wind_dir, sunrise, sunset)
