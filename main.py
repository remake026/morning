# -*- coding: utf-8 -*-
"""
每日早安推送 - 给女朋友的微信模板消息
修复版：解决原项目 API 失效、无限递归、无错误处理等问题
"""
import os
import random
import math
import logging
from datetime import date, datetime

import requests
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("morning")

# 读取环境变量（提供默认值，避免 KeyError 直接崩溃）
START_DATE = os.getenv("START_DATE", "2022-01-01")
CITY = os.getenv("CITY", "绵阳,510703")
BIRTHDAY = os.getenv("BIRTHDAY", "01-01")
APP_ID = os.getenv("APP_ID", "")
APP_SECRET = os.getenv("APP_SECRET", "")
# USER_ID 支持多个 openid，用英文逗号分隔，例如：openid1,openid2,openid3
USER_IDS = [uid.strip() for uid in os.getenv("USER_ID", "").split(",") if uid.strip()]
TEMPLATE_ID = os.getenv("TEMPLATE_ID", "")

# 通用请求头（模拟浏览器，避免被部分 API 拒绝）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 彩虹屁本地兜底词库（API 失败时使用）
FALLBACK_WORDS = [
    "你是我所有温柔的来源和归属。",
    "今天也要开心呀，我的小朋友。",
    "喜欢你的每一天，都是晴天。",
    "世界很暗，然后你来了，带着星星和月亮。",
    "你是我枯燥生活里的糖。",
    "所有的美好都与你环环相扣。",
    "见你一眼，万物不及。",
    "你是我余生的欢喜。",
]


def get_weather():
    """
    获取天气信息。
    使用 uapis.cn 免费天气 API，直接返回中文、精确到区县。
    CITY 环境变量支持两种格式：
      - 纯城市名：绵阳
      - 城市名,adcode：绵阳,510703（adcode 更精确，可定位到区县）
    """
    try:
        # 解析 CITY，支持 "城市名" 或 "城市名,adcode"
        parts = [p.strip() for p in CITY.split(",")]
        city_name = parts[0]
        params = {"city": city_name}
        if len(parts) > 1 and parts[1]:
            params["adcode"] = parts[1]

        url = "https://uapis.cn/api/v1/misc/weather"
        res = requests.get(url, params=params, headers=HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        weather_desc = data.get("weather", "未知")
        temperature = math.floor(float(data.get("temperature", 0)))
        return weather_desc, temperature
    except Exception as e:
        log.warning("获取天气失败，使用默认值: %s", e)
        return "未知", 0


def get_count():
    """计算在一起的天数"""
    try:
        delta = datetime.now() - datetime.strptime(START_DATE, "%Y-%m-%d")
        return delta.days
    except ValueError as e:
        log.error("START_DATE 格式错误，应为 YYYY-MM-DD: %s", e)
        return 0


def get_birthday():
    """计算距离下次生日的天数，处理 2 月 29 日闰年问题"""
    try:
        today = date.today()
        # BIRTHDAY 格式: MM-DD
        month, day = (int(x) for x in BIRTHDAY.split("-"))
        # 处理 2 月 29 日：非闰年时顺延到 2 月 28 日
        try:
            next_birthday = date(today.year, month, day)
        except ValueError:
            next_birthday = date(today.year, 2, 28)
        if next_birthday < today:
            try:
                next_birthday = date(today.year + 1, month, day)
            except ValueError:
                next_birthday = date(today.year + 1, 2, 28)
        return (next_birthday - today).days
    except Exception as e:
        log.error("计算生日失败: %s", e)
        return 0


def get_words():
    """
    获取彩虹屁文案。
    修复原项目的无限递归 Bug：原代码在 API 失败时递归调用自身，
    若 API 持续失败会导致栈溢出。改为有限次重试 + 本地兜底。
    """
    for _ in range(3):  # 最多重试 3 次，而非无限递归
        try:
            res = requests.get("https://api.shadiao.pro/chp",
                               headers=HEADERS, timeout=10)
            if res.status_code == 200:
                text = res.json()["data"]["text"]
                if text:
                    return text
        except Exception as e:
            log.warning("彩虹屁 API 调用失败: %s", e)
    # 所有重试失败后使用本地兜底文案
    log.info("使用本地兜底文案")
    return random.choice(FALLBACK_WORDS)


def get_random_color():
    """生成随机十六进制颜色"""
    return "#%06x" % random.randint(0, 0xFFFFFF)


def main():
    # 关键配置校验
    if not all([APP_ID, APP_SECRET, TEMPLATE_ID]):
        log.error("缺少必要配置：APP_ID / APP_SECRET / TEMPLATE_ID")
        return
    if not USER_IDS:
        log.error("缺少必要配置：USER_ID（请填写至少一个 openid，多个用逗号分隔）")
        return

    try:
        client = WeChatClient(APP_ID, APP_SECRET)
        wm = WeChatMessage(client)

        # 数据只获取一次，复用给所有用户
        wea, temperature = get_weather()
        data = {
            "weather": {"value": wea},
            "temperature": {"value": temperature},
            "love_days": {"value": get_count()},
            "birthday_left": {"value": get_birthday()},
            "words": {"value": get_words(), "color": get_random_color()},
        }
        log.info("推送数据: %s", data)

        # 逐个发送，单个失败不影响其他用户
        for user_id in USER_IDS:
            try:
                res = wm.send_template(user_id, TEMPLATE_ID, data)
                log.info("推送给 %s 成功: %s", user_id, res)
            except Exception as e:
                log.error("推送给 %s 失败: %s", user_id, e, exc_info=True)
    except Exception as e:
        log.error("推送过程中发生错误: %s", e, exc_info=True)


if __name__ == "__main__":
    main()
