package com.ai_sign.assistant.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.ai_sign.assistant.helper.AlarmScheduler
import com.ai_sign.assistant.helper.CheckinConfig
import com.ai_sign.assistant.helper.PrefsHelper
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class ConfigViewModel(application: Application) : AndroidViewModel(application) {

    private val context get() = getApplication<Application>()

    /** 配置状态，UI 直接 collect */
    val config: StateFlow<CheckinConfig> = PrefsHelper.configFlow(context)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), CheckinConfig())

    /** 保存配置并重新设置闹钟 */
    fun saveConfig(newConfig: CheckinConfig) {
        viewModelScope.launch {
            PrefsHelper.saveConfig(context, newConfig)
            AlarmScheduler.scheduleAll(context, newConfig)
        }
    }

    /** 立即触发一次打卡（测试用） */
    fun triggerNow() {
        viewModelScope.launch {
            val cfg = PrefsHelper.getConfig(context)
            if (cfg.targetPackage.isBlank()) return@launch
            val intent = android.content.Intent(
                context,
                com.ai_sign.assistant.service.CheckinAccessibilityService::class.java
            ).apply {
                action = com.ai_sign.assistant.service.CheckinAccessibilityService.ACTION_DO_CHECKIN
            }
            context.startService(intent)
        }
    }
}
