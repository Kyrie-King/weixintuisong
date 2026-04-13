def get_weather(region):
    """改成付费/正式接口 api.qweather.com"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]

    location_id = "101120901"

    # 👉 这里全部改成 api.qweather.com（正式版接口）
    now_url = f"https://api.qweather.com/v7/weather/now?location={location_id}&key={key}"
    daily_url = f"https://api.qweather.com/v7/weather/3d?location={location_id}&key={key}"
    astro_url = f"https://api.qweather.com/v7/astronomy/sun?location={location_id}&date={date.today().strftime('%Y%m%d')}&key={key}"

    weather = "获取失败"
    temp = "获取失败"
    wind_dir = "获取失败"
    min_temp = "获取失败"
    max_temp = "获取失败"
    sunrise = "获取失败"
    sunset = "获取失败"

    try:
        resp = requests.get(now_url, headers=headers, timeout=10)
        resp.raise_for_status()
        now_data = resp.json()
        if now_data.get("code") == "200":
            weather = now_data["now"]["text"]
            temp = f"{now_data['now']['temp']}℃"
            wind_dir = now_data["now"]["windDir"]
    except Exception as e:
        print(f"获取实时天气失败：{str(e)}")

    try:
        resp = requests.get(daily_url, headers=headers, timeout=10)
        resp.raise_for_status()
        daily_data = resp.json()
        if daily_data.get("code") == "200" and daily_data.get("daily"):
            today_daily = daily_data["daily"][0]
            min_temp = f"{today_daily['tempMin']}℃"
            max_temp = f"{today_daily['tempMax']}℃"
    except Exception as e:
        print(f"获取高低温失败：{str(e)}")

    try:
        resp = requests.get(astro_url, headers=headers, timeout=10)
        resp.raise_for_status()
        astro_data = resp.json()
        if astro_data.get("code") == "200" and astro_data.get("sun"):
            sunrise = astro_data["sun"][0]["rise"]
            sunset = astro_data["sun"][0]["set"]
    except Exception as e:
        print(f"获取日出日落失败：{str(e)}")

    return weather, temp, wind_dir, min_temp, max_temp, sunrise, sunset
