package com.ai_sign.assistant.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.ai_sign.assistant.helper.AlarmScheduler
import com.ai_sign.assistant.helper.PrefsHelper
import com.ai_sign.assistant.service.CheckinAccessibilityService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * 广播接收器，处理两类事件：
 *
 * 1. 闹钟触发（ACTION_CHECKIN_ALARM）
 *    - 通知无障碍服务执行打卡
 *    - 自动重新设置下一天的同一时间闹钟（实现每日重复）
 *
 * 2. 开机完成（BOOT_COMPLETED）/ APP 更新（MY_PACKAGE_REPLACED）
 *    - 重新注册闹钟（重启/更新后 AlarmManager 的闹钟会被清除）
 */
class CheckinAlarmReceiver : BroadcastReceiver() {

    companion object {
        const val TAG = "AlarmReceiver"
        const val ACTION_CHECKIN_ALARM = "com.ai_sign.assistant.ACTION_CHECKIN_ALARM"
    }

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            ACTION_CHECKIN_ALARM -> handleAlarm(context, intent)
            Intent.ACTION_BOOT_COMPLETED,
            Intent.ACTION_MY_PACKAGE_REPLACED -> handleBoot(context)
        }
    }

    // -------------------------------------------------------------------------

    private fun handleAlarm(context: Context, intent: Intent) {
        val type = intent.getStringExtra(AlarmScheduler.EXTRA_TYPE) ?: AlarmScheduler.TYPE_CHECKIN
        Log.i(TAG, "闹钟触发，类型：$type")

        // 1. 通知无障碍服务开始打卡
        val service = CheckinAccessibilityService.instance
        if (service == null) {
            Log.w(TAG, "无障碍服务未运行，无法自动打卡。请前往「设置 → 无障碍」开启 AiSign 服务。")
            // 仍然设置下一天闹钟
        } else {
            val serviceIntent = Intent(context, CheckinAccessibilityService::class.java).apply {
                action = CheckinAccessibilityService.ACTION_DO_CHECKIN
            }
            context.startService(serviceIntent)
        }

        // 2. 重新设置明天的闹钟（AlarmManager 单次触发，需手动循环）
        rescheduleNext(context, type)
    }

    private fun handleBoot(context: Context) {
        Log.i(TAG, "设备启动，重新注册打卡闹钟 ...")
        // 从 DataStore 读取配置后重新设置闹钟
        CoroutineScope(Dispatchers.IO).launch {
            val config = PrefsHelper.getConfig(context)
            AlarmScheduler.scheduleAll(context, config)
        }
    }

    private fun rescheduleNext(context: Context, type: String) {
        CoroutineScope(Dispatchers.IO).launch {
            val config = PrefsHelper.getConfig(context)
            when (type) {
                AlarmScheduler.TYPE_CHECKIN  ->
                    if (config.checkinEnabled)
                        AlarmScheduler.scheduleCheckin(context, config.checkinTime, config.randomDelaySeconds)
                AlarmScheduler.TYPE_CHECKOUT ->
                    if (config.checkoutEnabled)
                        AlarmScheduler.scheduleCheckout(context, config.checkoutTime, config.randomDelaySeconds)
            }
            Log.i(TAG, "已重新设置明日 $type 闹钟")
        }
    }
}
