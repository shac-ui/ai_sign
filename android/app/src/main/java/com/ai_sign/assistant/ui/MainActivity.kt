package com.ai_sign.assistant.ui

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ai_sign.assistant.helper.CheckinConfig
import com.ai_sign.assistant.helper.NotificationHelper

class MainActivity : ComponentActivity() {

    private val viewModel: ConfigViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        NotificationHelper.createChannel(this)

        // Android 13+ 申请通知权限
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 100)
        }

        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AiSignScreen(viewModel)
                }
            }
        }
    }
}

@Composable
fun AiSignScreen(viewModel: ConfigViewModel) {
    val config by viewModel.config.collectAsState()
    val context = LocalContext.current

    // 本地编辑状态（保存前不直接写 DataStore）
    var targetPackage     by remember(config) { mutableStateOf(config.targetPackage) }
    var buttonText        by remember(config) { mutableStateOf(config.buttonText) }
    var buttonResourceId  by remember(config) { mutableStateOf(config.buttonResourceId) }
    var checkinTime       by remember(config) { mutableStateOf(config.checkinTime) }
    var checkoutTime      by remember(config) { mutableStateOf(config.checkoutTime) }
    var checkinEnabled    by remember(config) { mutableStateOf(config.checkinEnabled) }
    var checkoutEnabled   by remember(config) { mutableStateOf(config.checkoutEnabled) }
    var successText       by remember(config) { mutableStateOf(config.successText) }
    var popupDismiss      by remember(config) { mutableStateOf(config.popupDismissTexts) }
    var randomDelay       by remember(config) { mutableStateOf(config.randomDelaySeconds.toString()) }
    var goHome            by remember(config) { mutableStateOf(config.goHomeAfterCheckin) }

    // 无障碍服务状态
    val isA11yEnabled = remember(config) {
        isAccessibilityServiceEnabled(context)
    }

    var saved by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        // 标题
        Text(
            text = "AiSign 辅助打卡",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
        )

        // 无障碍权限状态卡片
        AccessibilityCard(isA11yEnabled) {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            context.startActivity(intent)
        }

        Divider()

        // 目标 APP 配置
        SectionTitle("目标打卡 APP")

        OutlinedTextField(
            value = targetPackage,
            onValueChange = { targetPackage = it },
            label = { Text("APP 包名（必填）") },
            placeholder = { Text("例：com.example.checkin") },
            supportingText = { Text("打开目标 APP → 运行 adb shell dumpsys window | grep mCurrentFocus 获取") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        OutlinedTextField(
            value = buttonText,
            onValueChange = { buttonText = it },
            label = { Text("打卡按钮文字") },
            placeholder = { Text("例：打卡、签到") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        OutlinedTextField(
            value = buttonResourceId,
            onValueChange = { buttonResourceId = it },
            label = { Text("打卡按钮 ID（可选，优先级更高）") },
            placeholder = { Text("例：com.example.checkin:id/btn_punch") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        Divider()

        // 打卡时间配置
        SectionTitle("打卡时间")

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Checkbox(
                checked = checkinEnabled,
                onCheckedChange = { checkinEnabled = it },
            )
            Text("启用上班打卡")
        }

        if (checkinEnabled) {
            TimePickerField(
                label = "上班打卡时间（HH:mm）",
                value = checkinTime,
                onValueChange = { checkinTime = it },
            )
        }

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Checkbox(
                checked = checkoutEnabled,
                onCheckedChange = { checkoutEnabled = it },
            )
            Text("启用下班打卡")
        }

        if (checkoutEnabled) {
            TimePickerField(
                label = "下班打卡时间（HH:mm）",
                value = checkoutTime,
                onValueChange = { checkoutTime = it },
            )
        }

        OutlinedTextField(
            value = randomDelay,
            onValueChange = { randomDelay = it.filter { c -> c.isDigit() } },
            label = { Text("随机延迟最大秒数") },
            supportingText = { Text("打卡前随机等待 0~N 秒，模拟人工波动（推荐 60~300）") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        Divider()

        // 高级配置
        SectionTitle("高级配置")

        OutlinedTextField(
            value = successText,
            onValueChange = { successText = it },
            label = { Text("成功提示文字（可选）") },
            placeholder = { Text("例：打卡成功") },
            supportingText = { Text("打卡后检测此文字以确认成功，留空则不验证") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        OutlinedTextField(
            value = popupDismiss,
            onValueChange = { popupDismiss = it },
            label = { Text("弹窗关闭按钮文字（逗号分隔）") },
            placeholder = { Text("我知道了,跳过,关闭,以后再说") },
            modifier = Modifier.fillMaxWidth(),
        )

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Checkbox(
                checked = goHome,
                onCheckedChange = { goHome = it },
            )
            Text("打卡完成后回到桌面")
        }

        Divider()

        // 操作按钮
        if (saved) {
            Text(
                text = "✅ 配置已保存，闹钟已设置",
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Medium,
            )
        }

        Button(
            onClick = {
                val newConfig = CheckinConfig(
                    targetPackage      = targetPackage.trim(),
                    buttonText         = buttonText.trim(),
                    buttonResourceId   = buttonResourceId.trim(),
                    checkinTime        = checkinTime.trim(),
                    checkoutTime       = checkoutTime.trim(),
                    checkinEnabled     = checkinEnabled,
                    checkoutEnabled    = checkoutEnabled,
                    successText        = successText.trim(),
                    popupDismissTexts  = popupDismiss.trim(),
                    randomDelaySeconds = randomDelay.toIntOrNull() ?: 120,
                    goHomeAfterCheckin = goHome,
                )
                viewModel.saveConfig(newConfig)
                saved = true
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = targetPackage.isNotBlank(),
        ) {
            Text("保存配置 & 设置闹钟")
        }

        OutlinedButton(
            onClick = { viewModel.triggerNow() },
            modifier = Modifier.fillMaxWidth(),
            enabled = isA11yEnabled && targetPackage.isNotBlank(),
        ) {
            Text("立即测试打卡")
        }

        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(
        text = text,
        fontSize = 16.sp,
        fontWeight = FontWeight.SemiBold,
        color = MaterialTheme.colorScheme.primary,
    )
}

@Composable
private fun AccessibilityCard(isEnabled: Boolean, onEnable: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isEnabled)
                MaterialTheme.colorScheme.primaryContainer
            else
                MaterialTheme.colorScheme.errorContainer,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = if (isEnabled) "无障碍服务：已开启 ✅" else "无障碍服务：未开启 ❌",
                fontWeight = FontWeight.SemiBold,
            )
            Text(
                text = if (isEnabled)
                    "辅助打卡功能正常运行"
                else
                    "自动打卡需要无障碍权限，点击前往系统设置开启",
                fontSize = 13.sp,
            )
            if (!isEnabled) {
                Button(onClick = onEnable) {
                    Text("前往开启无障碍权限")
                }
            }
        }
    }
}

@Composable
private fun TimePickerField(label: String, value: String, onValueChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = {
            // 只接受 "HH:mm" 格式
            if (it.length <= 5) onValueChange(it)
        },
        label = { Text(label) },
        placeholder = { Text("09:00") },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
    )
}

/** 检查无障碍服务是否已开启 */
private fun isAccessibilityServiceEnabled(context: android.content.Context): Boolean {
    val serviceName = "${context.packageName}/.service.CheckinAccessibilityService"
    val enabledServices = Settings.Secure.getString(
        context.contentResolver,
        Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
    ) ?: return false
    return enabledServices.split(":").any {
        it.equals(serviceName, ignoreCase = true)
    }
}
