def get_weather():
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={ADCODE}&key={GAODE_KEY}&extensions=all"
    retry_times = 3
    resp = None
    for i in range(retry_times):
        try:
            resp = requests.get(url, timeout=30, verify=False).json()
            print("高德返回原始数据：",resp)
            if resp.get("status") == "1":
                # 校验必需字段
                if "lives" in resp and "forecasts" in resp:
                    break
            print(f"第{i+1}次请求高德天气接口返回异常，准备重试")
            time.sleep(2)
        except Exception as e:
            print(f"第{i+1}次请求高德超时，正在重试,错误:{e}")
            time.sleep(2)

    # 取消兜底，多次重试失败则终止程序
    if resp is None or resp.get("status") != "1" or "lives" not in resp or "forecasts" not in resp:
        raise RuntimeError("高德天气接口获取失败，已经用尽重试次数，程序终止，请检查高德Key、ADCODE、IP黑名单、每日额度")

    live_info = resp["lives"][0]
    forecast_today = resp["forecasts"][0]["casts"][0]

    observer = ephem.Observer()
    observer.lat, observer.lon = '35.06', '118.33'
    sun = ephem.Sun()
    sunrise = observer.next_rising(sun).datetime().strftime("%H:%M")
    sunset = observer.next_setting(sun).datetime().strftime("%H:%M")

    weather_data = {
        "city": REGION,
        "weather": forecast_today["dayweather"],
        "real_temp": live_info["temperature"],
        "min_temperature": forecast_today["nighttemp"],
        "max_temperature": forecast_today["daytemp"],
        "wind_direction": f"{forecast_today['daywind']}风 {forecast_today['daypower']}级",
        "sunrise": sunrise,
        "sunset": sunset
    }
    # 增加温度校验，防止极端情况下实时温度大于当日最高温
    rt_temp = float(weather_data["real_temp"])
    max_temp = float(weather_data["max_temperature"])
    if rt_temp > max_temp:
        weather_data["max_temperature"] = weather_data["real_temp"]

    return weather_data
