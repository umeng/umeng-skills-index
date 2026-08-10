## 友盟Flutter APM SDK集成Skill

## 功能说明

自动将友盟 APM Flutter SDK 增量集成到已集成统计SDK的 Flutter 项目中（覆盖 Android + iOS 双端），简化APM SDK集成流程。

### 核心功能

1. ✅ **环境检查** - 检测 Flutter SDK、Dart SDK、Android SDK、CocoaPods
2. ✅ **项目验证** - 验证 Flutter 项目完整性
3. ✅ **前置条件检查** - 验证 umeng_common_sdk 是否已集成
4. ✅ **参数交互** - 引导输入 Android AppKey、iOS AppKey 和 channel
5. ✅ **集成路径决策** - 根据工程类型选择集成路径
6. ✅ **SDK集成** - 自动完成 pubspec.yaml、Binding 替换、NavigatorObserver 注册
7. ✅ **编译验证** - 集成后 flutter build 编译验证
8. ✅ **SDK验证** - 验证 APM 数据采集
9. ✅ **回滚机制** - 提供回滚脚本恢复修改

### 前置依赖

⚠️ **必须先完成 Flutter 统计SDK集成**（检查 `pubspec.yaml` 中已有 `umeng_common_sdk` 依赖）。如未集成，请先运行：
```bash
python scripts/umeng-flutter-analytics-integration/main.py --project-path /path/to/flutter/project
```

### 支持的项目类型

- ✅ 标准 Flutter App（`flutter create` 生成的默认项目）
- ✅ Flutter Module（嵌入原生工程，需设置 `projectType: 1`）

### 前置要求

#### 必需条件
- ✅ 已集成友盟统计SDK的Flutter项目（`pubspec.yaml` 中存在 `umeng_common_sdk`）
- ✅ Flutter SDK >= 2.0.0
- ✅ Dart SDK >= 2.12.0（空安全）
- ✅ Android minSdkVersion >= 21
- ✅ iOS Deployment Target >= 10.0

#### 可选工具
- ⚠️ CocoaPods >= 1.10（仅 iOS 端需要）
- ⚠️ adb工具（仅 Android SDK验证时需要）
- ⚠️ Android设备或模拟器 / iOS真机或模拟器（仅SDK验证时需要）


## 使用方式

### 基本用法

```bash
python scripts/umeng-flutter-apm-integration/main.py --project-path /path/to/flutter/project
```

### 非交互式模式

```bash
python scripts/umeng-flutter-apm-integration/main.py \
  --project-path /path/to/flutter/project \
  --android-key YOUR_ANDROID_APPKEY \
  --ios-key YOUR_IOS_APPKEY \
  --channel Umeng \
  --native-crash
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--project-path` | ✅ | - | Flutter项目路径 |
| `--android-key` | ❌ | 交互式输入 | Android端 AppKey |
| `--ios-key` | ❌ | 交互式输入 | iOS端 AppKey |
| `--channel` | ❌ | `Umeng` | 渠道标识 |
| `--native-crash` | ❌ | `false` | 是否采集Native崩溃（启用后执行步骤4） |
| `--yes` | ❌ | `false` | 跳过确认提示直接集成 |
| `--timeout` | ❌ | `1800` | 编译超时时间（秒），默认 1800 秒（30 分钟） |
| `--no-trace` | ❌ | `false` | 禁用 Skill 使用情况上报（umeng-cli trace） |
| `--rollback-on-failure` | ❌ | `false` | 编译验证失败时自动回滚（默认保留集成代码便于排查） |

## 工作流程

```
步骤1: 🔍 环境检查
  ↓
步骤2: 📋 项目验证
  ↓
步骤3: ✅ 前置条件检查 (umeng_common_sdk 已集成？)
  ↓
步骤4: ⚙️ 参数配置 (Android AppKey + iOS AppKey + channel)
  ↓
步骤5: 🔀 集成路径决策 (纯Flutter App / Native崩溃采集 / Module)
  ↓
步骤6: 💾 项目备份
  ↓
步骤7: 🔧 SDK集成
  ├─ pubspec.yaml 添加 umeng_apm_sdk + umeng_common_sdk
  ├─ flutter pub get
  ├─ lib/main.dart: 替换为 APM 初始化代码（Binding替换 + NavigatorObserver）
  ├─ Android: 权限 + 混淆规则
  ├─ (可选) Android: MyApplication + UMCrash.initConfig
  ├─ (可选) iOS: AppDelegate + UMAPMConfig
  └─ iOS: pod install
  ↓
步骤8: 🏗️ 编译验证
  ↓
步骤9: 📊 集成报告
```

**关键检查点：**
- ✅ **步骤3完成后** - 确认统计SDK已正确集成（`pubspec.yaml` 中存在 `umeng_common_sdk`）
- ✅ **步骤6完成后** - 确认备份成功创建，可随时回滚
- ✅ **步骤7 Binding替换** - 必须删除 `WidgetsFlutterBinding.ensureInitialized()`，用自定义 `MyApmWidgetsFlutterBinding` 替代
- ✅ **步骤7 NavigatorObserver** - 必须将 `ApmNavigatorObserver` 注入 `MaterialApp.navigatorObservers`
- ✅ **步骤8失败时** - 提供回滚选项，不强制继续

## 集成路径决策表

> 下表编号为**文档章节号**（非脚本执行步骤）；脚本实际执行步骤为 main.py 的 1→9（纯 Flutter App 对应脚本步骤 1→2→3→6→7→8→9），排障对照时请注意区分。

| 工程类型 | 执行步骤 | 说明 |
|---------|---------|------|
| 纯 Flutter App（最常见） | 步骤 1→2→3→5→6→7（跳过 Native 端配置） | 只监控 Dart 异常 |
| 需要采集 Native 崩溃 | 步骤 1→2→3→4→5→6→7（含 Android MyApplication + iOS AppDelegate） | 同时监控 Java/OC 层崩溃 |
| Flutter Module 嵌入原生 | 步骤 1→2→3→4→5→6→7，projectType: 1 | 必须执行 Native 端配置 |

> `flutter create` 生成的默认项目属于"纯 Flutter App"，走最短路径即可。

## SDK集成内容

### 1. pubspec.yaml 依赖配置

**文件：** `pubspec.yaml`

在 `dependencies:` 下添加：

```yaml
dependencies:
  flutter:
    sdk: flutter
  umeng_apm_sdk: ^2.2.1
  umeng_common_sdk: ^1.2.6
```

> 如需动态获取应用版本信息（可选），额外添加 `package_info_plus: ^4.0.0`（需 Flutter 3.x+）。

**执行命令：**
```bash
flutter pub get
```

**预期输出：** 包含 `+ umeng_apm_sdk 2.x.x` 和 `+ umeng_common_sdk 1.x.x`。

**依赖冲突处理：** 如果报 `http` 包版本冲突（常见于 Dart < 3.0），在 `pubspec.yaml` 底部添加：

```yaml
dependency_overrides:
  http: ^0.13.1
```

然后重新执行 `flutter pub get`。

### 2. Binding 替换（⚠️ 最关键步骤）

**⚠️ 强制检查项：必须删除原有的 `WidgetsFlutterBinding.ensureInitialized()`**

全局搜索 `ensureInitialized`，如果存在则删除。SDK 通过 `initFlutterBinding` 参数完成绑定初始化，重复调用会抛出 "Binding already initialized" 异常。

**自定义 Binding 类：**
```dart
/// 自定义 Binding：必须继承 ApmWidgetsFlutterBinding
/// 如果项目使用 Flutter Boost，改为：
/// class MyApmWidgetsFlutterBinding extends ApmWidgetsFlutterBinding with BoostFlutterBinding
class MyApmWidgetsFlutterBinding extends ApmWidgetsFlutterBinding {
  static WidgetsBinding? ensureInitialized() {
    MyApmWidgetsFlutterBinding();
    return WidgetsBinding.instance;
  }
}
```

### 3. NavigatorObserver 注册（⚠️ 必须）

**⚠️ 强制检查项：不注册则无法采集页面 PV，错误率指标（Dart异常数/PV次数）将失真。**

集成脚本会自动向 `MaterialApp.navigatorObservers` 注入 `ApmNavigatorObserver.singleInstance`，**MyApp 无需接收 observer 参数**：

```dart
class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'APM Demo',
      // 关键：注册 APM 路由监听器（集成脚本自动注入）
      navigatorObservers: <NavigatorObserver>[
        ApmNavigatorObserver.singleInstance,
      ],
      home: const HomePage(),
    );
  }
}
```

> ⚠️ **双注册陷阱**：同一个 observer 实例只能注册到一个 Navigator。若既在 `navigatorObservers` 中注册 `singleInstance`，又通过 `appRunner: (observer) => MyApp(observer)` 把 observer 传入 MyApp 再注册一次，会触发 `observer.navigator == null` 断言导致 widget 树构建失败（见 FAQ Q14）。保持 MyApp 构造不变（不接收 observer，`appRunner` 内直接 `return const MyApp();`）即可避免，`test/widget_test.dart` 中的 `const MyApp()` 也无需改动。

### 4. UmengApmSdk 初始化代码

**文件：** `lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:umeng_apm_sdk/umeng_apm_sdk.dart';
import 'package:umeng_common_sdk/umeng_common_sdk.dart';

void main() {
  // 1. 创建 APM SDK 实例
  final UmengApmSdk umengApmSdk = UmengApmSdk(
    name: 'my_flutter_app',           // 应用名称（对应 pubspec.yaml 的 name）
    bver: '1.0.0+1',                  // 版本号+构建号（对应 pubspec.yaml 的 version）
    enableLog: true,                   // 调试阶段开启，上线时改为 false
    enableTrackingPageFps: true,       // 开启帧率监测 (v2.1.3+)
    enableTrackingPagePerf: true,      // 开启页面性能监测 (v2.1.3+)
    // 关键：用自定义 Binding 替代 WidgetsFlutterBinding.ensureInitialized()
    initFlutterBinding: MyApmWidgetsFlutterBinding.ensureInitialized,
  );

  // 2. 初始化 SDK 并启动 App
  umengApmSdk.init(appRunner: (observer) {
    // 3. 初始化 Common SDK（必须在用户同意隐私政策后调用）
    UmengCommonSdk.initCommon(
      'YOUR_ANDROID_APPKEY',  // 替换为实际 Android AppKey
      'YOUR_IOS_APPKEY',      // 替换为实际 iOS AppKey
      'Umeng',                // 渠道标识
    );

    // 4. 启动 App（observer 已由 MaterialApp.navigatorObservers 注册，勿传入 MyApp，避免双注册）
    return const MyApp();
  });
}
```

**重要说明：**
- ⚠️ **`bver` 必须精确到构建号**（如 "1.0.0+1"），从 `pubspec.yaml` 的 `version` 字段读取，确保后台符号表解析正确
- ⚠️ **双端 AppKey 必须区分**：Android AppKey 和 iOS AppKey 分别从友盟后台获取
- ⚠️ **`initCommon()` 必须在用户同意隐私政策后调用**
- ⚠️ **初始化时机约束**：所有 `UmengCommonSdk.*` / `UmengApmSdk` 相关方法必须在 `runApp()` 之后调用（推荐放在首页 `initState` 或隐私政策同意回调中）。在 `main()` 的 `runApp()` 之前调用会因 Flutter Binding 未就绪而静默失败（App 正常启动但数据不上报）。

#### 4.1 激活脚本注入的注释模板（⚠️ 必须人工完成）

出于隐私合规考虑，集成脚本注入到 `main()` 的 APM 初始化代码是**注释状态的待激活模板**，脚本报告会标注“⚠️ 待办事项”。编译通过不代表 APM 已生效，需人工完成以下步骤：

1. 打开 `lib/main.dart`，找到 `// TODO: 请在用户同意隐私政策后添加 APM 初始化` 注释块
2. 取消整段注释（`UmengApmSdk(...)` + `init(appRunner: ...)`），确认 appkey 为真实值
3. 将激活后的初始化代码放到用户同意隐私政策的回调中（或验证阶段临时放在 `runApp` 之后直接调用）
4. **保持 `return const MyApp();` 不变**，勿将 observer 传入 MyApp（双注册风险见第 3 节警示）
5. 重新编译运行，按「运行验证」章节确认日志证据链

### 5. Android 端配置

#### 5.1 权限配置

**文件：** `android/app/src/main/AndroidManifest.xml`

在 `<manifest>` 标签内、`<application>` 标签之前，添加以下四行（如已存在则跳过）：

```xml
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>
<uses-permission android:name="android.permission.READ_PHONE_STATE"/>
<uses-permission android:name="android.permission.INTERNET"/>
```

#### 5.2 混淆配置（Release 必须）

**文件：** `android/app/proguard-rules.pro`（若不存在则新建）

```proguard
# 友盟 APM SDK 混淆规则（必须，否则 Release 包 APM 无法工作）
-keep class com.umeng.** {*;}
-keep class com.uc.** {*;}
-keepclassmembers class * {
    public <init> (org.json.JSONObject);
}
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}
```

确认 `android/app/build.gradle` 中 release buildType 引用了此文件：

```groovy
buildTypes {
    release {
        minifyEnabled true
        proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
    }
}
```

> 混淆配置仅在 Release 构建时生效，Debug 运行不受影响。

#### 5.3 (可选) MyApplication — Native 崩溃采集

**仅需要采集 Native 崩溃时执行此步骤。**

**新建文件：** `android/app/src/main/kotlin/<包路径>/MyApplication.kt`

> `<包路径>` 的确定方法：查看 `android/app/build.gradle` 中的 `namespace` 字段（如 `namespace "com.example.myapp"`），将 `.` 替换为 `/` 即为目录路径。

```kotlin
package com.example.myapp

import android.app.Application
import android.os.Bundle
import com.umeng.commonsdk.UMConfigure
import com.umeng.umcrash.UMCrash

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        // 配置 Native 采集开关（必须在 preInit 之前调用）
        val bundle = Bundle().apply {
            putBoolean(UMCrash.KEY_ENABLE_CRASH_JAVA, true)
            putBoolean(UMCrash.KEY_ENABLE_CRASH_NATIVE, true)
            putBoolean(UMCrash.KEY_ENABLE_CRASH_ALL, true)
            putBoolean(UMCrash.KEY_ENABLE_ANR, false)
            putBoolean(UMCrash.KEY_ENABLE_PA, false)
            putBoolean(UMCrash.KEY_ENABLE_LAUNCH, false)
            putBoolean(UMCrash.KEY_ENABLE_MEM, false)
            putBoolean(UMCrash.KEY_ENABLE_H5PAGE, false)
            putBoolean(UMCrash.KEY_ENABLE_POWER, false)
        }
        UMCrash.initConfig(bundle)

        // 预初始化
        UMConfigure.preInit(this, "YOUR_ANDROID_APPKEY", "UMENG",
            UMConfigure.DEVICE_TYPE_PHONE, "")
    }
}
```

**注册 Application：** 在 `AndroidManifest.xml` 的 `<application` 标签中新增 `android:name=".MyApplication"`：

```xml
<application
    android:name=".MyApplication"
    android:label="myapp"
    android:icon="@mipmap/ic_launcher">
```

**注意：** 如果项目是 Java（`android/app/src/main/java/` 目录存在），则创建 `MyApplication.java` 而非 `.kt`。Kotlin 和 Java 版本**只能选一个**，不要同时创建，否则报 duplicate class。

### 6. iOS 端配置（可选，仅 Native 崩溃采集）

**仅需要采集 Native 崩溃时执行此步骤。**

#### 6.1 Swift 项目（flutter create 默认）

**文件：** `ios/Runner/AppDelegate.swift`

在 `didFinishLaunchingWithOptions` 中、`GeneratedPluginRegistrant.register` 之前添加：

```swift
import UMCommon
import UMAPM

// 配置 APM 采集开关
let config = UMAPMConfig.defaultConfig()
config?.crashAndBlockMonitorEnable = true   // 崩溃和卡顿
config?.launchMonitorEnable = true           // 启动监控
config?.memMonitorEnable = false             // 内存
config?.oomMonitorEnable = false             // OOM
config?.networkEnable = true                 // 网络
UMCrashConfigure.setAPMConfig(config)

// 在用户同意隐私政策后初始化
// UMConfigure.initWithAppkey("YOUR_IOS_APPKEY", channel: "App Store")
```

> 如果 `UMAPMConfig.defaultConfig()` 编译失败，尝试 `UMAPMConfig.default()`（取决于 SDK 版本的 Swift 命名适配）。

#### 6.2 Objective-C 项目

**文件：** `ios/Runner/AppDelegate.m`

```objectivec
#import <UMCommon/UMCommon.h>
#import <UMAPM/UMCrashConfigure.h>
#import <UMAPM/UMAPMConfig.h>

// 在 didFinishLaunchingWithOptions 方法内、GeneratedPluginRegistrant 之前添加：
UMAPMConfig *config = [UMAPMConfig defaultConfig];
config.crashAndBlockMonitorEnable = YES;
config.launchMonitorEnable = YES;
config.memMonitorEnable = NO;
config.oomMonitorEnable = NO;
config.networkEnable = YES;
[UMCrashConfigure setAPMConfig:config];

// 在用户同意隐私政策后初始化
// [UMConfigure initWithAppkey:@"YOUR_IOS_APPKEY" channel:@"App Store"];
```

### 7. 删除已有原生 SDK 依赖（如存在）

如果原生工程中已有友盟 SDK 依赖，**必须删除**，否则与 Flutter SDK 内置的原生 SDK 冲突：

**Android** — `android/app/build.gradle`：
```groovy
dependencies {
    // 删除或注释以下行（如存在）：
    // implementation 'com.umeng.umsdk:common:x.x.x'
    // implementation 'com.umeng.umsdk:asms:x.x.x'
    // implementation 'com.umeng.umsdk:apm:x.x.x'
}
```

**iOS** — `ios/Podfile`：
```ruby
# 删除或注释以下行（如存在）：
# pod 'UMCommon'
# pod 'UMAPM'
# pod 'UMDevice'
```

删除后重新执行 `flutter pub get` 和 `(cd ios && pod install)`。

### 8. 进阶功能

#### 8.1 监听滚动 FPS（v2.1.3+）

用 `ApmScrollController` 替代原生 `ScrollController`：

```dart
import 'package:umeng_apm_sdk/umeng_apm_sdk.dart';

// 将 ScrollController() 替换为 ApmScrollController()，其余用法完全一致
final ScrollController _scrollController = ApmScrollController();
```

#### 8.2 自定义异常上报

```dart
import 'package:umeng_apm_sdk/umeng_apm_sdk.dart';

try {
  // 业务代码
} catch (e, stackTrace) {
  ExceptionTrace.captureException(
    exception: Exception(e),       // 必传：异常摘要
    stack: stackTrace.toString(),  // 可选：堆栈
    extra: {"userId": "123"},      // 可选：自定义属性 Map<String, dynamic>
  );
}
```

**Isolate 异常捕获：**

```dart
import 'dart:isolate';
import 'package:umeng_apm_sdk/umeng_apm_sdk.dart';

Isolate isolate = await Isolate.spawn(myIsolateEntry, []);
isolate.addErrorListener(RawReceivePort((pair) {
  ExceptionTrace.captureException(
    exception: Exception(pair[0]),
    stack: pair[1].toString(),
  );
}).sendPort);
```

#### 8.3 异常黑白名单（ErrorFilter）

```dart
UmengApmSdk(
  name: 'my_app',
  bver: '1.0.0+1',
  errorFilter: {
    "mode": "ignore",  // ignore=黑名单（命中的不上报），match=白名单（仅命中的上报）
    "rules": [RegExp('NetworkError'), 'TimeoutException'],  // 规则之间为"或"关系
  },
  initFlutterBinding: MyApmWidgetsFlutterBinding.ensureInitialized,
).init(appRunner: (observer) => const MyApp());
```

#### 8.4 Flutter Boost 兼容（v2.2.0+）

如果使用 Flutter Boost 插件，Binding 类需同时混入 `BoostFlutterBinding`：

```dart
import 'package:flutter_boost/flutter_boost.dart';
import 'package:umeng_apm_sdk/umeng_apm_sdk.dart';

class MyApmWidgetsFlutterBinding extends ApmWidgetsFlutterBinding
    with BoostFlutterBinding {
  static WidgetsBinding? ensureInitialized() {
    MyApmWidgetsFlutterBinding();
    return WidgetsBinding.instance;
  }
}
```

#### 8.5 Flutter Module 嵌入原生工程

初始化时设置 `projectType: 1`：

```dart
UmengApmSdk(
  name: 'my_flutter_module',
  bver: '1.0.0+1',
  projectType: 1,  // Flutter Module（默认为 0 即 Flutter App）
  initFlutterBinding: MyApmWidgetsFlutterBinding.ensureInitialized,
).init(appRunner: (observer) => const MyApp());
```

同时必须执行步骤 4（Native 端配置），在宿主 App 中完成 preInit。

## 采样率限制表

| 版本 | Flutter PV 采样率 | 单设备 Dart 异常/天 | 单设备性能日志/天 |
|------|------------------|-------------------|----------------|
| 免费版 | 5%（不可更改） | 20 条 | 200 条 |
| 专业版 | 最高 5% | 40 条 | 500 条 |
| 尊享版 | 最高 100% | 120 条 | 1000 条 |

> ⚠️ 免费版采样率固定 5%，验证时务必添加设备白名单（U-APM 后台 → 设备管理 → 通用采样设置）。

## 运行验证

### 验证前提

- 已完成「4.1 激活注释模板」，appkey 为真实值（占位符下初始化日志可输出但数据上报不可验证）
- 免费版 5% 采样率下建议先添加设备白名单（见 FAQ Q3）

### 日志关键词（SDK 2.3.7+ 实测）

SDK 2.3.7+ 输出中文日志，旧版为英文，两套关键词均有效：

| 证据链顺序 | 日志关键词（2.3.7+） | 旧版英文关键词 |
|-----------|-------------------|--------------|
| 1. 初始化 | `成功接收APM Native SDK 初始化状态` | `apm sdk init success` / `initialized, version=2.x.x` |
| 2. 采样 | `采样率命中 true` | - |
| 3. 异常采集 | `处理异常 日志数N` | - |
| 4. 上报 | `fluttererror-日志上报成功` | `page PV tracked` |

```bash
adb logcat -d | grep -i 'umeng\|UMLog\|apm\|ApmSdk'
```

### ⚠️ 验证注意事项（实测经验，极易误判）

1. **必须冷启动验证**：`adb shell am force-stop <包名>` 后再启动。用 `am start` 热重启已存活进程会导致 APM 初始化时序错乱，轮询永不成功、异常不进 APM 通道
2. **泛化上传日志不能作为证据**：`crashsdk uploading logs`、`efs.send_log` 等日志是底层通道通用输出，**不代表 Flutter 异常已上传**，必须以上表证据链为准
3. **后台查看位置**：U-APM 后台的 **Flutter 异常/自定义日志分类**（非原生崩溃列表），数据有分钟~小时级延迟

## 注意事项

- **Swift Package Manager（SPM）**：友盟 Flutter SDK 当前不支持 SPM。Flutter 3.44+ 新建 iOS 工程默认启用 SPM 且无 Podfile，集成脚本的项目验证阶段会检测 pbxproj 中的 `FlutterGeneratedPluginSwiftPackage` 标记并**直接阻塞**，请按下方「SPM → CocoaPods 迁移」章节处理。请关注友盟插件官方 SPM 适配进展。
- **插件兼容性自动修复**：`umeng_common_sdk 1.3.1` 存在打包缺陷（残留双实现桩文件、compileSdkVersion 过低），`umeng_apm_sdk`（如 2.3.7）同样存在 compileSdkVersion 33 缺陷，在 Flutter 3.44+/Gradle 9.1 环境下编译必失败。集成脚本已在 `flutter pub get` 后通过 `plugin_fixer.py` 自动修复 pub cache 中的插件源码（删除桩文件、compileSdkVersion 33→34），失败不阻塞流程。
- **回滚策略**：编译验证失败时默认保留集成代码（便于排查，完整构建日志落盘至 `build/umeng_integration_build.log`）；如需失败自动回滚，添加 `--rollback-on-failure` 参数。

## SPM → CocoaPods 迁移

Flutter 3.44+ 新建 iOS 工程默认启用 Swift Package Manager（SPM）且不再生成 Podfile，而友盟 Flutter SDK 依赖 CocoaPods 分发原生 SDK。SPM 工程执行 `flutter build ios` **永远不会生成 Podfile**，必须迁移到 CocoaPods：

1. **关闭 Flutter 的 SPM 支持**：
   ```bash
   flutter config --no-enable-swift-package-manager
   ```
2. **重生成 ios/ 目录**（先备份），或手工移除 pbxproj 中的 `FlutterGeneratedPluginSwiftPackage` 引用：
   ```bash
   # 注意：flutter create 可能卡在签名证书交互选择，用管道方式处理
   mv ios ios.bak
   printf '1\n' | flutter create --platforms=ios . < /dev/null
   ```
3. **确认 Podfile**：`ios/Podfile` 存在且 `platform :ios, '13.0'` 一行已取消注释（与 `IPHONEOS_DEPLOYMENT_TARGET` 一致，≥13.0）
4. **补 xcconfig 引用（极易遗漏）**：在 `ios/Flutter/Debug.xcconfig` 与 `ios/Flutter/Release.xcconfig` 首行分别添加：
   ```
   #include? "Pods/Target Support Files/Pods-Runner/Pods-Runner.debug.xcconfig"   // Debug.xcconfig
   #include? "Pods/Target Support Files/Pods-Runner/Pods-Runner.release.xcconfig" // Release.xcconfig
   ```
   遗漏此步时 `pod install` 会告警 base configuration 未设置
5. 重新运行集成脚本（或手动 `cd ios && pod install`）

## 常见问题

### Q1: 报错 "Binding already initialized" 崩溃？

**A**: 代码中仍存在 `WidgetsFlutterBinding.ensureInitialized()`。全局搜索 `ensureInitialized`，删除所有 `WidgetsFlutterBinding.ensureInitialized()` 调用。SDK 通过 `initFlutterBinding` 参数完成绑定，不能重复。

### Q2: NavigatorObserver 未注册导致 PV=0？

**A**: 必须将 `ApmNavigatorObserver` 注入 `MaterialApp.navigatorObservers`。不注册则无法采集页面 PV，错误率指标（Dart异常数/PV次数）将失真。确认根 Widget 接收 `NavigatorObserver` 参数并正确传递给 `MaterialApp`。

### Q3: 采样率限制导致看不到数据？

**A**: 免费版默认 5% 采样率不可更改，验证时需添加设备白名单：
1. 开启 `enableLog: true`，在日志中搜索 `umid` 获取设备 UMID
2. 登录 U-APM 后台（https://apm.umeng.com）→ 设备管理 → 通用采样设置 → 添加 UMID 到白名单
3. 不卸载 App，将设备时间改为 8 小时后冷启动，白名单立即生效

### Q4: bver 不正确导致符号表解析失败？

**A**: `bver` 必须精确到构建号（如 "1.0.0+1"），对应 `pubspec.yaml` 的 `version` 字段。错误的 bver 会导致后台符号表无法正确映射，崩溃堆栈无法解析。

### Q5: Flutter Boost 兼容问题？

**A**: 如果使用 Flutter Boost 插件（v2.2.0+），Binding 类需同时混入 `BoostFlutterBinding`：
```dart
class MyApmWidgetsFlutterBinding extends ApmWidgetsFlutterBinding
    with BoostFlutterBinding {
  static WidgetsBinding? ensureInitialized() {
    MyApmWidgetsFlutterBinding();
    return WidgetsBinding.instance;
  }
}
```

### Q6: flutter pub get 依赖冲突？

**A**: 常见于 Dart < 3.0 的 `http` 包版本冲突。在 `pubspec.yaml` 底部添加：
```yaml
dependency_overrides:
  http: ^0.13.1
```
然后重新执行 `flutter pub get`。

### Q7: iOS pod install 失败？

**A**: 执行以下步骤：
```bash
cd ios
pod repo update
pod install --repo-update
```
检查 `ios/Podfile` 中 `platform :ios` 是否与 `IPHONEOS_DEPLOYMENT_TARGET` 一致（≥13.0）。若使用错误的项目文件，确认使用 `.xcworkspace` 而非 `.xcodeproj`。

### Q8: 原生 SDK 依赖冲突（duplicate class）？

**A**: 可能原因：
- 同时创建了 `MyApplication.kt` 和 `MyApplication.java`（只能保留一个）
- 原生工程中已有友盟 SDK 依赖，与 Flutter SDK 内置的冲突

**解决：** 删除原生工程中的友盟依赖（见 SDK集成内容 第7节），然后执行 `flutter clean && flutter pub get`。

### Q9: Release 构建混淆问题？

**A**: 最常见原因为未配置混淆规则。确认 `android/app/proguard-rules.pro` 中已添加友盟 keep 规则（见 SDK集成内容 5.2），且 `build.gradle` 中 `minifyEnabled true` 时引用了该文件。混淆配置仅在 Release 构建时生效，Debug 运行不受影响。

### Q10: umeng-cli trace 使用说明？

**A**: 这是 Skill 调用埋点上报，用于统计 Skill 实际使用情况：

- Skill 每次被加载：上报 `{"skill_name":"flutter-apm-integration"}`
- 拿到 Appkey（从已集成的统计 SDK 复用）：补报 `{"skill_name":"flutter-apm-integration","appkey":"<appkey>"}`

仅上报「哪个 Skill 在哪个 App 上被用」，不涉及任何工程源码内容，可放心执行。

### Q11: Android 编译报错 "Redeclaration: class UmengCommonSdkPlugin"？

**A**: `umeng_common_sdk 1.3.1` 打包缺陷——插件同时包含平台实现桩文件与预编译产物，新版 Gradle 下类重复定义。集成脚本已通过 `plugin_fixer.py` 自动修复；若需手动修复（删除 pub cache 中的桩文件）：

```bash
PUB_CACHE_DIR=${PUB_CACHE:-$HOME/.pub-cache}
PLUGIN_DIR="$PUB_CACHE_DIR/hosted/pub.dev/umeng_common_sdk-1.3.1"
rm -f "$PLUGIN_DIR/android/src/main/kotlin/com/umeng/umeng_common_sdk/UmengCommonSdkPlugin.kt"
```

### Q12: iOS 编译报错 "Duplicate interface definition for class 'UmengCommonSdkPlugin'"？

**A**: 同 Q11，为 `umeng_common_sdk 1.3.1` 双实现桩文件缺陷的 iOS 端表现。集成脚本已通过 `plugin_fixer.py` 自动修复；手动修复：

```bash
PUB_CACHE_DIR=${PUB_CACHE:-$HOME/.pub-cache}
PLUGIN_DIR="$PUB_CACHE_DIR/hosted/pub.dev/umeng_common_sdk-1.3.1"
rm -f "$PLUGIN_DIR/ios/Classes/UmengCommonSdkPlugin.swift"
```

### Q13: Android 编译报错 "requires ... compile against version 34"？

**A**: `umeng_common_sdk` 插件的 `compileSdkVersion 33` 与新版 AGP/Gradle 环境不兼容。集成脚本已通过 `plugin_fixer.py` 自动修复（33→34）；手动修复：

```bash
PUB_CACHE_DIR=${PUB_CACHE:-$HOME/.pub-cache}
PLUGIN_DIR="$PUB_CACHE_DIR/hosted/pub.dev/umeng_common_sdk-1.3.1"
sed -i '' 's/compileSdkVersion 33/compileSdkVersion 34/' "$PLUGIN_DIR/android/build.gradle"
```

> 以上三个问题均源于 pub cache 中的插件源码，手动修复后需执行 `flutter clean` 再重新编译；若重新执行 `flutter pub get` 触发插件重新下载，需再次修复（集成脚本会自动处理）。

### Q14: 运行时报 `observer.navigator == null` 断言，APM 卡等 Native 初始化？

**A**: 典型的 **observer 重复注册**。判定特征：logcat 出现 `NavigatorState.initState` 断言失败（`observer.navigator == null`）+ APM Dart 层日志卡在“等待接收APM Native SDK 初始化结束状态”，且无任何报错直接指向 observer。

**原因**：同一个 `ApmNavigatorObserver.singleInstance` 被注册了两次——既在 `MaterialApp.navigatorObservers` 中注册，又通过 `appRunner: (observer) => MyApp(observer)` 传入 MyApp 再注册一次。

**解决**：保持 MyApp 构造不变（不接收 observer），仅保留 `MaterialApp.navigatorObservers` 中的注册，`appRunner` 内直接 `return const MyApp();`（见第 3 节与 4.1 节）。旧版脚本注入过 `MyApp(observer)` 模板的工程，重跑脚本时会收到旧模板检测告警，按上述方式手工清理即可。

> **widget_test.dart 联动适配**：若已把 MyApp 构造改为接收 observer（旧模板或官方文档模式），模板自带的 `test/widget_test.dart` 中 `pumpWidget(const MyApp())` 会编译失败（`flutter analyze` / `flutter test` 报 error）。适配二选一：① 恢复 MyApp 构造为不接收 observer（推荐，测试无需改动）；② 同步修改测试为 `pumpWidget(MyApp(ApmNavigatorObserver.singleInstance))`。重跑集成脚本时会自动检测并告警。

## 参考资源

### 官方文档
- **友盟APM Flutter SDK集成文档**: https://developer.umeng.com/docs/193624/detail/2521038
- **友盟开发者中心**: https://developer.umeng.com
- **Flutter Common SDK集成**: https://developer.umeng.com/docs/119267/detail/174923

### SDK资料
- **Flutter统计SDK集成指南**: `集成文档/Flutter/Flutter-统计SDK-集成指南.md`
- **APM Flutter SDK集成指南**: `集成文档/Flutter/Flutter-APM-SDK-集成指南.md`

### 相关Skills
- **Flutter统计SDK集成**: `scripts/umeng-flutter-analytics-integration/` (APM SDK前置依赖)
- **Android APM集成**: `scripts/umeng-apm-integration/`
- **iOS APM集成**: `scripts/umeng-ios-apm-integration/`

### 工具脚本

| 脚本 | 功能 |
|------|------|
| `scripts/umeng-flutter-apm-integration/main.py` | 主工作流编排 |
| `scripts/umeng-flutter-apm-integration/env_checker.py` | 环境检查 |
| `scripts/umeng-flutter-apm-integration/project_validator.py` | 项目验证 |
| `scripts/umeng-flutter-apm-integration/sdk_integrator.py` | APM SDK增量集成 |
| `scripts/umeng-flutter-apm-integration/plugin_fixer.py` | 插件兼容性自动修复（umeng_common_sdk 1.3.1 打包缺陷） |
| `scripts/umeng-flutter-apm-integration/device_detector.py` | 设备检测（flutter devices） |
| `scripts/umeng-flutter-apm-integration/rollback.py` | 回滚恢复 |

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/193624/detail/2521038
- Flutter开发文档: https://docs.flutter.dev/
- 合规指南: https://developer.umeng.com/docs/193624/detail/194588
