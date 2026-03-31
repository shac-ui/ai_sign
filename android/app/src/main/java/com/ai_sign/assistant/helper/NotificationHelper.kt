package com.ai_sign.assistant.helper

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.ai_sign.assistant.R
import com.ai_sign.assistant.ui.MainActivity

/**
 * 通知辅助模块
 * - 打卡进行中：进度通知（不可消除）
 * - 打卡结果：可消除通知，点击跳转主界面
 */
object NotificationHelper {

    private const val CHANNEL_ID = "ai_sign_channel"
    private const val ID_PROGRESS = 1
    private const val ID_RESULT   = 2

    fun createChannel(context: Context) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (manager.getNotificationChannel(CHANNEL_ID) != null) return

        val channel = NotificationChannel(
            CHANNEL_ID,
            context.getString(R.string.notification_channel_name),
            NotificationManager.IMPORTANCE_DEFAULT,
        ).apply {
            description = "打卡状态通知"
            setShowBadge(true)
        }
        manager.createNotificationChannel(channel)
    }

    /** 打卡进行中（不可滑动消除） */
    fun showProgress(context: Context) {
        createChannel(context)
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle(context.getString(R.string.notification_checkin_title))
            .setContentText("正在自动操作打卡 APP ...")
            .setOngoing(true)
            .setProgress(0, 0, true)
            .build()

        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(ID_PROGRESS, notification)
    }

    /** 打卡结果通知（可消除，点击打开主界面） */
    fun showResult(context: Context, success: Boolean, msg: String? = null) {
        createChannel(context)

        // 先取消进度通知
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.cancel(ID_PROGRESS)

        val title = if (success)
            context.getString(R.string.notification_success)
        else
            context.getString(R.string.notification_failure)

        val text = msg ?: if (success) "已自动完成打卡" else "请打开 APP 手动确认"

        val tapIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            context, 0, tapIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle(title)
            .setContentText(text)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        manager.notify(ID_RESULT, notification)
    }
}
