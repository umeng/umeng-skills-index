## 友盟Android统计SDK集成Skill

## 功能说明

自动将友盟Android统计SDK集成到现有Android项目中,简化SDK集成流程。

### 核心功能

1. ✅ **环境检查** - 自动检测Java、Android SDK、adb等开发工具
2. ✅ **项目验证** - 验证目标Android项目完整性并尝试编译
3. ✅ **参数交互** - 引导用户输入appkey和channel,支持占位符模式
4. ✅ **SDK集成** - 自动完成Maven仓库、依赖、权限、混淆、Application类配置
5. ✅ **编译验证** - 集成后编译验证
6. ✅ **SDK验证** - 通过logcat日志验证SDK是否成功上报数据
7. ✅ **回滚机制** - 提供回滚脚本恢复修改

## 前置要求

### 必需工具
- ✅ Java环境 (JDK 17+)
- ✅ Android SDK (配置ANDROID_HOME或ANDROID_SDK_ROOT)
- ✅ 可编译的Android项目

### 可选工具
- ⚠️ adb工具 (仅SDK验证时需要)
- ⚠️ Android设备或模拟器 (仅SDK验证时需要)


## 使用方式

### 基本用法(交互式)

```bash
python scripts/umeng-analytics-integration/main.py --project-path /path/to/android/project
```

运行后会引导你输入:
- appkey: 友盟后台获取的应用标识
- channel: 应用分发渠道(如: googleplay, huawei)

### 指定app模块

```bash
python scripts/umeng-analytics-integration/main.py --project-path /path/to/project --app-module myapp
```

### 非交互式模式(传递参数)

如果需要避免交互提示,可以直接传递参数:

```bash
echo -e "y\nyour_appkey\nyour_channel\ny" | python scripts/umeng-analytics-integration/main.py --project-path /path/to/project
```

或使用占位符:

```bash
echo -e "n\ny" | python scripts/umeng-analytics-integration/main.py --project-path /path/to/project
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--project-path` | ✅ | - | Android项目路径 |
| `--app-module` | ❌ | `app` | App模块名称 |

## 工作流程

```
步骤1: 🔍 环境检查
  ↓
步骤2: 📂 项目验证(含编译验证)
  ↓
步骤3: ⌨️  参数交互(appkey + channel)
  ↓
步骤4: 📦 SDK集成
  ├─ 添加Maven仓库
  ├─ 添加SDK依赖
  ├─ 配置权限
  ├─ 添加混淆规则
  └─ 创建/修改Application类
  ↓
步骤5: 🔨 编译验证
  ↓
步骤6: 📱 SDK验证
  ├─ 检查当前appkey是否为占位符(YOUR_UMENG_APPKEY等)
  ├─ 若为占位符，要求用户输入真实appkey并替换后重新编译
  └─ logcat过滤UMConfigure,确认成功日志
  ↓
步骤7: 📋 生成报告
```

## SDK集成内容

### 1. Maven仓库配置

在项目级`settings.gradle.kts`中配置(Version Catalogs模式):
```kotlin
dependencyResolutionManagement {
    repositories {
        mavenCentral()
        maven { setUrl("https://repo1.maven.org/maven2/") }
    }
}
```

### 2. SDK依赖

**Version Catalogs模式(推荐):**

在`gradle/libs.versions.toml`中定义:
```toml
[versions]
umeng-common = "+"
umeng-asms = "+"

[libraries]
umeng-common = { module = "com.umeng.umsdk:common", version.ref = "umeng-common" }
umeng-asms = { module = "com.umeng.umsdk:asms", version.ref = "umeng-asms" }
```

在`app/build.gradle.kts`中引用:
```kotlin
dependencies {
    implementation(libs.umeng.common)
    implementation(libs.umeng.asms)
}
```

**传统模式:**
```kotlin
dependencies {
    implementation("com.umeng.umsdk:common:+")
    implementation("com.umeng.umsdk:asms:+")
}
```

### 3. 权限配置

在`AndroidManifest.xml`中添加:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 4. 混淆配置

在`proguard-rules.pro`中添加:
```
-keep class com.umeng.** {*;}
-keep class org.repackage.** {*;}
-keep class com.uyumao.** { *; }
-keepclassmembers class * {
   public <init> (org.json.JSONObject);
}
```

### 5. Application类

创建或修改Application类,添加SDK初始化代码:

**Kotlin版本:**
```kotlin
class UmengApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        UMConfigure.setLogEnabled(true)
        UMConfigure.preInit(this, "your_appkey", "your_channel")
        
        Thread {
            UMConfigure.init(
                this,
                "your_appkey",
                "your_channel",
                UMConfigure.DEVICE_TYPE_PHONE,
                null
            )
        }.start()
    }
}
```

## 常见问题

### Q1: 提示缺少Java环境?

**A**: 安装JDK 17或更高版本:
```bash
## macOS
brew install openjdk@17

## Linux
sudo apt install openjdk-17-jdk

## Windows
## 下载: https://adoptium.net/
```

### Q2: 提示Android SDK未配置?

**A**: 安装Android Studio,它会自动配置环境变量。或手动配置:
```bash
## macOS
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$ANDROID_HOME/platform-tools:$PATH

## Linux/Ubuntu
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$ANDROID_HOME/platform-tools:$PATH

## 在~/.bashrc或~/.zshrc中添加上述配置
source ~/.bashrc  # 使配置生效
```

**Ubuntu安装Android SDK:**
```bash
## 方法1: 安装Android Studio(推荐)
sudo snap install android-studio --classic

## 方法2: 命令行安装SDK Tools
sudo apt install wget unzip
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-11076708_latest.zip
mkdir -p $HOME/Android/Sdk/cmdline-tools
mv cmdline-tools $HOME/Android/Sdk/cmdline-tools/latest

## 接受license并安装必要组件
export ANDROID_HOME=$HOME/Android/Sdk
$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses
$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

### Q3: 项目编译失败?

**A**: SDK集成前项目必须可编译。请:
1. 在Android Studio中打开项目
2. 修复所有编译错误
3. 确保能成功生成APK
4. 再运行SDK集成

### Q4: 使用占位符集成后怎么办?

**A**: 集成时需要替换为真实值:
1. 在友盟后台创建应用获取appkey
2. 打开Application类
3. 替换`YOUR_UMENG_APPKEY`为真实appkey
4. 替换`YOUR_CHANNEL`为真实channel
5. 重新编译运行

### Q5: 如何验证SDK集成成功?

**A**: 运行应用后查看logcat日志:

⚠️ **重要：** 运行时验证前，必须确保应用已配置真实 appkey。若当前使用占位符（如 `YOUR_UMENG_APPKEY`），需先向用户索取真实 appkey，替换后重新编译，再进行运行时验证。占位符 appkey 下 SDK 初始化日志虽能输出，但无法验证数据上报的完整性。

```bash
adb logcat | grep "UMConfigure"
```

看到以下日志说明成功:
```
本次启动数据: 发送成功!
```

### Q6: 集成失败如何回滚?

**A**: 使用回滚脚本:
```bash
python scripts/umeng-analytics-integration/rollback.py --backup-dir /path/to/backup
```

### Q7: 支持多模块项目吗?

**A**: 支持,使用`--app-module`参数指定:
```bash
python scripts/umeng-analytics-integration/main.py --project-path /path/to/project --app-module myapp
```

### Q8: 已有Application类会怎么处理?

**A**: 自动修改现有Application类:
- 备份原文件
- 在onCreate方法尾部追加SDK初始化代码
- 保持原有逻辑不变

### Q9: 为什么集成前 AI Agent 会先执行 umeng-cli trace？

**A**: 这是 Skill 调用埋点上报，用于统计 Skill 实际使用情况：

- Skill 每次被加载：上报 `{"skill_name":"umeng-analytics-integration"}`
- 拿到新 Appkey：补报 `{"skill_name":"umeng-analytics-integration","appkey":"<appkey>"}`

仅上报「哪个 Skill 在哪个 App 上被用」，不涉及任何工程源码内容，可放心执行。

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/119267/detail/118578
- Android开发文档: https://developer.android.com/
