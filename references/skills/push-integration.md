## 友盟Android推送SDK集成Skill

## 功能说明

自动将友盟Android推送SDK增量集成到已集成统计SDK的Android项目中,简化推送SDK集成流程。

### 核心功能

1. ✅ **前置条件检查** - 验证项目是否已集成友盟统计SDK
2. ✅ **参数交互** - 引导用户输入messageSecret,支持复用统计SDK的appkey和channel
3. ✅ **增量SDK集成** - 在统计SDK基础上添加推送SDK依赖和初始化代码
4. ✅ **编译验证** - 集成后编译验证
5. ✅ **SDK验证** - 通过logcat日志验证deviceToken获取成功
6. ✅ **回滚机制** - 提供回滚脚本恢复修改

## 前置要求

### 必需条件
- ✅ 已集成友盟统计SDK的Android项目
- ✅ Java环境 (JDK 17+)
- ✅ Android SDK (配置ANDROID_HOME或ANDROID_SDK_ROOT)

### 可选工具
- ⚠️ adb工具 (仅SDK验证时需要)
- ⚠️ Android设备或模拟器 (仅SDK验证时需要)


## 使用方式

### 基本用法(交互式)

```bash
python scripts/umeng-push-integration/main.py --project-path /path/to/android/project
```

运行后会引导你输入:
- messageSecret: 友盟消息后台获取的Message Secret

### 指定app模块

```bash
python scripts/umeng-push-integration/main.py --project-path /path/to/project --app-module myapp
```

### 非交互式模式(传递参数)

```bash
python scripts/umeng-push-integration/main.py --project-path /path/to/project --message-secret YOUR_MESSAGE_SECRET
```

或完全指定所有参数:

```bash
python scripts/umeng-push-integration/main.py --project-path /path/to/project --app-key YOUR_KEY --channel YOUR_CHANNEL --message-secret YOUR_SECRET
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--project-path` | ✅ | - | Android项目路径 |
| `--app-module` | ❌ | `app` | App模块名称 |
| `--message-secret` | ❌ | - | 推送Message Secret(非交互模式必需) |
| `--app-key` | ❌ | - | 复用统计SDK的appkey时可省略 |
| `--channel` | ❌ | - | 复用统计SDK的channel时可省略 |

## 工作流程

```
步骤1: 🔍 环境检查
  ↓
步骤2: 📂 项目验证(含编译验证)
  ↓
步骤3: 📋 前置条件检查(验证统计SDK已集成)
  ↓
步骤4: ⌨️  参数交互(messageSecret)
  ↓
步骤5: 💾 创建备份(整个工程zip备份)
  ↓
步骤6: 📦 SDK增量集成
  ├─ 添加推送SDK依赖
  ├─ 修改UMConfigure.init()第5个参数
  ├─ 添加PushAgent注册代码
  └─ 添加AndroidManifest.xml meta-data配置
  ↓
步骤7: ✅ 集成确认(用户确认修改内容)
  ↓
步骤8: 🔨 编译验证
  ↓
步骤9: 📱 SDK验证
  ├─ 检查当前appkey是否为占位符(YOUR_UMENG_APPKEY等)
  ├─ 若为占位符，要求用户输入真实appkey并替换后重新编译
  └─ logcat过滤PushAgent,确认deviceToken获取成功
  ↓
步骤10: 📋 生成报告
```

**关键检查点：**
- ✅ **步骤3完成后** - 确认统计SDK已正确集成
- ✅ **步骤5完成后** - 确认备份成功创建，可随时回滚
- ✅ **步骤7（确认点）** - 展示修改清单，用户确认后继续编译
- ✅ **步骤8失败时** - 提供回滚选项，不强制继续
- ✅ **步骤9之前** - 检查当前 appkey 是否为占位符（如 `YOUR_UMENG_APPKEY`），若是则必须要求用户输入真实 appkey，替换后重新编译再进行运行时验证

## SDK集成内容

### 1. 推送SDK依赖

**Version Catalogs模式(推荐):**

在`gradle/libs.versions.toml`中定义:
```toml
[versions]
umeng-push = "+"

[libraries]
umeng-push = { module = "com.umeng.umsdk:push", version.ref = "umeng-push" }
```

在`app/build.gradle.kts`中引用:
```kotlin
dependencies {
    implementation(libs.umeng.push)
}
```

**传统模式:**
```kotlin
dependencies {
    implementation("com.umeng.umsdk:push:+")
}
```

### 2. 修改初始化代码

将Application类中的:
```java
UMConfigure.init(this, "appkey", "channel", UMConfigure.DEVICE_TYPE_PHONE, null);
```

修改为:
```java
UMConfigure.init(this, "appkey", "channel", UMConfigure.DEVICE_TYPE_PHONE, "your_message_secret");
```

### 3. 添加推送注册代码

**Kotlin版本:**
```kotlin
// 在init()函数中，UMConfigure.init()调用之后
val mPushAgent = PushAgent.getInstance(context)
mPushAgent.register(object : UPushRegisterCallback {
    override fun onSuccess(deviceToken: String) {
        Log.i("UmengPush", "deviceToken: " + deviceToken)
    }
    override fun onFailure(errCode: String, errDesc: String) {
        Log.e("UmengPush", "register failed: " + errCode + " " + errDesc)
    }
})
```

**Java版本:**
```java
// 在init()方法中，UMConfigure.init()调用之后
PushAgent mPushAgent = PushAgent.getInstance(context);
mPushAgent.register(new UPushRegisterCallback() {
    @Override
    public void onSuccess(String deviceToken) {
        Log.i("UmengPush", "deviceToken: " + deviceToken);
    }
    @Override
    public void onFailure(String s, String s1) {
        Log.i("UmengPush", "register failed: " + s + " " + s1);
    }
});
```

**重要说明：**
- ⚠️ 推送注册代码必须放在`init()`函数内部，紧跟在`UMConfigure.init()`之后
- ⚠️ 必须保证注册代码和初始化代码在同一个线程中执行
- ⚠️ 使用`context`参数而非`this`（因为在companion object中）

### 4. AndroidManifest.xml配置

**必需添加meta-data配置：**
```xml
<application
    android:name=".UmengApplication"
    ...>
    
    <!-- 友盟推送配置 -->
    <meta-data
        android:name="UMENG_APPKEY"
        android:value="your_appkey" />
    <meta-data
        android:name="UMENG_MESSAGE_SECRET"
        android:value="your_message_secret" />
    
    ...
</application>
```

**重要说明：**
- ⚠️ 推送SDK**必须**配置这两个meta-data，否则会导致`Appkey、MessageSecret cannot be empty!`错误
- ⚠️ `UMENG_MESSAGE_SECRET`的值必须与`UMConfigure.init()`第5个参数一致

## 常见问题

### Q1: 提示未集成统计SDK?

**A**: 推送SDK强依赖统计基础组件,请先运行统计SDK集成:
```bash
python scripts/umeng-analytics-integration/main.py --project-path /path/to/project
```

### Q2: Message Secret从哪里获取?

**A**: 登录友盟消息后台:
1. 访问 https://message.umeng.com
2. 进入应用设置页面
3. 复制"Umeng Message Secret"值

### Q3: 使用占位符集成后怎么办?

**A**: 集成时需要替换为真实值:
1. 在友盟消息后台获取真实messageSecret
2. 打开Application类
3. 替换`YOUR_MESSAGE_SECRET`为真实值
4. 重新编译运行

### Q4: 如何验证推送SDK集成成功?

**A**: 运行应用后查看logcat日志:

⚠️ **重要：** 运行时验证前，必须确保应用已配置真实 appkey。若当前使用占位符（如 `YOUR_UMENG_APPKEY`），需先向用户索取真实 appkey，替换后重新编译，再进行运行时验证。占位符 appkey 下 SDK 初始化日志虽能输出，但无法验证推送注册和 deviceToken 获取的完整性。

```bash
adb logcat | grep -E "device_token|deviceToken|sendLaunch"
```

看到以下日志说明成功:
```
device_token: Artfws9cl-LCHHo0BDhcFCXavttflFE23wEfEgBG8Yks
```

或完整日志示例:
```json
sendLaunch: {"header":{"p_sdk_v":"6.7.6"},"content":{"push":[{"device_token":"Artfws9cl...","channel":[]}]}}
```

### Q5: 集成失败如何回滚?

**A**: 使用回滚脚本（使用zip备份）:
```bash
python scripts/umeng-push-integration/rollback.py --backup-zip /path/to/backup.zip --project-path /path/to/project
```

**注意：** 集成前会自动创建整个工程目录的zip备份，回滚时会删除当前工程并重新解压备份。

### Q6: 支持多模块项目吗?

**A**: 支持,使用`--app-module`参数指定:
```bash
python scripts/umeng-push-integration/main.py --project-path /path/to/project --app-module myapp
```

### Q7: 已有Application类会怎么处理?

**A**: 自动修改现有Application类:
- 修改`UMConfigure.init()`第5个参数（null → messageSecret）
- 在`init()`函数中`UMConfigure.init()`之后添加PushAgent注册代码
- 保持原有逻辑不变

### Q8: 为什么需要在AndroidManifest.xml中添加meta-data?

**A**: 推送SDK除了需要在代码中传入messageSecret，还需要在AndroidManifest.xml中配置：
- `UMENG_APPKEY`: 应用AppKey
- `UMENG_MESSAGE_SECRET`: 推送Message Secret

如果不配置，会导致错误：`Appkey、MessageSecret cannot be empty!`

### Q9: 为什么集成前 AI Agent 会先执行 umeng-cli trace？

**A**: 这是 Skill 调用埋点上报，用于统计 Skill 实际使用情况：

- Skill 每次被加载：上报 `{"skill_name":"umeng-push-integration"}`
- 拿到 Appkey（输入或从已集成的统计 SDK 复用）：补报 `{"skill_name":"umeng-push-integration","appkey":"<appkey>"}`

仅上报「哪个 Skill 在哪个 App 上被用」，**messageSecret 不纳入埋点**，不涉及任何工程源码内容，可放心执行。

## 参考资源

### 官方文档
- **友盟推送SDK接入指南**: https://developer.umeng.com/docs/119267/detail/118584
- **友盟消息后台**: https://message.umeng.com
- **友盟开发者中心**: https://developer.umeng.com

### SDK资料
- **Android推送SDK**: `SDK集成资料/android/Android推送SDK接入说明.md`
- **Android统计SDK**: `SDK集成资料/android/Android统计SDK接入说明.md`
- **友盟OpenAPI Python SDK**: `友盟_openapi_python_SDK/`

### 相关Skills
- **统计SDK集成**: `scripts/umeng-analytics-integration/` (推送SDK前置依赖)
- **iOS统计SDK集成**: `skills/umeng-ios-analytics-integration/`

### 工具脚本
| 脚本 | 功能 |
|------|------|
| `scripts/umeng-push-integration/main.py` | 主流程控制 |
| `scripts/umeng-push-integration/sdk_integrator.py` | SDK集成逻辑 |
| `scripts/sdk_verifier.py` | SDK验证(logcat) |
| `scripts/env_checker.py` | 环境检查 |
| `scripts/project_validator.py` | 项目验证 |
| `scripts/device_manager.py` | 设备管理(adb) |
| `scripts/rollback.py` | 回滚(zip备份恢复) |

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/119267/detail/118584
- Android开发文档: https://developer.android.com/
