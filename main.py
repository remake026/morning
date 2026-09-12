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
    "愿你眼里有光，心中有爱，目光所及皆是美好。",
    "你笑起来的样子，是我见过最美的风景。",
    "想把世界上最好的都给你，却发现世界上最好的就是你。",
    "你是我漫漫长夜里的那颗星，照亮我所有的路。",
    "往后余生，风雪是你，平淡是你，清贫是你，荣华是你。",
    "我喜欢你，像风走了八千里，不问归期。",
    "愿你三冬暖，愿你春不寒，愿你天黑有灯，下雨有伞。",
    "你是我藏在云层里的月亮，也是我穷极一生寻找的宝藏。",
    "所有的温柔眷恋都是对你灿若星辰的喜欢。",
    "你是我纸短情长的雨季，也是我往后余生的晴空万里。",
    "喜欢你，是心动的感觉，是藏不住的欢喜。",
    "愿你被这个世界温柔以待，愿所有美好都如期而至。",
    "你是我心头的朱砂痣，也是我窗前的白月光。",
    "山水一程，三生有幸，遇见你真好。",
    "我想和你一起，把日子过成诗。",
    "你的名字，是我见过最短的情诗。",
]


# 下雨提醒语（天气含"雨"时随机选一条）
RAIN_TIPS = [
    "今天有雨，出门记得带伞哦～",
    "外面下雨啦，别淋雨，会感冒的。",
    "今天下雨，路上注意安全，慢点走。",
    "雨天路滑，开车骑车都要小心呀。",
    "下雨了，记得带伞，别让自己淋湿了。",
]

# 不下雨的温馨提醒
SUNNY_TIPS = [
    "今天不下雨，可以放心出门啦～",
    "今天天气不错，适合出去走走。",
    "无雨的一天，也要开开心心的哦。",
    "今天没雨，记得防晒呀。",
]


def get_greeting():
    """根据当前时间返回时段问候语"""
    hour = datetime.now().hour
    if 5 <= hour < 9:
        return random.choice([
            "早上好呀，新的一天开始啦～",
            "早安，今天也要元气满满哦！",
            "起床啦，美好的一天从现在开始。",
        ])
    elif 9 <= hour < 12:
        return random.choice([
            "上午好，记得吃早餐哦～",
            "上午好呀，今天也要加油！",
        ])
    elif 12 <= hour < 14:
        return random.choice([
            "中午好，该吃饭啦～",
            "午安，记得午休一下哦。",
        ])
    elif 14 <= hour < 18:
        return random.choice([
            "下午好，困了就喝杯咖啡吧～",
            "下午好呀，再坚持一下就下班啦。",
        ])
    elif 18 <= hour < 22:
        return random.choice([
            "晚上好，今天辛苦啦～",
            "晚上好，记得吃晚饭哦。",
        ])
    else:
        return random.choice([
            "夜深了，早点休息呀～",
            "晚安，做个好梦。",
        ])


def get_rain_tip(weather):
    """根据天气描述返回下雨提醒"""
    if "雨" in weather:
        return random.choice(RAIN_TIPS)
    return random.choice(SUNNY_TIPS)


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
            "greeting": {"value": get_greeting(), "color": "#FF6B6B"},
            "weather": {"value": wea},
            "temperature": {"value": temperature},
            "rain_tip": {"value": get_rain_tip(wea), "color": "#4ECDC4"},
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
