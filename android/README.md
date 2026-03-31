# AiSign Android 辅助打卡 APP

## 技术方案说明

### 核心：无障碍服务（AccessibilityService）

Android 系统提供的**无障碍功能（Accessibility）** 原本设计用于帮助视障/肢障用户操作手机。  
它允许一个 APP **读取其他 APP 的界面元素，并代替用户执行点击操作**，是实现跨 APP 自动化的官方合法方案。

**关键点**：
- 无需 root
- 无需 ADB
- 无需逆向其他 APP
- 用户只需在「系统设置 → 无障碍」中手动开启一次权限

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户配置界面（MainActivity）               │
│  输入：目标APP包名、打卡按钮文字/ID、打卡时间、弹窗处理规则    │
└────────────────────────────┬────────────────────────────────┘
                             │ 保存配置
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 AlarmScheduler（定时调度）                    │
│  基于 AlarmManager.setExactAndAllowWhileIdle                 │
│  Doze 模式下精确触发，每天自动重新注册                        │
└────────────────────────────┬────────────────────────────────┘
                             │ PendingIntent 触发
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              CheckinAlarmReceiver（广播接收器）               │
│  接收闹钟广播 → 通知无障碍服务 → 重新注册明天的闹钟           │
│  也处理开机自启（BOOT_COMPLETED）                             │
└────────────────────────────┬────────────────────────────────┘
                             │ startService(ACTION_DO_CHECKIN)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│         CheckinAccessibilityService（核心服务）               │
│                                                             │
│  1. 启动目标打卡 APP                                         │
│  2. 监听 TYPE_WINDOW_STATE_CHANGED 事件                      │
│  3. 自动关闭弹窗（我知道了/跳过/关闭...）                    │
│  4. 查找打卡按钮（resource-id > text > xpath）               │
│  5. 执行 ACTION_CLICK，失败则降级为坐标手势                   │
│  6. 检测成功文字，发送通知                                    │
│  7. 按 HOME 键回桌面                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
android/
├── app/src/main/
│   ├── AndroidManifest.xml             # 权限声明、服务注册
│   ├── java/com/ai_sign/assistant/
│   │   ├── AiSignApp.kt                # Application 初始化
│   │   ├── helper/
│   │   │   ├── PrefsHelper.kt          # DataStore 配置持久化
│   │   │   ├── AlarmScheduler.kt       # AlarmManager 精确定时
│   │   │   └── NotificationHelper.kt  # 状态通知
│   │   ├── service/
│   │   │   └── CheckinAccessibilityService.kt  # 核心：无障碍自动点击
│   │   ├── receiver/
│   │   │   └── CheckinAlarmReceiver.kt # 闹钟触发 + 开机自启
│   │   └── ui/
│   │       ├── MainActivity.kt         # Jetpack Compose 配置界面
│   │       └── ConfigViewModel.kt      # ViewModel
│   └── res/
│       ├── xml/accessibility_service_config.xml  # 无障碍服务配置
│       └── values/strings.xml
└── gradle/libs.versions.toml           # 依赖版本管理
```

---

## 使用前提

| 条件 | 是否需要 |
|------|---------|
| Root 权限 | ❌ 不需要 |
| ADB 调试 | ❌ 不需要 |
| 开启开发者模式 | ❌ 不需要 |
| 开启无障碍权限 | ✅ 需要（一次性手动操作） |
| Android 版本 | ✅ Android 8.0+（API 26+）|

---

## 构建与安装

### 环境要求

- Android Studio Hedgehog 或更新版本
- JDK 17

### 步骤

```bash
# 1. 用 Android Studio 打开 android/ 目录
# 2. 等待 Gradle Sync 完成
# 3. 连接手机或启动模拟器
# 4. 点击 Run（▶）安装到设备
```

或使用命令行：

```bash
cd android
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

---

## 首次使用

1. **安装 APP** 并打开
2. **填写配置**：
   - 目标 APP 包名（见下方获取方法）
   - 打卡按钮文字（如"打卡"、"签到"）
   - 上班/下班时间
3. **点击「保存配置 & 设置闹钟」**
4. **开启无障碍权限**：点击界面上的「前往开启无障碍权限」按钮，在系统设置中找到「AiSign 辅助打卡」并开启
5. **测试**：点击「立即测试打卡」，观察手机是否自动打开打卡 APP 并完成打卡

### 获取目标 APP 包名

**方式 1（不需要 ADB）**：
- 在手机的「设置 → 应用管理」中找到打卡 APP，查看「应用信息」，包名通常显示在详情页

**方式 2（使用 ADB）**：
```bash
# 打开目标打卡 APP，然后执行：
adb shell dumpsys window | grep mCurrentFocus
# 输出示例：com.example.checkin/com.example.MainActivity
# 包名即斜杠前半部分：com.example.checkin
```

**方式 3**：使用「Package Name Viewer」等工具 APP 查看

### 获取打卡按钮 ID（可选但推荐）

安装「UI Automator Viewer」或使用 Android Studio 的「Layout Inspector」：
1. 打开目标打卡 APP 到打卡页面
2. 用 Layout Inspector 截取界面
3. 点击打卡按钮，查看其 `resource-id` 属性
4. 填入「打卡按钮 ID」字段

---

## 无障碍权限说明

本 APP 使用无障碍权限**仅用于**：
- 读取目标 APP 的界面元素（查找打卡按钮）
- 代替用户点击打卡按钮

不会读取密码、不会上传任何数据、不会操作其他 APP。

---

## 常见问题

**Q：无障碍服务开启后 APP 闪退？**
A：部分手机厂商（如 MIUI、ColorOS）会主动杀死无障碍服务进程，需要在「电池优化」中将本 APP 设为「不优化」。

**Q：闹钟到时间没有触发？**
A：检查系统设置中「精确闹钟」权限是否已授予（Android 12+）。路径：设置 → 应用 → AiSign → 权限 → 闹钟和提醒。

**Q：找不到打卡按钮？**
A：先填写「打卡按钮 ID」（resource-id），这比文字匹配更稳定。也可以用「立即测试打卡」按钮，在手机上观察操作过程。

**Q：手机重启后闹钟消失了？**
A：已处理，本 APP 监听 `BOOT_COMPLETED` 广播，开机后自动重新注册闹钟。但需确保「自启动」权限已授予。
