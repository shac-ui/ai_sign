package com.ai_sign.assistant.helper

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

// DataStore 单例扩展属性（每个 Context 只创建一次）
val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "checkin_prefs")

/**
 * 打卡配置数据模型
 */
data class CheckinConfig(
    /** 目标打卡 APP 的包名，例如 com.example.checkin */
    val targetPackage: String = "",
    /** 打卡按钮的文字，例如 "打卡"、"签到" */
    val buttonText: String = "打卡",
    /** 打卡按钮的 resource-id（可选，优先级高于 buttonText）*/
    val buttonResourceId: String = "",
    /** 上班打卡时间，格式 "HH:mm"，例如 "09:00" */
    val checkinTime: String = "09:00",
    /** 下班打卡时间，格式 "HH:mm"，例如 "18:00" */
    val checkoutTime: String = "18:00",
    /** 是否启用上班打卡 */
    val checkinEnabled: Boolean = true,
    /** 是否启用下班打卡 */
    val checkoutEnabled: Boolean = true,
    /** 打卡成功后页面显示的文字（用于验证），例如 "打卡成功" */
    val successText: String = "",
    /** 需要自动关闭的弹窗按钮文字，逗号分隔，例如 "我知道了,跳过" */
    val popupDismissTexts: String = "我知道了,跳过,关闭,以后再说",
    /** 随机最大延迟秒数（0~N 随机，模拟人工波动） */
    val randomDelaySeconds: Int = 120,
    /** 打卡完成后是否自动退回桌面 */
    val goHomeAfterCheckin: Boolean = true,
)

/**
 * 配置存取封装
 * 基于 Jetpack DataStore（协程 Flow，线程安全）
 */
object PrefsHelper {

    private val KEY_TARGET_PACKAGE   = stringPreferencesKey("target_package")
    private val KEY_BUTTON_TEXT      = stringPreferencesKey("button_text")
    private val KEY_BUTTON_ID        = stringPreferencesKey("button_resource_id")
    private val KEY_CHECKIN_TIME     = stringPreferencesKey("checkin_time")
    private val KEY_CHECKOUT_TIME    = stringPreferencesKey("checkout_time")
    private val KEY_CHECKIN_ENABLED  = booleanPreferencesKey("checkin_enabled")
    private val KEY_CHECKOUT_ENABLED = booleanPreferencesKey("checkout_enabled")
    private val KEY_SUCCESS_TEXT     = stringPreferencesKey("success_text")
    private val KEY_POPUP_DISMISS    = stringPreferencesKey("popup_dismiss_texts")
    private val KEY_RANDOM_DELAY     = intPreferencesKey("random_delay_seconds")
    private val KEY_GO_HOME          = booleanPreferencesKey("go_home_after_checkin")

    /** 读取配置（Flow，界面层 collect 自动更新） */
    fun configFlow(context: Context): Flow<CheckinConfig> =
        context.dataStore.data.map { prefs ->
            CheckinConfig(
                targetPackage      = prefs[KEY_TARGET_PACKAGE]   ?: "",
                buttonText         = prefs[KEY_BUTTON_TEXT]      ?: "打卡",
                buttonResourceId   = prefs[KEY_BUTTON_ID]        ?: "",
                checkinTime        = prefs[KEY_CHECKIN_TIME]     ?: "09:00",
                checkoutTime       = prefs[KEY_CHECKOUT_TIME]    ?: "18:00",
                checkinEnabled     = prefs[KEY_CHECKIN_ENABLED]  ?: true,
                checkoutEnabled    = prefs[KEY_CHECKOUT_ENABLED] ?: true,
                successText        = prefs[KEY_SUCCESS_TEXT]     ?: "",
                popupDismissTexts  = prefs[KEY_POPUP_DISMISS]    ?: "我知道了,跳过,关闭,以后再说",
                randomDelaySeconds = prefs[KEY_RANDOM_DELAY]     ?: 120,
                goHomeAfterCheckin = prefs[KEY_GO_HOME]          ?: true,
            )
        }

    /** 保存配置（挂起函数，需在协程中调用） */
    suspend fun saveConfig(context: Context, config: CheckinConfig) {
        context.dataStore.edit { prefs ->
            prefs[KEY_TARGET_PACKAGE]   = config.targetPackage
            prefs[KEY_BUTTON_TEXT]      = config.buttonText
            prefs[KEY_BUTTON_ID]        = config.buttonResourceId
            prefs[KEY_CHECKIN_TIME]     = config.checkinTime
            prefs[KEY_CHECKOUT_TIME]    = config.checkoutTime
            prefs[KEY_CHECKIN_ENABLED]  = config.checkinEnabled
            prefs[KEY_CHECKOUT_ENABLED] = config.checkoutEnabled
            prefs[KEY_SUCCESS_TEXT]     = config.successText
            prefs[KEY_POPUP_DISMISS]    = config.popupDismissTexts
            prefs[KEY_RANDOM_DELAY]     = config.randomDelaySeconds
            prefs[KEY_GO_HOME]          = config.goHomeAfterCheckin
        }
    }

    /** 同步读取（在 Service/Receiver 中使用，不适合 UI 层） */
    suspend fun getConfig(context: Context): CheckinConfig {
        var result = CheckinConfig()
        context.dataStore.data.collect { prefs ->
            result = CheckinConfig(
                targetPackage      = prefs[KEY_TARGET_PACKAGE]   ?: "",
                buttonText         = prefs[KEY_BUTTON_TEXT]      ?: "打卡",
                buttonResourceId   = prefs[KEY_BUTTON_ID]        ?: "",
                checkinTime        = prefs[KEY_CHECKIN_TIME]     ?: "09:00",
                checkoutTime       = prefs[KEY_CHECKOUT_TIME]    ?: "18:00",
                checkinEnabled     = prefs[KEY_CHECKIN_ENABLED]  ?: true,
                checkoutEnabled    = prefs[KEY_CHECKOUT_ENABLED] ?: true,
                successText        = prefs[KEY_SUCCESS_TEXT]     ?: "",
                popupDismissTexts  = prefs[KEY_POPUP_DISMISS]    ?: "我知道了,跳过,关闭,以后再说",
                randomDelaySeconds = prefs[KEY_RANDOM_DELAY]     ?: 120,
                goHomeAfterCheckin = prefs[KEY_GO_HOME]          ?: true,
            )
            return@collect
        }
        return result
    }

    /** 解析弹窗文字列表 */
    fun CheckinConfig.popupDismissList(): List<String> =
        popupDismissTexts.split(",").map { it.trim() }.filter { it.isNotEmpty() }
}
