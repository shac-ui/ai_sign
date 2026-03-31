# ai_sign — 辅助打卡工具

> **免责声明**：本项目仅用于学习 Python 自动化编程，请勿用于违反公司制度的场景。使用本工具产生的一切后果由使用者自行承担。

---

## 技术方案对比

| 方案 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **APP 自动化 Android（推荐）** | uiautomator2 + ADB 控制手机 UI | 支持任意打卡 APP；无需逆向接口；模拟真实操作 | 需要手机 USB 或无线连接电脑 | 最通用，推荐首选 |
| **APP 自动化 iOS** | facebook-wda + tidevice | 支持任意打卡 APP | 需要安装 WebDriverAgent，配置较复杂 | iPhone 用户 |
| **Web 接口（仅限钉钉）** | 携带 Cookie 调用 Web 打卡接口 | 无需手机连接 | 仅限钉钉；Cookie 7 天过期需更新 | 纯钉钉用户 |
| Appium | WebDriver 协议控制手机 | 跨平台统一 API | 配置最复杂，资源占用大 | 已有 Appium 环境时 |

**本项目同时支持 APP 自动化模式和 Web 接口模式，通过 `.env` 中的 `MODE` 切换。**

---

## 项目结构

```
ai_sign/
├── ai_sign/
│   ├── config.py          # 配置管理（支持 app / web 两种模式）
│   ├── app_automation.py  # APP 自动化核心（Android + iOS）
│   ├── checkin.py         # Web 接口打卡（仅钉钉）
│   ├── scheduler.py       # APScheduler 定时调度
│   ├── auth.py            # Web 模式 Cookie 鉴权
│   ├── notify.py          # Server 酱微信推送
│   └── logger.py          # 日志模块
├── tools/
│   └── inspect_app.py     # 元素定位辅助工具
├── main.py                # 程序入口
├── requirements.txt
└── .env.example           # 配置模板
```

---

## 快速开始（APP 自动化模式）

### 第一步：安装基础依赖

```bash
python -m venv .venv
source .venv/bin/activate   # Windows：.venv\Scripts\activate
pip install APScheduler python-dotenv loguru httpx
```

### 第二步：根据手机平台安装自动化库

**Android（推荐）：**

```bash
pip install uiautomator2
# 首次使用：向手机推送自动化 agent（手机需开启 USB 调试并连接电脑）
python -m uiautomator2 init
```

手机准备：
1. 设置 → 关于手机 → 连续点击「版本号」7 次，开启开发者模式
2. 设置 → 开发者选项 → 开启「USB 调试」
3. 用数据线连接电脑，在手机上点击「允许调试」
4. 验证连接：`adb devices`（能看到设备 serial 即成功）

> **无线连接（不用数据线）**：在同一 Wi-Fi 下，执行 `adb tcpip 5555`，然后 `adb connect <手机IP>:5555`

**iOS：**

```bash
pip install facebook-wda "tidevice[openssl]"
# 启动 WDA 代理（每次打卡前需确保此进程在运行）
tidevice wdaproxy -B com.facebook.wda.WebDriverAgent.Runner --port 8100
```

### 第三步：获取目标打卡 APP 的包名

**Android：**

```bash
# 先打开目标打卡 APP，然后执行：
adb shell dumpsys window | grep mCurrentFocus
# 输出示例：mCurrentFocus=Window{... com.example.checkin/com.example.MainActivity}
# APP_PACKAGE = com.example.checkin
# APP_ACTIVITY = com.example.MainActivity（可选）
```

**iOS：**

```bash
tidevice applist | grep 打卡
# 输出示例：com.example.checkin  某某打卡
# APP_BUNDLE_ID = com.example.checkin
```

### 第四步：找到打卡按钮的定位方式

打开目标 APP 并导航到打卡页面，运行元素定位工具：

```bash
python main.py --inspect
# iOS：APP_PLATFORM=ios python main.py --inspect
```

工具会：
- 保存截图 `screenshot.png`（肉眼确认当前页面）
- 打印所有可点击元素的 `text` 和 `resource-id`

输出示例：
```
[3]
  文字（APP_CHECKIN_TEXT）：打卡
  resource-id（APP_CHECKIN_RESOURCE_ID）：com.example.checkin:id/btn_punch
  位置：[120,800][360,900]
```

### 第五步：填写配置文件

```bash
cp .env.example .env
```

最小配置示例（Android 打卡 APP）：

```ini
MODE=app
APP_PLATFORM=android
APP_PACKAGE=com.example.checkin        # 第三步获取
APP_CHECKIN_TEXT=打卡                  # 第四步获取
APP_SUCCESS_TEXT=打卡成功
APP_POPUP_DISMISS=我知道了,跳过,关闭

CHECKIN_CRON=0 9 * * 1-5
CHECKOUT_CRON=0 18 * * 1-5
RANDOM_DELAY_MAX=300
```

### 第六步：测试打卡

```bash
# 手动触发一次上班打卡（测试配置是否正确）
python main.py --once on

# 确认无误后启动定时调度器
python main.py
```

---

## 定时调度说明

调度器每天按 cron 时间触发打卡，并在触发后随机等待 `RANDOM_DELAY_MIN`～`RANDOM_DELAY_MAX` 秒再实际操作，避免每天精确到秒的规律性打卡。

| cron 示例 | 含义 |
|-----------|------|
| `0 9 * * 1-5` | 周一至周五 09:00 |
| `30 8 * * 1-5` | 周一至周五 08:30 |
| `0 9 * * 1-6` | 周一至周六 09:00 |

---

## 部署到服务器（让手机 24 小时自动打卡）

### 方案：电脑/树莓派 + 手机无线 ADB

```
手机（Wi-Fi） ←无线ADB→ 树莓派/Mac Mini（运行 main.py）
```

1. 手机和电脑连同一 Wi-Fi
2. `adb tcpip 5555 && adb connect <手机IP>:5555`
3. 将手机IP写入 `.env`：`DEVICE_SERIAL=<手机IP>:5555`
4. 在电脑上运行调度器：`nohup python main.py &`

### systemd 服务（Linux）

```ini
[Unit]
Description=辅助打卡服务
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/ai_sign
ExecStart=/path/to/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 常见问题

**Q：`adb devices` 看不到设备？**
A：确认手机开启了 USB 调试，并在弹窗中点击「允许」。某些品牌还需关闭「MIUI 优化」或允许「USB 安装」。

**Q：找不到打卡按钮？**
A：运行 `python main.py --inspect`，查看截图确认当前页面是否是打卡页，然后根据输出的元素列表修改 `APP_CHECKIN_TEXT` 或 `APP_CHECKIN_RESOURCE_ID`。

**Q：打卡 APP 每次启动都显示广告/弹窗？**
A：将弹窗上的按钮文字加入 `APP_POPUP_DISMISS`，例如 `APP_POPUP_DISMISS=我知道了,跳过`。

**Q：需要打卡两次（上班+下班），但打卡按钮一样？**
A：两次打卡调用的是同一个函数，APP 内部会根据时间自动区分上班/下班打卡，无需额外配置。

**Q：Web 模式 Cookie 失效（401/302）？**
A：重新打开 [attend.dingtalk.com](https://attend.dingtalk.com) 登录，更新 `.env` 中的 `DINGTALK_TOKEN`。
