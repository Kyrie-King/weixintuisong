def get_weather(region):
    key = config["weather_key"]
    location = region

    # -------------- 实时天气 + 今日预报 --------------
    url = f"https://devapi.qweather.com/v7/weather/3d?location={location}&key={key}"
    res = requests.get(url, timeout=10).json()

    # 接口不正常就返回默认
    if res.get("code") != "200":
        return "晴", "25℃", "东风", "18℃", "28℃", "06:00", "18:00"

    day0 = res["daily"][0]
    weather = day0["textDay"]
    min_temp = day0["tempMin"] + "℃"
    max_temp = day0["tempMax"] + "℃"

    # -------------- 实时风向 --------------
    url_now = f"https://devapi.qweather.com/v7/weather/now?location={location}&key={key}"
    res_now = requests.get(url_now, timeout=10).json()
    wind_dir = res_now["now"]["windDir"] if res_now.get("code") == "200" else "东风"
    temp_now = res_now["now"]["temp"] + "℃"

    # -------------- 日出日落 --------------
    url_sun = f"https://devapi.qweather.com/v7/astronomy/sun?location={location}&date={date.today()}&key={key}"
    res_sun = requests.get(url_sun, timeout=10).json()
    sunrise = "06:00"
    sunset = "18:00"
    if res_sun.get("code") == "200":
        sunrise = res_sun["sunrise"][11:16]  # 只取 HH:MM
        sunset = res_sun["sunset"][11:16]

    return weather, temp_now, wind_dir, min_temp, max_temp, sunrise, sunset
