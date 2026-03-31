package com.ai_sign.assistant

import android.app.Application
import com.ai_sign.assistant.helper.NotificationHelper

class AiSignApp : Application() {
    override fun onCreate() {
        super.onCreate()
        NotificationHelper.createChannel(this)
    }
}
