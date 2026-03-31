# 保留无障碍服务类（混淆后系统无法找到服务）
-keep class com.ai_sign.assistant.service.** { *; }
-keep class com.ai_sign.assistant.receiver.** { *; }
-keep class com.ai_sign.assistant.helper.** { *; }

# Kotlin 协程
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}

# DataStore
-keep class androidx.datastore.** { *; }
