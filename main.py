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
from urllib.parse import quote

import requests
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("morning")

# 读取环境变量（提供默认值，避免 KeyError 直接崩溃）
START_DATE = os.getenv("START_DATE", "2022-01-01")
CITY = os.getenv("CITY", "北京")
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

# 天气描述中英文映射（wttr.in 的中文翻译不完整，用此表兜底）
WEATHER_MAP = {
    "sunny": "晴", "clear": "晴",
    "partly cloudy": "局部多云",
    "cloudy": "多云", "overcast": "阴",
    "mist": "薄雾", "fog": "雾", "freezing fog": "冻雾",
    "patchy rain possible": "可能有零星小雨",
    "patchy snow possible": "可能有零星小雪",
    "patchy sleet possible": "可能有零星雨夹雪",
    "patchy freezing drizzle possible": "可能有零星冻毛毛雨",
    "thundery outbreaks possible": "可能有雷阵雨",
    "blowing snow": "吹雪", "blizzard": "暴风雪",
    "freezing drizzle": "冻毛毛雨",
    "light drizzle": "小毛毛雨",
    "patchy light rain": "零星小雨",
    "light rain": "小雨", "moderate rain at times": "间歇中雨",
    "moderate rain": "中雨",
    "heavy rain at times": "间歇大雨",
    "heavy rain": "大雨",
    "light freezing rain": "小冻雨",
    "moderate or heavy freezing rain": "中到大冻雨",
    "light sleet": "小雨夹雪",
    "moderate or heavy sleet": "中到大雨夹雪",
    "patchy light snow": "零星小雪",
    "light snow": "小雪",
    "patchy moderate snow": "零星中雪",
    "moderate snow": "中雪",
    "patchy heavy snow": "零星大雪",
    "heavy snow": "大雪",
    "ice pellets": "冰粒",
    "light rain shower": "小阵雨",
    "moderate or heavy rain shower": "中到大阵雨",
    "torrential rain shower": "暴雨",
    "light sleet showers": "小阵雨夹雪",
    "moderate or heavy sleet showers": "中到大阵雨夹雪",
    "light snow showers": "小阵雪",
    "moderate or heavy snow showers": "中到大阵雪",
    "light showers of ice pellets": "小阵冰粒",
    "moderate or heavy showers of ice pellets": "中到大阵冰粒",
    "patchy light rain with thunder": "零星小雷阵雨",
    "moderate or heavy rain with thunder": "中到大雷阵雨",
    "patchy light snow with thunder": "零星小雷阵雪",
    "moderate or heavy snow with thunder": "中到大雷阵雪",
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
    原项目使用的 autodev.openspeech.cn 已失效（签名无效），
    改用 wttr.in，免费、无需密钥、支持中文。
    """
    try:
        # 对城市名做 URL 编码，防止特殊字符破坏 URL
        url = f"https://wttr.in/{quote(CITY)}?format=j1&lang=zh"
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        current = data["current_condition"][0]
        # wttr.in 在 lang=zh 时会返回 lang_zh 数组，但翻译常不完整
        raw_desc = (current.get("lang_zh", [{}])[0].get("value")
                    or current.get("weatherDesc", [{}])[0].get("value", "未知"))
        # 去掉可能的首尾空白，并用映射表翻译成中文
        weather_desc = WEATHER_MAP.get(raw_desc.strip().lower(), raw_desc.strip())
        temperature = math.floor(float(current.get("temp_C", 0)))
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
