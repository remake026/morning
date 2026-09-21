

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [效果预览](#效果预览)
- [技术栈](#技术栈)
- [目录结构](#目录结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [GitHub Actions 自动运行](#github-actions-自动运行)
- [Docker 部署](#docker-部署)
- [本地定时任务](#本地定时任务)
- [常见问题](#常见问题)
- [开发指南](#开发指南)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [致谢](#致谢)

---

## 项目简介

`Morning` 是一个用于每日定时推送信息的自动化项目。它可以在指定时间自动收集天气、温度、空气质量、每日一句、纪念日倒计时等内容，并通过微信、企业微信、钉钉、飞书、邮件等渠道发送给你或你的朋友。

项目适合以下场景：

- 每天早上给女朋友 / 男朋友发送早安问候
- 每天给自己推送天气和待办提醒
- 通过 GitHub Actions 零服务器定时运行
- 作为学习定时任务、API 调用、消息推送的练手项目
- 通过 Docker 部署到自己的服务器或 NAS

---

## 功能特性

- [x] 每日定时推送
- [x] 实时天气查询
- [x] 温度、湿度、风力、空气质量
- [x] 穿衣建议 / 出行提醒
- [x] 每日一句 / 毒鸡汤 / 土味情话
- [x] 纪念日、生日、恋爱天数倒计时
- [x] 支持企业微信机器人
- [x] 支持钉钉机器人
- [x] 支持飞书机器人
- [x] 支持邮件推送
- [x] 支持 GitHub Actions 自动运行
- [x] 支持 Docker 部署
- [x] 支持环境变量配置
- [x] 支持本地调试和 DRY_RUN 模式

---

## 效果预览

> 可在此处放置推送效果截图。

```text
早安，宝贝！

今天是 2026 年 09 月 21 日，星期一
我们在一起已经 1024 天啦 ❤️

📍 城市：成都
🌤 天气：多云
🌡 温度：22℃ ~ 28℃
💨 风力：东北风 2 级
😷 空气质量：优

👕 穿衣建议：
天气舒适，建议穿薄外套、长裤。

💬 每日一句：
愿你今天拥有一个温柔的早晨。

距离你的生日还有 30 天。
```

---

## 技术栈

根据实际项目替换：

- Python 3.11+
- requests
- python-dotenv
- GitHub Actions
- Docker
- 第三方 API：
  - 和风天气 / OpenWeatherMap
  - 韩小韩 API / One 一个 / 金山词霸
  - 企业微信 / 钉钉 / 飞书 Webhook

---

## 目录结构

```text
morning/
├── .github/
│   └── workflows/
│       └── morning.yml          # GitHub Actions 定时任务
├── src/
│   ├── main.py                  # 程序入口
│   ├── config.py                # 配置加载
│   ├── services/
│   │   ├── weather.py           # 天气服务
│   │   ├── quote.py             # 每日一句服务
│   │   ├── anniversary.py       # 纪念日计算
│   │   └── notify.py            # 消息推送
│   └── utils/
│       ├── logger.py            # 日志工具
│       └── helpers.py           # 通用工具
├── tests/
│   └── test_main.py
├── .env.example                 # 环境变量示例
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── LICENSE
└── README.md
```

> 如果你的项目是 Node.js、Go、Java 等，请把 `src/`、`requirements.txt`、`main.py` 替换为实际结构。

---

## 环境要求

- Python >= 3.11
- pip >= 23
- Git
- 可选：Docker >= 24
- 可选：Docker Compose >= 2

检查环境：

```bash
python --version
pip --version
git --version
```

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/remake026/morning.git
cd morning
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

激活虚拟环境：

macOS / Linux：

```bash
source .venv/bin/activate
```

Windows：

```bash
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env`，填写你的 API Key、城市、推送地址等信息：

```env
TZ=Asia/Shanghai
CITY=成都
WEATHER_API_KEY=your_weather_api_key
PUSH_CHANNEL=wechat
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxx
START_DATE=2023-01-01
LOVE_NAME=宝贝
DRY_RUN=true
```

### 5. 本地运行

```bash
python src/main.py
```

如果 `DRY_RUN=true`，程序只会打印推送内容，不会真正发送消息。

确认无误后改为：

```env
DRY_RUN=false
```

再次运行：

```bash
python src/main.py
```

---

## 配置说明

| 变量名 | 必填 | 默认值 | 说明 |
|---|---:|---|---|
| `TZ` | 否 | `Asia/Shanghai` | 时区 |
| `CITY` | 是 | - | 城市名称或城市代码 |
| `WEATHER_API_KEY` | 是 | - | 天气 API Key |
| `PUSH_CHANNEL` | 是 | `wechat` | 推送渠道：`wechat` / `dingtalk` / `feishu` / `email` |
| `WEBHOOK_URL` | 是 | - | 机器人 Webhook 地址 |
| `START_DATE` | 否 | - | 纪念日开始日期，格式：`YYYY-MM-DD` |
| `LOVE_NAME` | 否 | `亲爱的` | 对方昵称 |
| `BIRTHDAY` | 否 | - | 生日日期，格式：`MM-DD` 或 `YYYY-MM-DD` |
| `DRY_RUN` | 否 | `false` | 是否只打印不发送 |
| `LOG_LEVEL` | 否 | `INFO` | 日志等级：`DEBUG` / `INFO` / `WARNING` / `ERROR` |

### 企业微信机器人示例

```env
PUSH_CHANNEL=wechat
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
```

### 钉钉机器人示例

```env
PUSH_CHANNEL=dingtalk
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=你的token
```

### 飞书机器人示例

```env
PUSH_CHANNEL=feishu
WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的token
```

---

## GitHub Actions 自动运行

项目可以通过 GitHub Actions 每天定时运行，无需自己的服务器。

### 1. 创建 Workflow

文件位置：

```text
.github/workflows/morning.yml
```

内容示例：

```yaml
name: Morning Push

on:
  schedule:
    # UTC 时间，北京时间 06:00 = UTC 22:00
    - cron: '0 22 * * *'
  workflow_dispatch:

jobs:
  morning:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Morning
        env:
          TZ: Asia/Shanghai
          CITY: ${{ secrets.CITY }}
          WEATHER_API_KEY: ${{ secrets.WEATHER_API_KEY }}
          PUSH_CHANNEL: ${{ secrets.PUSH_CHANNEL }}
          WEBHOOK_URL: ${{ secrets.WEBHOOK_URL }}
          START_DATE: ${{ secrets.START_DATE }}
          LOVE_NAME: ${{ secrets.LOVE_NAME }}
          DRY_RUN: false
        run: python src/main.py
```

### 2. 配置 Secrets

进入 GitHub 仓库：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

依次添加：

- `CITY`
- `WEATHER_API_KEY`
- `PUSH_CHANNEL`
- `WEBHOOK_URL`
- `START_DATE`
- `LOVE_NAME`

### 3. 手动测试

进入：

```text
Actions -> Morning Push -> Run workflow
```

确认能否正常收到推送。

> 注意：GitHub Actions 的定时任务使用 UTC 时间。北京时间 06:00 对应 UTC 22:00，也就是前一天。  
> 例如：`0 22 * * *` 表示每天北京时间 06:00 运行。

---

## Docker 部署

### 1. 构建镜像

```bash
docker build -t morning .
```

### 2. 运行容器

```bash
docker run -d \
  --name morning \
  --env-file .env \
  --restart unless-stopped \
  morning
```

### 3. 使用 Docker Compose

`docker-compose.yml` 示例：

```yaml
version: "3.8"

services:
  morning:
    build: .
    container_name: morning
    env_file:
      - .env
    restart: unless-stopped
```

启动：

```bash
docker compose up -d
```

查看日志：

```bash
docker logs -f morning
```

停止：

```bash
docker compose down
```

---

## 本地定时任务

如果不使用 GitHub Actions 或 Docker，可以用系统定时任务。

### Linux / macOS：crontab

编辑定时任务：

```bash
crontab -e
```

添加：

```cron
0 6 * * * cd /path/to/morning && /path/to/morning/.venv/bin/python src/main.py >> /tmp/morning.log 2>&1
```

表示每天 06:00 运行。

### Windows：任务计划程序

1. 打开“任务计划程序”
2. 创建基本任务
3. 设置每天触发时间
4. 操作选择“启动程序”
5. 程序或脚本选择 Python 路径
6. 添加参数：`src/main.py`
7. 起始于：项目目录

---

## 常见问题

### 1. 没有收到推送怎么办？

检查顺序：

1. `DRY_RUN` 是否为 `false`
2. `WEBHOOK_URL` 是否正确
3. 机器人是否被限流或禁用
4. GitHub Actions 是否执行成功
5. 日志中是否有报错
6. 网络能否访问第三方 API

### 2. GitHub Actions 没有按时运行？

GitHub Actions 的定时任务可能延迟，通常几分钟内正常。  
另外请确认 cron 使用的是 UTC 时间。

### 3. 天气接口报错？

可能原因：

- API Key 过期
- 免费额度用完
- 城市名不匹配
- 接口临时不可用

可以增加重试逻辑或更换天气 API。

### 4. 如何修改推送时间？

修改 `.github/workflows/morning.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    - cron: '0 22 * * *'
```

改为你需要的 UTC 时间。

### 5. 如何本地调试而不发送消息？

设置：

```env
DRY_RUN=true
```

然后运行：

```bash
python src/main.py
```

---

## 开发指南

### 安装开发依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black .
isort .
flake8 .
```

### 提交前检查

```bash
pytest
black --check .
isort --check-only .
flake8 .
```

---

## 贡献指南

欢迎提交 Issue 和 Pull Request。

贡献流程：

1. Fork 本仓库
2. 创建分支：

```bash
git checkout -b feature/your-feature
```

3. 提交修改：

```bash
git commit -m "feat: add your feature"
```

4. 推送分支：

```bash
git push origin feature/your-feature
```

5. 创建 Pull Request

请确保：

- 代码风格统一
- 新功能附带测试
- README 同步更新
- 不提交真实 API Key、Webhook、密码等敏感信息

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

你可以自由使用、修改、分发，但请保留原始许可证声明。

---

## 致谢

感谢以下项目和服务的支持：

- [GitHub Actions](https://github.com/features/actions)
- [和风天气](https://www.qweather.com/)
- [One 一个](https://one.hitokoto.cn/)
- [企业微信](https://work.weixin.qq.com/)
- [钉钉](https://www.dingtalk.com/)
- [飞书](https://www.feishu.cn/)

---

## 联系作者

- GitHub：[@remake026](https://github.com/remake026)
- 仓库：[remake026/morning](https://github.com/remake026/morning)

如果这个项目对你有帮助，欢迎点一个 Star ⭐️。
