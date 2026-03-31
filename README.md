# ai_sign — 钉钉辅助打卡工具

> **免责声明**：本项目仅用于学习 Python 自动化编程，请勿用于违反公司制度的场景。使用本工具产生的一切后果由使用者自行承担。

---

## 技术选型说明

| 技术 | 版本要求 | 作用 |
|------|---------|------|
| **Python** | ≥ 3.10 | 主语言，生态丰富、跨平台、部署简单 |
| **httpx** | ≥ 0.27 | 模拟钉钉 APP 的 HTTP(S) 打卡请求，支持同步/异步 |
| **APScheduler** | ≥ 3.10 | 基于 cron 表达式的定时调度，精确触发打卡任务 |
| **python-dotenv** | ≥ 1.0 | 从 `.env` 文件加载账号等敏感配置，避免硬编码 |
| **loguru** | ≥ 0.7 | 结构化彩色日志，自动按日滚动，便于排查问题 |

### 为什么选 Python + httpx，而不是其他方案？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Python + httpx**（本项目） | 轻量、无需安装 APP 环境、可运行在服务器/树莓派/NAS | 需要逆向 APP 接口，接口变更需维护 |
| Appium + Android 模拟器 | 真实模拟人工点击，稳定性高 | 资源消耗大（需 GUI），配置复杂 |
| ADB 控制真机 | 直接操作真机，最接近真实操作 | 需要持续保持手机连接 USB |
| 钉钉开放平台 OpenAPI | 官方接口，稳定 | 仅支持企业管理员操作，普通员工无法使用 |

---

## 项目结构

```
ai_sign/
├── ai_sign/
│   ├── __init__.py      # 包入口
│   ├── config.py        # 配置管理（读取 .env）
│   ├── logger.py        # 日志模块
│   ├── auth.py          # 钉钉登录鉴权
│   ├── checkin.py       # 核心打卡逻辑
│   ├── notify.py        # 微信推送通知
│   └── scheduler.py     # APScheduler 定时调度
├── main.py              # 程序入口
├── requirements.txt     # Python 依赖
├── .env.example         # 配置模板
└── .gitignore
```

---

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置账号

```bash
cp .env.example .env
# 用编辑器打开 .env，填入手机号、密码、公司 GPS 坐标等
```

`.env` 配置说明：

```ini
# 账号
DINGTALK_MOBILE=13800138000
DINGTALK_PASSWORD=your_password

# 打卡时间（cron：分 时 日 月 周）
CHECKIN_CRON=0 9 * * 1-5     # 周一到周五 09:00 上班打卡
CHECKOUT_CRON=0 18 * * 1-5   # 周一到周五 18:00 下班打卡

# 公司 GPS 坐标（必须与实际位置一致，否则打卡会显示"异常"）
LOCATION_LATITUDE=39.9042
LOCATION_LONGITUDE=116.4074
LOCATION_ADDRESS=北京市东城区某某大厦

# 打卡前随机等待 0~300 秒（模拟人工操作波动）
RANDOM_DELAY_MIN=0
RANDOM_DELAY_MAX=300

# 可选：Server 酱微信推送 https://sct.ftqq.com/
SERVERCHAN_KEY=
```

### 3. 测试打卡（手动触发）

```bash
# 测试上班打卡
python main.py --once on

# 测试下班打卡
python main.py --once off
```

### 4. 启动定时调度器

```bash
# 前台运行（开发测试）
python main.py

# 后台持久运行（Linux 服务器推荐）
nohup python main.py > /dev/null 2>&1 &

# 或使用 systemd 服务（见下方）
```

---

## 部署到服务器（推荐）

### systemd 服务

创建 `/etc/systemd/system/ai_sign.service`：

```ini
[Unit]
Description=钉钉辅助打卡服务
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/ai_sign
ExecStart=/path/to/ai_sign/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai_sign
sudo systemctl start ai_sign
sudo systemctl status ai_sign
```

### Docker 部署

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
docker build -t ai_sign .
docker run -d --env-file .env --name ai_sign ai_sign
```

---

## 日志查看

日志文件位于 `logs/` 目录，按天滚动，保留 30 天：

```bash
tail -f logs/ai_sign_$(date +%Y-%m-%d).log
```

---

## 常见问题

**Q：打卡后显示"地点异常"？**
A：GPS 坐标必须与公司打卡范围一致，坐标偏差过大会被标记异常。可在手机地图 App 上获取精确坐标。

**Q：登录失败报错 401？**
A：钉钉 APP 端接口可能发生变化，需更新 `auth.py` 中的接口地址和参数。

**Q：能否部署在树莓派/NAS 上？**
A：可以，只需 Python 3.10+ 环境，资源占用极低（内存 < 30MB）。
