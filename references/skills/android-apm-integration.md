## 友盟Android APM性能监控SDK集成Skill

## 功能说明

自动将友盟Android APM性能监控SDK增量集成到已集成统计SDK的Android项目中,简化APM SDK集成流程。

### 核心功能

1. ✅ **前置条件检查** - 验证项目是否已集成友盟统计SDK
2. ✅ **Gradle插件配置** - 自动注入APM插件classpath和efs配置块
3. ✅ **增量SDK集成** - 在统计SDK基础上添加APM SDK依赖和初始化代码
4. ✅ **编译验证** - 集成后编译验证
5. ✅ **SDK验证** - 通过logcat日志验证APM初始化成功
6. ✅ **回滚机制** - 提供zip备份恢复修改
7. ✅ **性能开关配置** - 支持自定义启用/禁用各项监控能力

## 前置要求

### 必需条件
- ✅ 已集成友盟统计SDK的Android项目
- ✅ Java环境 (JDK 17+)
- ✅ Android SDK (配置ANDROID_HOME或ANDROID_SDK_ROOT)

### 可选工具
- ⚠️ adb工具 (仅SDK验证时需要)
- ⚠️ Android设备或模拟器 (仅SDK验证时需要)


## 使用方式

### 基本用法

```bash
python scripts/umeng-apm-integration/main.py --project-path /path/to/android/project
```

### 指定app模块

```bash
python scripts/umeng-apm-integration/main.py --project-path /path/to/project --app-module myapp
```

### 非交互式模式

```bash
python scripts/umeng-apm-integration/main.py --project-path /path/to/project --non-interactive
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--project-path` | ✅ | - | Android项目路径 |
| `--app-module` | ❌ | `app` | App模块名称 |
| `--non-interactive` | ❌ | `false` | 跳过确认提示直接集成 |

## 工作流程

```
步骤1: 🔍 环境检查
  ↓
步骤2: 📂 项目验证(验证Android项目结构有效)
  ↓
步骤3: 📋 前置条件检查(验证统计SDK已集成,UMConfigure.init存在)
  ↓
步骤4: 💾 创建备份(整个工程zip备份)
  ↓
步骤5: 🔌 Gradle插件配置(注入apm-plugin classpath + apply + efs配置块)
  ↓
步骤6: 📦 SDK增量集成
  ├─ 添加APM SDK依赖
  ├─ 配置权限
  ├─ 添加混淆规则
  └─ 添加APM初始化代码(UMConfigure.init之前)
  ↓
步骤7: ✅ 集成确认(展示变更摘要供用户确认)
  ↓
步骤8: 🔨 编译验证(./gradlew assembleDebug)
  ↓
步骤9: 📱 SDK验证
  ├─ 检查当前appkey是否为占位符(YOUR_UMENG_APPKEY等)
  ├─ 若为占位符，要求用户输入真实appkey并替换后重新编译
  └─ logcat过滤UMCrash,确认成功日志
  ↓
步骤10: 📋 集成报告(输出集成摘要、修改文件清单、备份路径、验证结果)
```

**关键检查点：**
- ✅ **步骤3完成后** - 确认统计SDK已正确集成
- ✅ **步骤4完成后** - 确认备份成功创建，可随时回滚
- ✅ **步骤7（确认点）** - 展示修改清单，用户确认后继续编译
- ✅ **步骤8失败时** - 提供回滚选项，不强制继续
- ✅ **步骤9之前** - 检查当前 appkey 是否为占位符（如 `YOUR_UMENG_APPKEY`），若是则必须要求用户输入真实 appkey，替换后重新编译再进行运行时验证

## SDK集成内容

### 1. Gradle插件配置

**工程根目录 `build.gradle` — buildscript.dependencies 中添加：**
```groovy
buildscript {
    dependencies {
        classpath "com.umeng.umsdk:apm-plugin:2.0.0"
    }
}
```

**App模块 `build.gradle` — 文件头部添加：**
```groovy
apply plugin: 'com.efs.sdk.plugin'
```

**App模块 `build.gradle` — android{} 同级添加 efs 配置块：**
```groovy
efs {
    enable = true
    whiteList = [
            "com.your.package.name"
    ]
    blackList = [
            "com.your.package.name.BaseActivity"
    ]
}
```

**重要说明：**
- ⚠️ **whiteList**：填入需要APM监控的类/包名（通常为应用主包名）
- ⚠️ **blackList**：填入需要排除监控的类（如基类、工具类）
- ⚠️ 黑白名单为可选配置，whiteList留空则默认监控所有类

### 2. APM SDK依赖

**Version Catalogs模式(推荐):**

在`gradle/libs.versions.toml`中定义:
```toml
[versions]
umeng-apm = "+"

[libraries]
umeng-apm = { module = "com.umeng.umsdk:apm", version.ref = "umeng-apm" }
```

在`app/build.gradle.kts`中引用:
```kotlin
dependencies {
    implementation(libs.umeng.apm)
}
```

**传统模式:**
```kotlin
dependencies {
    implementation("com.umeng.umsdk:apm:+")
}
```

### 3. 权限配置

在`AndroidManifest.xml`中添加:
```xml
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>
<uses-permission android:name="android.permission.INTERNET"/>
```

**注意：** 这些权限与统计SDK重叠，如果已集成统计SDK通常已有，无需重复添加。

### 3.5 Native库提取配置

APM SDK 使用 native 库进行崩溃采集和性能监控，必须确保 native 库从 APK 中正确提取。

**AGP 8.x+ 项目（在 app/build.gradle 中配置，推荐）：**
```groovy
android {
    packaging {
        jniLibs {
            useLegacyPackaging = true
        }
    }
}
```

**AGP 7.x 及以下项目（在 AndroidManifest.xml 中配置）：**
```xml
<application
    android:extractNativeLibs="true"
    ...>
```

**说明:**
- Android Gradle Plugin 3.6+ 默认关闭 native 库提取，可能导致 APM native crash 采集异常
- AGP 8.x 中 `extractNativeLibs` 已迁移至 build.gradle 配置，写在 Manifest 会产生 Warning
- 判断依据：查看根目录 `build.gradle` 中 AGP 版本号（如 `com.android.tools.build:gradle:8.7.0`）

### 4. 混淆配置

在`proguard-rules.pro`中添加:
```
-keep class com.umeng.** { *; }
-keep class com.uc.** { *; }
-keep class com.efs.** { *; }
-keepclassmembers class * {
    public <init>(org.json.JSONObject);
}
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}
```

### 5. APM初始化代码

在Application类中，**`UMConfigure.init()` 之前**添加APM配置代码：

**Kotlin版本:**
```kotlin
class UmengApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        // APM性能监控配置（必须在UMConfigure.init之前调用）
        val bundle = Bundle().apply {
            putBoolean(UMCrash.KEY_ENABLE_CRASH_JAVA, true)
            putBoolean(UMCrash.KEY_ENABLE_CRASH_NATIVE, true)
            putBoolean(UMCrash.KEY_ENABLE_ANR, true)
            putBoolean(UMCrash.KEY_ENABLE_PA, true)
            putBoolean(UMCrash.KEY_ENABLE_LAUNCH, true)
            putBoolean(UMCrash.KEY_ENABLE_MEM, true)
            putBoolean(UMCrash.KEY_ENABLE_NET, true)
            putBoolean(UMCrash.KEY_ENABLE_PAGE, true)
            putBoolean(UMCrash.KEY_ENABLE_POWER, true)
            putBoolean(UMCrash.KEY_ENABLE_CODE_LOG, true)
            putBoolean(UMCrash.KEY_ENABLE_MEMLEAK, true)
            putLong(UMCrash.KEY_PA_TIMEOUT_TIME, 2000L)
        }
        UMCrash.initConfig(bundle)

        // 统计SDK初始化（已有代码，保持不变）
        UMConfigure.init(this, "appkey", "channel", UMConfigure.DEVICE_TYPE_PHONE, null)
    }
}
```

**Java版本:**
```java
public class UmengApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();

        // APM性能监控配置（必须在UMConfigure.init之前调用）
        Bundle bundle = new Bundle();
        bundle.putBoolean(UMCrash.KEY_ENABLE_CRASH_JAVA, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_CRASH_NATIVE, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_ANR, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_PA, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_LAUNCH, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_MEM, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_NET, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_PAGE, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_POWER, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_CODE_LOG, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_MEMLEAK, true);
        bundle.putLong(UMCrash.KEY_PA_TIMEOUT_TIME, 2000L);
        UMCrash.initConfig(bundle);

        // 统计SDK初始化（已有代码，保持不变）
        UMConfigure.init(this, "appkey", "channel", UMConfigure.DEVICE_TYPE_PHONE, null);
    }
}
```

**重要说明：**
- ⚠️ `UMCrash.initConfig(bundle)` 必须在 `UMConfigure.init()` **之前**调用
- ⚠️ 所有开关默认为开启状态，不调用 `initConfig` 也是全部开启
- ⚠️ 如需自定义监控能力，可将对应开关设为 `false`

## 常见问题

### Q1: 提示未集成统计SDK?

**A**: APM SDK强依赖统计基础组件,请先运行统计SDK集成:
```bash
python scripts/umeng-analytics-integration/main.py --project-path /path/to/project
```

### Q2: Gradle插件冲突怎么办?

**A**: 检查 `apm-plugin` 版本与项目AGP版本兼容性:
1. 确认工程根目录 `build.gradle` 中 AGP 版本
2. 将 `apm-plugin` 升级到最新版本 `2.0.0`
3. 如仍冲突，尝试在 `gradle.properties` 中添加: `android.enableJetifier=true`

### Q3: efs whiteList/blackList 如何填写?

**A**: 配置说明:
- **whiteList**: 填入需要APM监控的类/包名，通常为应用主包名（如 `com.example.myapp`）
- **blackList**: 填入需要排除监控的类（如基类 `com.example.myapp.BaseActivity`）
- 两者均为可选配置，whiteList留空则默认监控所有类
- 建议whiteList只填应用自身包名，避免监控第三方库

### Q4: 如何验证APM SDK集成成功?

**A**: 运行应用后查看logcat日志:

⚠️ **重要：** 运行时验证前，必须确保应用已配置真实 appkey。若当前使用占位符（如 `YOUR_UMENG_APPKEY`），需先向用户索取真实 appkey，替换后重新编译，再进行运行时验证。占位符 appkey 下 SDK 初始化日志虽能输出，但无法验证数据上报的完整性。

```bash
adb logcat | grep "UMCrash"
```

看到以下日志说明成功:
```
可接入免费的网络分析能力
```

### Q5: 各监控开关含义是什么?

**A**: APM性能监控开关说明:

| 开关 | 功能 | 默认值 |
|------|------|--------|
| `KEY_ENABLE_CRASH_JAVA` | Java崩溃监控 | true |
| `KEY_ENABLE_CRASH_NATIVE` | Native崩溃监控 | true |
| `KEY_ENABLE_ANR` | ANR监控 | true |
| `KEY_ENABLE_PA` | 性能分析 | true |
| `KEY_ENABLE_LAUNCH` | 启动耗时监控 | true |
| `KEY_ENABLE_MEM` | 内存监控 | true |
| `KEY_ENABLE_NET` | 网络监控 | true |
| `KEY_ENABLE_PAGE` | 页面监控 | true |
| `KEY_ENABLE_POWER` | 功耗监控 | true |
| `KEY_ENABLE_CODE_LOG` | 代码日志 | true |
| `KEY_ENABLE_MEMLEAK` | 内存泄漏监控 | true |

`KEY_PA_TIMEOUT_TIME` 为性能分析超时时间（毫秒），默认 2000ms。

### Q6: 集成失败如何回滚?

**A**: 使用回滚脚本（使用zip备份）:
```bash
python scripts/umeng-apm-integration/rollback.py --backup-zip /path/to/backup.zip --project-path /path/to/project
```

**注意：** 集成前会自动创建整个工程目录的zip备份，回滚时会删除当前工程并重新解压备份。

**⚠️ 多SDK共存回滚风险警告：**
- 当前采用全工程 zip 备份策略，备份时间点为 APM 集成前
- 如果项目已先集成了统计SDK/推送SDK，再集成APM，回滚操作会将整个工程恢复到 APM 集成前的状态，**其他SDK在APM集成之后的修改也会被覆盖**
- **建议**：多SDK共存场景下，优先使用 `git commit` 管理每次集成的变更，利用 git 的精细化回退能力实现多层次回滚，而非依赖脚本的 zip 备份

### Q7: 支持多模块项目吗?

**A**: 支持,使用`--app-module`参数指定:
```bash
python scripts/umeng-apm-integration/main.py --project-path /path/to/project --app-module myapp
```

### Q8: 集成后对包体积影响多大?

**A**: APM SDK增量约为:
- `apm` 库：约 800KB
- `apm-plugin` 插桩后增量：视项目规模而定，通常 50-200KB
- 总增量一般在 1-2MB 范围内

### Q9: 为什么集成前 AI Agent 会先执行 umeng-cli trace？

**A**: 这是 Skill 调用埋点上报，用于统计 Skill 实际使用情况：

- Skill 每次被加载：上报 `{"skill_name":"android-apm-integration"}`
- 拿到 Appkey（从已集成的统计 SDK 复用）：补报 `{"skill_name":"android-apm-integration","appkey":"<appkey>"}`

仅上报「哪个 Skill 在哪个 App 上被用」，不涉及任何工程源码内容，可放心执行。

### Q10: 集成后发现代码中有 YOUR_APPKEY/YOUR_CHANNEL 占位符怎么办?

**A**: 当脚本无法从已有的 `UMConfigure.init()` 调用中解析出真实的 appkey 和 channel 时，会使用占位符 `YOUR_APPKEY` 和 `YOUR_CHANNEL` 完成集成。集成完成后必须将占位符替换为真实值：

1. 找到 Application 类中的 `UMConfigure.init()` 调用
2. 将 `"YOUR_APPKEY"` 替换为友盟后台获取的真实 appkey
3. 将 `"YOUR_CHANNEL"` 替换为真实渠道名（如 `googleplay`、`huawei`）
4. 重新编译运行，确认无报错

## 参考资源

### 官方文档
- **友盟APM性能监控接入指南**: https://developer.umeng.com/docs/193624/detail/194590
- **友盟开发者中心**: https://developer.umeng.com

### SDK资料
- **Android统计SDK**: `SDK集成资料/android/Android统计SDK接入说明.md`

### 相关Skills
- **统计SDK集成**: `scripts/umeng-analytics-integration/` (APM SDK前置依赖)
- **推送SDK集成**: `scripts/umeng-push-integration/`

### 工具脚本
| 脚本 | 功能 |
|------|------|
| `scripts/umeng-apm-integration/main.py` | 主工作流编排 |
| `scripts/umeng-apm-integration/sdk_integrator.py` | APM SDK增量集成 |
| `scripts/umeng-apm-integration/plugin_configurator.py` | Gradle插件配置 |
| `scripts/umeng-apm-integration/sdk_verifier.py` | SDK验证 |
| `scripts/umeng-apm-integration/env_checker.py` | 环境检查 |
| `scripts/umeng-apm-integration/project_validator.py` | 项目验证 |
| `scripts/umeng-apm-integration/device_manager.py` | 设备管理 |
| `scripts/umeng-apm-integration/rollback.py` | 回滚恢复 |

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/193624/detail/194590
- Android开发文档: https://developer.android.com/
