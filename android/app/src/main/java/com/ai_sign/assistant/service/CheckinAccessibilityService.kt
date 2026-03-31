package com.ai_sign.assistant.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.ai_sign.assistant.helper.CheckinConfig
import com.ai_sign.assistant.helper.PrefsHelper
import com.ai_sign.assistant.helper.PrefsHelper.popupDismissList
import com.ai_sign.assistant.helper.NotificationHelper
import kotlinx.coroutines.*

/**
 * 核心：无障碍辅助功能服务
 *
 * 工作流程：
 *  1. AlarmManager 触发 → 启动目标打卡 APP
 *  2. 本服务监听到目标 APP 的 Window 事件
 *  3. 自动关闭弹窗 → 查找打卡按钮 → 点击 → 验证成功文字
 *  4. 发送通知结果 → 按 HOME 键回桌面
 *
 * 用户需手动在「设置 → 无障碍 → AiSign 辅助打卡」中开启本服务。
 */
class CheckinAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "CheckinA11y"
        const val ACTION_DO_CHECKIN = "com.ai_sign.assistant.ACTION_DO_CHECKIN"

        /** 当前服务实例（用于外部判断服务是否存活） */
        @Volatile
        var instance: CheckinAccessibilityService? = null
    }

    private val mainHandler = Handler(Looper.getMainLooper())
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    /** 是否处于"等待打卡"状态（由闹钟激活，打卡完成后清除） */
    @Volatile
    private var pendingCheckin = false

    /** 防重复点击：记录最近一次点击时间 */
    private var lastClickTime = 0L

    /** 当前加载的配置（每次触发时从 DataStore 刷新） */
    private var config: CheckinConfig = CheckinConfig()

    // -------------------------------------------------------------------------
    // 生命周期
    // -------------------------------------------------------------------------

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(TAG, "无障碍服务已连接")
    }

    override fun onUnbind(intent: Intent?): Boolean {
        instance = null
        serviceScope.cancel()
        Log.i(TAG, "无障碍服务已断开")
        return super.onUnbind(intent)
    }

    /**
     * 响应外部指令（由 CheckinAlarmReceiver 通过 startService 发送）
     * ACTION_DO_CHECKIN：刷新配置 → 标记待打卡状态 → 拉起目标 APP
     */
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_DO_CHECKIN) {
            serviceScope.launch {
                config = PrefsHelper.getConfig(this@CheckinAccessibilityService)
                if (config.targetPackage.isBlank()) {
                    Log.w(TAG, "目标 APP 包名未配置，跳过打卡")
                    return@launch
                }
                pendingCheckin = true
                Log.i(TAG, "收到打卡指令，准备启动 APP：${config.targetPackage}")
                NotificationHelper.showProgress(this@CheckinAccessibilityService)
                launchTargetApp()
            }
        }
        return START_NOT_STICKY
    }

    // -------------------------------------------------------------------------
    // 无障碍事件回调
    // -------------------------------------------------------------------------

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (!pendingCheckin) return

        val pkg = event.packageName?.toString() ?: return
        if (pkg != config.targetPackage) return

        // 只处理页面切换和内容变化事件
        if (event.eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED &&
            event.eventType != AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) return

        // 防抖：500ms 内不重复处理
        val now = System.currentTimeMillis()
        if (now - lastClickTime < 500) return

        Log.d(TAG, "收到目标 APP 事件，开始处理界面 ...")

        // 延迟 800ms 等待页面渲染完成后再查找按钮
        mainHandler.postDelayed({ handleCheckinPage() }, 800)
    }

    override fun onInterrupt() {
        Log.w(TAG, "无障碍服务中断")
    }

    // -------------------------------------------------------------------------
    // 核心操作逻辑
    // -------------------------------------------------------------------------

    /** 拉起目标打卡 APP */
    private fun launchTargetApp() {
        val pkg = config.targetPackage
        val launchIntent = packageManager.getLaunchIntentForPackage(pkg)
        if (launchIntent == null) {
            Log.e(TAG, "找不到目标 APP：$pkg，请确认包名正确")
            pendingCheckin = false
            NotificationHelper.showResult(this, success = false, msg = "找不到打卡 APP：$pkg")
            return
        }
        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED)
        startActivity(launchIntent)
        Log.i(TAG, "已启动 APP：$pkg")
    }

    /** 处理打卡页面：关闭弹窗 → 找按钮 → 点击 */
    private fun handleCheckinPage() {
        val root = rootInActiveWindow ?: run {
            Log.w(TAG, "无法获取根节点，等待下次事件")
            return
        }

        // 1. 先尝试关闭弹窗
        val dismissed = tryDismissPopups(root)
        if (dismissed) {
            // 关闭弹窗后等待页面稳定
            mainHandler.postDelayed({ handleCheckinPage() }, 600)
            return
        }

        // 2. 查找打卡按钮
        val btnNode = findCheckinButton(root)
        if (btnNode == null) {
            Log.d(TAG, "未找到打卡按钮，等待下次事件")
            return
        }

        // 3. 点击
        performClick(btnNode)
    }

    /** 尝试关闭配置中定义的弹窗，返回是否关闭了弹窗 */
    private fun tryDismissPopups(root: AccessibilityNodeInfo): Boolean {
        for (text in config.popupDismissList()) {
            val nodes = root.findAccessibilityNodeInfosByText(text)
            for (node in nodes) {
                if (node.isClickable && node.isVisibleToUser) {
                    node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                    Log.d(TAG, "关闭弹窗：$text")
                    return true
                }
                // 父节点可能才是可点击的
                val parent = node.parent
                if (parent != null && parent.isClickable && parent.isVisibleToUser) {
                    parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                    Log.d(TAG, "关闭弹窗（父节点）：$text")
                    return true
                }
            }
        }
        return false
    }

    /**
     * 查找打卡按钮
     * 优先级：resource-id > 精确文字 > 模糊文字
     */
    private fun findCheckinButton(root: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        // 方式 1：resource-id（最稳定）
        if (config.buttonResourceId.isNotBlank()) {
            val nodes = root.findAccessibilityNodeInfosByViewId(config.buttonResourceId)
            nodes.firstOrNull { it.isClickable && it.isVisibleToUser }?.let { return it }
        }

        // 方式 2：精确文字匹配
        if (config.buttonText.isNotBlank()) {
            val nodes = root.findAccessibilityNodeInfosByText(config.buttonText)
            // 优先找可点击的
            nodes.firstOrNull { it.isClickable && it.isVisibleToUser }?.let { return it }
            // 找到文字节点后取父节点
            nodes.firstOrNull { it.isVisibleToUser }?.let { node ->
                val parent = node.parent
                if (parent != null && parent.isClickable) return parent
            }
        }

        return null
    }

    /**
     * 执行点击操作
     * 优先使用 ACTION_CLICK，失败时降级为坐标手势点击
     */
    private fun performClick(node: AccessibilityNodeInfo) {
        val now = System.currentTimeMillis()
        lastClickTime = now

        val clicked = node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        if (clicked) {
            Log.i(TAG, "成功点击打卡按钮（ACTION_CLICK）")
        } else {
            // 降级：用坐标手势点击
            val bounds = android.graphics.Rect()
            node.getBoundsInScreen(bounds)
            val cx = bounds.centerX().toFloat()
            val cy = bounds.centerY().toFloat()
            Log.w(TAG, "ACTION_CLICK 失败，使用坐标手势点击 ($cx, $cy)")
            performGestureClick(cx, cy)
        }

        // 点击后等待 2 秒验证结果
        mainHandler.postDelayed({ verifyAndFinish() }, 2000)
    }

    /** 坐标手势点击（当 ACTION_CLICK 无效时的备用方案） */
    private fun performGestureClick(x: Float, y: Float) {
        val path = Path().apply { moveTo(x, y) }
        val stroke = GestureDescription.StrokeDescription(path, 0, 100)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()
        dispatchGesture(gesture, null, null)
    }

    /** 验证打卡结果并收尾 */
    private fun verifyAndFinish() {
        pendingCheckin = false

        val root = rootInActiveWindow
        val successText = config.successText

        val success = if (successText.isBlank() || root == null) {
            // 没有配置验证文字，默认视为成功
            true
        } else {
            root.findAccessibilityNodeInfosByText(successText).isNotEmpty()
        }

        if (success) {
            Log.i(TAG, "打卡成功！")
            NotificationHelper.showResult(this, success = true)
        } else {
            Log.w(TAG, "未检测到成功标志「$successText」，请手动确认")
            NotificationHelper.showResult(this, success = false, msg = "未检测到成功提示，请手动确认")
        }

        // 回到桌面
        if (config.goHomeAfterCheckin) {
            mainHandler.postDelayed({
                performGlobalAction(GLOBAL_ACTION_HOME)
            }, 1000)
        }
    }
}
