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
        os.system("pause")
        sys.exit(1)
    except Exception as e:
        print(f"获取access_token异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
    return access_token
 
 
def get_weather(region):
    """原有天气逻辑 + 新增最低/最高温、日出日落"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = "https://api.qweather.com/v7/city/lookup?location={}&key={}".format(region, key)
    
    # 1. 获取地区ID（原有逻辑）
    try:
        response = requests.get(region_url, headers=headers, timeout=10)
        response.raise_for_status()
        region_data = response.json()
        
        if region_data.get("code") == "404":
            print(f"地区「{region}」未找到，请检查！")
            os.system("pause")
            sys.exit(1)
        elif region_data.get("code") == "401":
            print("和风天气key无效/过期，请检查！")
            os.system("pause")
            sys.exit(1)
        elif region_data.get("code") != "200" or not region_data.get("location"):
            print("获取地区ID失败，使用默认天气数据")
            # 默认值：原有字段 + 新增字段
            return "多云", "25℃", "南风", "18℃", "32℃", "06:00", "18:00"
        
        location_id = region_data["location"][0]["id"]
        
    except Exception as e:
        print(f"获取地区ID异常：{str(e)}，使用默认数据")
        return "多云", "25℃", "南风", "18℃", "32℃", "06:00", "18:00"
 
    # 2. 调用接口（原有：实时天气；新增：3天预报、天文接口）
    now_url = f"https://api.qweather.com/v7/weather/now?location={location_id}&key={key}"
    daily_url = f"https://api.qweather.com/v7/weather/3d?location={location_id}&key={key}"
    astro_url = f"https://api.qweather.com/v7/astronomy/sun?location={location_id}&date={date.today().strftime('%Y%m%d')}&key={key}"
 
    # 初始化变量（原有 + 新增）
    weather = "多云"   # 原有
    temp = "25℃"       # 原有
    wind_dir = "南风"  # 原有（对应wind_direction）
    min_temp = "18℃"   # 新增：最低温
    max_temp = "32℃"   # 新增：最高温
    sunrise = "06:00"  # 新增：日出
    sunset = "18:00"   # 新增：日落
 
    # 抓取实时天气（原有逻辑）
    try:
        resp = requests.get(now_url, headers=headers, timeout=10)
        resp.raise_for_status()
        now_data = resp.json()
        if now_data.get("code") == "200":
            weather = now_data["now"]["text"]
            temp = f"{now_data['now']['temp']}℃"
            wind_dir = now_data["now"]["windDir"]  # 风向数据（给wind_direction用）
    except Exception as e:
        print(f"获取实时天气失败：{str(e)}")
 
    # 新增：抓取最低/最高温
    try:
        resp = requests.get(daily_url, headers=headers, timeout=10)
        resp.raise_for_status()
        daily_data = resp.json()
        if daily_data.get("code") == "200" and daily_data.get("daily"):
            today_daily = daily_data["daily"][0]
            min_temp = f"{today_daily['tempMin']}℃"
            max_temp = f"{today_daily['tempMax']}℃"
    except Exception as e:
        print(f"获取最低/最高温失败：{str(e)}")
 
    # 新增：抓取日出日落
    try:
        resp = requests.get(astro_url, headers=headers, timeout=10)
        resp.raise_for_status()
        astro_data = resp.json()
        if astro_data.get("code") == "200" and astro_data.get("sun"):
            sunrise = astro_data["sun"][0]["rise"]
            sunset = astro_data["sun"][0]["set"]
    except Exception as e:
        print(f"获取日出日落失败：{str(e)}")
    
    # 返回值：原有3个 + 新增4个
    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset
 
 
def get_birthday(birthday_str, year, today):
    """计算生日倒计时（原有功能，适配你的birthday1/birthday2）"""
    try:
        # 区分农历/公历
        if birthday_str.startswith("r"):
            _, month, day = birthday_str.split("-")
            lunar_date = ZhDate(year, int(month), int(day))
            solar_date = lunar_date.to_datetime().date()
            birthday_date = date(year, solar_date.month, solar_date.day)
        else:
            _, month, day = birthday_str.split("-")
            birthday_date = date(year, int(month), int(day))
 
        # 计算天数差
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
        print(f"计算生日天数异常：{str(e)}")
        return "未知"
 
 
def get_ciba():
    """获取每日金句（原有功能）"""
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
 
 
def send_message(to_user, access_token, region, weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en):
    """推送消息（新增city.DATA和wind_direction.DATA）"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = date(localtime().tm_year, localtime().tm_mon, localtime().tm_mday)
    week = week_list[today.isoweekday() % 7]
    date_str = f"{today} {week}"
 
    # 计算在一起天数（原有功能）
    try:
        love_year, love_month, love_day = map(int, config["love_date"].split("-"))
        love_date = date(love_year, love_month, love_day)
        love_days = str((today - love_date).days)
    except Exception as e:
        print(f"计算在一起天数异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
 
    # 组装模板数据（核心修改：新增city和wind_direction两个变量）
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            # 原有字段
            "date": {"value": date_str, "color": get_color()},
            "region": {"value": region, "color": get_color()},  # 保留原有region，兼容旧模板
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},  # 保留原有wind_dir，兼容旧模板
            "love_day": {"value": love_days, "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()},
            # 新增字段：city（和region值一致，适配模板里的city.DATA）
            "city": {"value": region, "color": get_color()},
            # 新增字段：wind_direction（和wind_dir值一致，适配模板里的wind_direction.DATA）
            "wind_direction": {"value": wind_dir, "color": get_color()},
            # 新增的温度/日出日落字段
            "min_temperature": {"value": min_temp, "color": get_color()},
            "max_temperature": {"value": max_temp, "color": get_color()},
            "sunrise": {"value": sunrise, "color": get_color()},
            "sunset": {"value": sunset, "color": get_color()}
        }
    }
 
    # 处理生日数据（原有功能，适配你的birthday1/birthday2）
    try:
        # birthday1
        if "birthday1" in config:
            b1_days = get_birthday(config["birthday1"]["birthday"], localtime().tm_year, today)
            b1_text = f"今天{config['birthday1']['name']}生日🎂！" if b1_days == "0" else f"距离{config['birthday1']['name']}生日还有{b1_days}天"
            data["data"]["birthday1"] = {"value": b1_text, "color": get_color()}
        
        # birthday2
        if "birthday2" in config:
            b2_days = get_birthday(config["birthday2"]["birthday"], localtime().tm_year, today)
            b2_text = f"今天{config['birthday2']['name']}生日🎂！" if b2_days == "0" else f"距离{config['birthday2']['name']}生日还有{b2_days}天"
            data["data"]["birthday2"] = {"value": b2_text, "color": get_color()}
    except Exception as e:
        print(f"处理生日数据异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
 
    # 推送消息（原有逻辑）
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
    # 读取配置文件（原有功能，适配你的双引号格式）
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("找不到config.txt文件！")
        os.system("pause")
        sys.exit(1)
    except SyntaxError:
        print("config.txt格式错误，请检查！")
        os.system("pause")
        sys.exit(1)
    except Exception as e:
        print(f"读取配置异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
 
    # 校验核心配置（原有字段，无新增）
    must_have = ["app_id", "app_secret", "weather_key", "template_id", "user", "region", "love_date"]
    for key in must_have:
        if key not in config:
            print(f"配置缺失：{key}")
            os.system("pause")
            sys.exit(1)
 
    # 执行核心流程（原有逻辑 + 传递新增参数）
    access_token = get_access_token()
    users = config["user"]
    if not isinstance(users, list) or len(users) == 0:
        print("user字段必须是非空列表！")
        os.system("pause")
        sys.exit(1)
 
    # 获取天气（接收新增的4个返回值）
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather(config["region"])
 
    # 获取金句（原有逻辑）
    note_ch = config.get("note_ch", "")
    note_en = config.get("note_en", "")
    if not note_ch or not note_en:
        note_ch, note_en = get_ciba()
 
    # 推送消息（传递新增参数）
    for user in users:
        send_message(user, access_token, config["region"], weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset, note_ch, note_en)
 
    os.system("pause")
