# -*- coding: utf-8 -*-
"""
晚睡提醒 - 微信模板消息定时推送
精简版：随机发送静态晚安文案，无天气、生日等额外字段
"""
import os
import random
import logging

from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("goodnight")

# 读取环境变量（注意这里改成了 GOODNIGHT_TEMPLATE_ID）
APP_ID = os.getenv("APP_ID", "")
APP_SECRET = os.getenv("APP_SECRET", "")
TEMPLATE_ID = os.getenv("GOODNIGHT_TEMPLATE_ID", "")
USER_IDS = [uid.strip() for uid in os.getenv("USER_ID", "").split(",") if uid.strip()]

# 静态晚安文案库（每条不超过 20 字）
GOODNIGHT_MESSAGES = [
    "不早了，早点休息，晚安。",
    "夜深了，放下手机，做个好梦。",
    "今天辛苦啦，快睡吧，晚安。",
    "愿你一夜好梦，明天见。",
    "晚安，愿你梦里有星辰大海。",
    "早点睡，别熬夜，晚安。",
    "夜深了，盖好被子，晚安。",
    "晚安，明天也要元气满满哦。",
    "放下烦恼，安心入睡，晚安。",
    "愿你被世界温柔以待，晚安。",
    "晚安，好梦，明天会更好。",
    "夜深人静，早点休息吧。",
    "晚安，记得梦到我哦。",
    "今天也辛苦啦，晚安。",
    "愿长夜无梦，一夜安眠。",
    "晚安，明天又是新的一天。",
    "早点休息，别让我担心。",
    "晚安，愿你睡个好觉。",
    "夜深了，快睡吧，明天见。",
    "晚安，好梦，一切顺利。",
]


def main():
    """主函数：校验配置、随机选文案、逐个发送"""
    if not all([APP_ID, APP_SECRET, TEMPLATE_ID]):
        log.error("缺少必要配置：APP_ID / APP_SECRET / GOODNIGHT_TEMPLATE_ID")
        return
    if not USER_IDS:
        log.error("缺少必要配置：USER_ID")
        return

    try:
        client = WeChatClient(APP_ID, APP_SECRET)
        wm = WeChatMessage(client)
    except Exception as e:
        log.error("初始化微信客户端失败: %s", e, exc_info=True)
        return

    message = random.choice(GOODNIGHT_MESSAGES)
    log.info("本次推送文案: %s", message)

    data = {
        "first": {"value": message, "color": "#173177"},
    }

    for user_id in USER_IDS:
        try:
            res = wm.send_template(user_id, TEMPLATE_ID.strip(), data)
            log.info("推送给 %s 成功: %s", user_id, res)
        except Exception as e:
            log.error("推送给 %s 失败: %s", user_id, e, exc_info=True)


if __name__ == "__main__":
    main()
