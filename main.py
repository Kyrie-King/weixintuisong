import random
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os
import json  # 新增：用于安全解析配置（可选优化）
 
 
def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)
 
 
def get_access_token():
    # appId
    app_id = config["app_id"]
    # appSecret
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        # 新增：添加超时和异常捕获
        response = get(post_url, timeout=10)
        response.raise_for_status()  # 触发HTTP错误（4xx/5xx）
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
    """修复核心：添加完整异常捕获+JSON解析容错+网络超时"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = "https://geoapi.qweather.com/v2/city/lookup?location={}&key={}".format(region, key)
    
    # 第一步：请求地区ID - 新增完整异常捕获
    try:
        # 添加超时（避免卡死）+ 触发HTTP错误
        response = get(region_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 修复JSON解析报错：添加容错
        try:
            region_data = response.json()
        except json.JSONDecodeError:
            print("和风天气API返回非JSON格式数据，请检查网络或API key")
            os.system("pause")
            sys.exit(1)
        
        # 状态码校验优化
        if region_data.get("code") == "404":
            print(f"推送消息失败：地区「{region}」未找到，请检查地区名是否正确！")
            os.system("pause")
            sys.exit(1)
        elif region_data.get("code") == "401":
            print("推送消息失败：和风天气key无效或已过期，请检查！")
            os.system("pause")
            sys.exit(1)
        elif region_data.get("code") != "200":
            print(f"获取地区信息失败：{region_data.get('msg', '未知错误')}")
            os.system("pause")
            sys.exit(1)
        
        # 容错：防止location为空
        if not region_data.get("location"):
            print(f"地区「{region}」未查询到有效位置信息")
            os.system("pause")
            sys.exit(1)
        location_id = region_data["location"][0]["id"]
        
    except requests.exceptions.Timeout:
        print("请求和风天气API超时，请检查网络！")
        os.system("pause")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"请求地区信息失败：{str(e)}")
        os.system("pause")
        sys.exit(1)
    except Exception as e:
        print(f"解析地区信息异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
 
    # 第二步：请求天气数据 - 新增异常捕获
    weather_url = "https://devapi.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
    try:
        response = get(weather_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 修复JSON解析报错
        try:
            weather_data = response.json()
        except json.JSONDecodeError:
            print("天气接口返回非JSON格式数据，请稍后重试")
            os.system("pause")
            sys.exit(1)
        
        if weather_data.get("code") != "200":
            print(f"获取天气失败：{weather_data.get('msg', '未知错误')}")
            os.system("pause")
            sys.exit(1)
        
        # 容错：防止字段缺失
        weather = weather_data["now"].get("text", "未知")
        temp = weather_data["now"].get("temp", "0") + u"\N{DEGREE SIGN}" + "C"
        wind_dir = weather_data["now"].get("windDir", "未知")
        
    except requests.exceptions.Timeout:
        print("请求天气数据超时，请检查网络！")
        os.system("pause")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"请求天气数据失败：{str(e)}")
        os.system("pause")
        sys.exit(1)
    except Exception as e:
        print(f"解析天气数据异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
    
    return weather, temp, wind_dir
 
 
def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 获取农历生日的今年对应的月和日
        try:
            birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在（如闰月问题）")
            os.system("pause")
            sys.exit(1)
        birthday_month = birthday.month
        birthday_day = birthday.day
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
 
    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    try:
        if today > year_date:
            if birthday_year[0] == "r":
                # 获取农历明年生日的月和日
                r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
                birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
            else:
                birth_date = date((year + 1), birthday_month, birthday_day)
            birth_day = str(birth_date.__sub__(today)).split(" ")[0]
        elif today == year_date:
            birth_day = 0
        else:
            birth_date = year_date
            birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    except Exception as e:
        print(f"计算生日天数异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
    
    return birth_day
 
 
def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    try:
        r = get(url, headers=headers, timeout=10)
        r.raise_for_status()
        ciba_data = r.json()
        note_en = ciba_data.get("content", "No content today")
        note_ch = ciba_data.get("note", "今日无金句")
    except Exception as e:
        print(f"获取每日金句失败，使用默认文案：{str(e)}")
        note_en = "Keep going"
        note_ch = "每天都有新的希望"
    return note_ch, note_en
 
 
def send_message(to_user, access_token, region_name, weather, temp, wind_dir, note_ch, note_en):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    
    # 获取在一起的日子的日期格式 - 新增容错
    try:
        love_year = int(config["love_date"].split("-")[0])
        love_month = int(config["love_date"].split("-")[1])
        love_day = int(config["love_date"].split("-")[2])
        love_date = date(love_year, love_month, love_day)
        # 获取在一起的日期差
        love_days = str(today.__sub__(love_date)).split(" ")[0]
    except Exception as e:
        print(f"计算恋爱纪念日异常：{str(e)}，请检查love_date格式")
        os.system("pause")
        sys.exit(1)
    
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": get_color()
            },
            "region": {
                "value": region_name,
                "color": get_color()
            },
            "weather": {
                "value": weather,
                "color": get_color()
            },
            "temp": {
                "value": temp,
                "color": get_color()
            },
            "wind_dir": {
                "value": wind_dir,
                "color": get_color()
            },
            "love_day": {
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            }
        }
    }
    
    # 生日数据处理 - 新增容错
    try:
        for key, value in birthdays.items():
            # 获取距离下次生日的时间
            birth_day = get_birthday(value["birthday"], year, today)
            if birth_day == 0:
                birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
            else:
                birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
            # 将生日数据插入data
            data["data"][key] = {"value": birthday_data, "color": get_color()}
    except Exception as e:
        print(f"处理生日数据异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    
    # 推送消息 - 新增异常捕获
    try:
        response = post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        resp_data = response.json()
        
        if resp_data["errcode"] == 40037:
            print("推送消息失败，请检查模板id是否正确")
        elif resp_data["errcode"] == 40036:
            print("推送消息失败，请检查模板id是否为空")
        elif resp_data["errcode"] == 40003:
            print(f"推送消息失败：用户「{to_user}」的微信号/openid不正确")
        elif resp_data["errcode"] == 0:
            print(f"向「{to_user}」推送消息成功")
        else:
            print(f"推送消息失败：{resp_data.get('errmsg', '未知错误')}")
    except Exception as e:
        print(f"推送消息异常：{str(e)}")
 
 
if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            # 优化：替换eval（安全风险），改用json解析（需确保config.txt是标准JSON格式）
            # 如果你的config.txt是Python字典格式（如单引号），保留eval，仅添加异常捕获
            try:
                config = json.load(f)  # 推荐：改用JSON解析
                # config = eval(f.read())  # 兼容旧格式：保留eval（注释掉上面一行，打开这行）
            except json.JSONDecodeError:
                print("配置文件格式错误：请确保config.txt是标准JSON格式（使用双引号）")
                os.system("pause")
                sys.exit(1)
    except FileNotFoundError:
        print("推送消息失败，请检查config.txt文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except SyntaxError:
        print("推送消息失败，请检查配置文件格式是否正确")
        os.system("pause")
        sys.exit(1)
    except Exception as e:
        print(f"读取配置文件异常：{str(e)}")
        os.system("pause")
        sys.exit(1)
 
    # 校验核心配置项
    must_have = ["app_id", "app_secret", "weather_key", "template_id", "user", "region", "love_date"]
    for key in must_have:
        if key not in config:
            print(f"配置文件缺失关键项：{key}")
            os.system("pause")
            sys.exit(1)
 
    # 获取accessToken
    accessToken = get_access_token()
    # 接收的用户
    users = config["user"]
    if not isinstance(users, list) or len(users) == 0:
        print("配置文件中user必须是非空列表")
        os.system("pause")
        sys.exit(1)
    
    # 传入地区获取天气信息
    region = config["region"]
    weather, temp, wind_dir = get_weather(region)
    
    # 处理每日金句
    note_ch = config.get("note_ch", "")
    note_en = config.get("note_en", "")
    if note_ch == "" and note_en == "":
        # 获取词霸每日金句
        note_ch, note_en = get_ciba()
    
    # 公众号推送消息
    for user in users:
        send_message(user, accessToken, region, weather, temp, wind_dir, note_ch, note_en)
    
    os.system("pause")
