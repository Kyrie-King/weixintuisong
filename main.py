def main():
    with open("config.txt", encoding="utf-8") as f:
        config = eval(f.read())

    app_id = config["app_id"]
    app_secret = config["app_secret"]
    template_id = config["template_id"]
    user = config["user"][0]
    love_date = config["love_date"]
    gaode_key = config["gaode_key"]

    access_token = get_access_token(app_id, app_secret)
    today = date.today()
    week = ["日", "一", "二", "三", "四", "五", "六"][today.weekday()]
    date_str = f"{today} 星期{week}"

    # 在一起天数
    try:
        ly, lm, ld = map(int, love_date.split("-"))
        love_days = str((today - date(ly, lm, ld)).days)
    except Exception as e:
        print("❌ 在一起天数计算失败：", e)
        love_days = "获取失败"

    # 天气（已带℃单位）
    weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset = get_weather("371300", gaode_key)

    # 生日文案
    birthday1 = ""
    if "birthday1" in config:
        days = get_birthday(config["birthday1"]["birthday"], today.year, today)
        if days == "0":
            birthday1 = f"今天是{config['birthday1']['name']}生日！"
        else:
            birthday1 = f"距离{config['birthday1']['name']}生日还有{days}天"

    birthday2 = ""
    if "birthday2" in config:
        days = get_birthday(config["birthday2"]["birthday"], today.year, today)
        if days == "0":
            birthday2 = f"今天是{config['birthday2']['name']}生日！"
        else:
            birthday2 = f"距离{config['birthday2']['name']}生日还有{days}天"

    # 情话和脑筋急转弯（固定赋值，避免为空）
    love_word = "我喜欢你，胜于昨日，略匮明朝。"
    riddle_q = "什么门永远关不上？"
    riddle_a = "球门"

    # 推送数据（与模板字段完全对应）
    data = {
        "touser": user,
        "template_id": template_id,
        "url": "https://github.com",
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
            "birthday1": {"value": birthday1, "color": get_color()},
            "birthday2": {"value": birthday2, "color": get_color()},
            "love_word": {"value": love_word, "color": get_color()},
            "riddle_q": {"value": riddle_q, "color": get_color()},
            "riddle_a": {"value": riddle_a, "color": get_color()}
        }
    }

    # 关键：打印完整的推送数据！
    print("===== 推送数据详情 =====")
    print(data)
    print("=======================")

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        print("✅ 推送成功：", resp.json())
    except Exception as e:
        print("❌ 推送失败：", e)
