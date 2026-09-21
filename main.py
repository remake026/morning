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

# 固定问候语（可改为环境变量控制）
GREETING = os.getenv("GREETING", "早上好，今天也要开心呀！(≧∇≦)ﾉ")

# 通用请求头（模拟浏览器，避免被部分 API 拒绝）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 彩虹屁文案最大字数限制（超过则丢弃）
MAX_WORD_LEN = 20

# 彩虹屁本地兜底词库（API 失败或文案超长时使用），全部 ≤ 20 字
FALLBACK_WORDS = [
    "你是我所有温柔的来源和归属。",
    "今天也要开心呀，我的小朋友。",
    "喜欢你的每一天，都是晴天。",
    "世界很暗，然后你来了，带着星星和月亮。",
    "你是我枯燥生活里的糖。",
    "所有的美好都与你环环相扣。",
    "见你一眼，万物不及。",
    "你是我余生的欢喜。",
    "你笑起来的样子，是我见过最美的风景。",
    "我喜欢你，像风走了八千里，不问归期。",
    "所有的温柔眷恋都是对你灿若星辰的喜欢。",
    "喜欢你，是心动的感觉，是藏不住的欢喜。",
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
    新增：API 返回文案超过 MAX_WORD_LEN(20) 字则丢弃，改用本地兜底。
    """
    for _ in range(3):  # 最多重试 3 次，而非无限递归
        try:
            res = requests.get("https://api.shadiao.pro/chp",
                               headers=HEADERS, timeout=10)
            if res.status_code == 200:
                text = res.json()["data"]["text"]
                if text and len(text) <= MAX_WORD_LEN:
                    return text
                elif text:
                    log.info("API 文案超过 %d 字，丢弃：%s", MAX_WORD_LEN, text)
        except Exception as e:
            log.warning("彩虹屁 API 调用失败: %s", e)
    # 所有重试失败（或文案均超长）后使用本地兜底文案
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

        # ===== 调试：拉取微信端实际模板内容，确认 TEMPLATE_ID 对应的模板 =====
        try:
            tpl_list = client.template.get_all_private_template()
            tpl_info = None
            for t in tpl_list.get("template_list", []):
                if t.get("template_id") == TEMPLATE_ID.strip():
                    tpl_info = t
                    break
            if tpl_info:
                log.info("[调试] 当前使用的模板标题: %s", tpl_info.get("title"))
                log.info("[调试] 当前使用的模板内容: %s", tpl_info.get("content"))
            else:
                log.error("[调试] 找不到 TEMPLATE_ID=%s 对应的模板！模板列表有 %d 个", TEMPLATE_ID, len(tpl_list.get("template_list", [])))
                for t in tpl_list.get("template_list", []):
                    log.info("[调试] 可选模板: id=%s, title=%s, content=%s", t.get("template_id"), t.get("title"), t.get("content"))
        except Exception as e:
            log.warning("[调试] 拉取模板列表失败: %s", e)
        # ===== 调试结束 =====

        # 数据只获取一次，复用给所有用户
        wea, temperature = get_weather()
        data = {
            # 使用公众号模板消息最常见的标准字段名，需与模板中的变量名一致。
            # 问候语固定为 GREETING，不再根据时间段判断
            "first": {"value": GREETING, "color": "#FF6B6B"},
            "keyword1": {"value": wea, "color": "#173177"},
            "keyword2": {"value": f"{temperature}℃", "color": "#173177"},
            "keyword3": {"value": get_rain_tip(wea), "color": "#4ECDC4"},
            "remark": {"value": get_words(), "color": get_random_color()},
        }
        log.info("推送数据: %s", data)

        # 逐个发送，单个失败不影响其他用户
        for user_id in USER_IDS:
            try:
                res = wm.send_template(user_id, TEMPLATE_ID.strip(), data)
                log.info("推送给 %s 成功: %s", user_id, res)
            except Exception as e:
                log.error("推送给 %s 失败: %s", user_id, e, exc_info=True)
    except Exception as e:
        log.error("推送过程中发生错误: %s", e, exc_info=True)


if __name__ == "__main__":
    main()
