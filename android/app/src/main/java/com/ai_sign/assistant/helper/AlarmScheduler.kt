package com.ai_sign.assistant.helper

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import com.ai_sign.assistant.receiver.CheckinAlarmReceiver
import java.util.Calendar

/**
 * AlarmManager 定时调度封装
 *
 * 为什么用 AlarmManager 而不是 WorkManager？
 *  - WorkManager 用于可延迟的后台任务，精确时间无法保证
 *  - AlarmManager.setExactAndAllowWhileIdle 在 Doze 模式下仍可精确触发
 *  - 打卡需要精确到分钟，AlarmManager 是正确选择
 */
object AlarmScheduler {

    private const val TAG = "AlarmScheduler"

    // 两个独立的 requestCode，区分上班和下班闹钟
    const val REQUEST_CHECKIN  = 1001
    const val REQUEST_CHECKOUT = 1002

    const val EXTRA_TYPE = "checkin_type"
    const val TYPE_CHECKIN  = "OnDuty"
    const val TYPE_CHECKOUT = "OffDuty"

    /**
     * 设置下一次上班打卡闹钟
     * @param timeStr "HH:mm" 格式
     * @param randomDelaySeconds 随机延迟最大秒数
     */
    fun scheduleCheckin(context: Context, timeStr: String, randomDelaySeconds: Int = 0) {
        schedule(context, timeStr, REQUEST_CHECKIN, TYPE_CHECKIN, randomDelaySeconds)
    }

    /**
     * 设置下一次下班打卡闹钟
     */
    fun scheduleCheckout(context: Context, timeStr: String, randomDelaySeconds: Int = 0) {
        schedule(context, timeStr, REQUEST_CHECKOUT, TYPE_CHECKOUT, randomDelaySeconds)
    }

    /**
     * 设置两个闹钟（保存配置后统一调用）
     */
    fun scheduleAll(context: Context, config: CheckinConfig) {
        if (config.checkinEnabled && config.targetPackage.isNotBlank()) {
            scheduleCheckin(context, config.checkinTime, config.randomDelaySeconds)
        } else {
            cancel(context, REQUEST_CHECKIN)
        }
        if (config.checkoutEnabled && config.targetPackage.isNotBlank()) {
            scheduleCheckout(context, config.checkoutTime, config.randomDelaySeconds)
        } else {
            cancel(context, REQUEST_CHECKOUT)
        }
    }

    /** 取消全部闹钟 */
    fun cancelAll(context: Context) {
        cancel(context, REQUEST_CHECKIN)
        cancel(context, REQUEST_CHECKOUT)
    }

    // -------------------------------------------------------------------------

    private fun schedule(
        context: Context,
        timeStr: String,
        requestCode: Int,
        type: String,
        randomDelaySeconds: Int,
    ) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

        // 检查精确闹钟权限（Android 12+）
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (!alarmManager.canScheduleExactAlarms()) {
                Log.w(TAG, "没有精确闹钟权限，请在设置中开启「精确闹钟」权限")
                return
            }
        }

        val triggerAt = nextTriggerMillis(timeStr, randomDelaySeconds)
        val pendingIntent = buildPendingIntent(context, requestCode, type)

        // setExactAndAllowWhileIdle：即使在 Doze 省电模式下也能精确触发
        alarmManager.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            triggerAt,
            pendingIntent,
        )

        val label = if (type == TYPE_CHECKIN) "上班打卡" else "下班打卡"
        Log.i(TAG, "$label 闹钟已设置：$timeStr（随机延迟 0~${randomDelaySeconds}s），下次触发：${java.util.Date(triggerAt)}")
    }

    private fun cancel(context: Context, requestCode: Int) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        alarmManager.cancel(buildPendingIntent(context, requestCode, ""))
        Log.i(TAG, "闹钟已取消，requestCode=$requestCode")
    }

    /**
     * 计算下一次触发的毫秒时间戳
     * - 今天对应时刻还没到 → 今天触发
     * - 今天对应时刻已过   → 明天同一时刻触发
     * - 加上随机延迟
     */
    private fun nextTriggerMillis(timeStr: String, randomDelaySeconds: Int): Long {
        val parts = timeStr.split(":")
        val hour   = parts.getOrNull(0)?.toIntOrNull() ?: 9
        val minute = parts.getOrNull(1)?.toIntOrNull() ?: 0

        val cal = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, hour)
            set(Calendar.MINUTE, minute)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }

        // 如果设定时间已过，则改为明天
        if (cal.timeInMillis <= System.currentTimeMillis()) {
            cal.add(Calendar.DAY_OF_YEAR, 1)
        }

        // 加随机延迟
        val delayMs = if (randomDelaySeconds > 0) (Math.random() * randomDelaySeconds * 1000).toLong() else 0L
        return cal.timeInMillis + delayMs
    }

    private fun buildPendingIntent(context: Context, requestCode: Int, type: String): PendingIntent {
        val intent = Intent(context, CheckinAlarmReceiver::class.java).apply {
            action = CheckinAlarmReceiver.ACTION_CHECKIN_ALARM
            putExtra(EXTRA_TYPE, type)
        }
        return PendingIntent.getBroadcast(
            context,
            requestCode,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }
}
