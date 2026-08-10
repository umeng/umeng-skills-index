## 友盟Flutter统计SDK集成Skill

## 功能说明

自动将友盟统计 Flutter SDK 集成到现有 Flutter 项目中（覆盖 Android + iOS 双端），简化 SDK 集成流程。

### 核心功能

1. ✅ **环境检查** - 检测 Flutter SDK、Dart SDK、Android SDK、CocoaPods
2. ✅ **项目验证** - 验证 Flutter 项目完整性（pubspec.yaml、android/、ios/）
3. ✅ **参数交互** - 引导输入 Android AppKey、iOS AppKey 和 channel
4. ✅ **SDK集成** - 自动完成 pubspec.yaml 依赖、Android 原生配置、Dart 初始化代码
5. ✅ **编译验证** - 集成后 flutter build 编译验证
6. ✅ **SDK验证** - 通过 adb logcat 验证 Android 端 SDK 上报
7. ✅ **回滚机制** - 提供回滚脚本恢复修改

### 支持的项目类型

- ✅ 标准 Flutter App（`flutter create` 生成）
- ✅ Flutter Module（嵌入原生工程）

### 前置要求

### 必需工具
- ✅ Flutter SDK (>= 2.0.0)
- ✅ Dart SDK (>= 2.12.0，空安全)
- ✅ Android SDK + minSdkVersion >= 21
- ✅ Android Gradle Plugin (AGP >= 7.0，推荐 >= 8.0)
- ✅ Gradle JDK 17（AGP 8.0+ 强制要求）
- ✅ iOS Deployment Target >= 10.0（推荐 >= 14.0）
- ✅ CocoaPods (>= 1.10，仅 macOS)

### 可选工具
- ⚠️ adb 工具（仅 SDK 验证时需要）
- ⚠️ Android 设备或模拟器（仅 SDK 验证时需要）
- ⚠️ iOS 设备或模拟器（仅 macOS 下 SDK 验证时需要）


## 使用方式

### 基本用法（交互式）

```bash
python scripts/umeng-flutter-analytics-integration/main.py --project-path /path/to/flutter/project
```

运行后会引导你输入:
- Android AppKey: 友盟后台 Android 平台应用标识
- iOS AppKey: 友盟后台 iOS 平台应用标识
- channel: 应用分发渠道（如: Umeng, googleplay, App Store）

⚠️ **注意：** Android AppKey 和 iOS AppKey 是不同的，请勿填反！AppKey 获取路径：友盟后台（https://www.umeng.com）→ 应用管理 → 对应应用 → 应用信息。

### 非交互式模式（传递参数）

```bash
python scripts/umeng-flutter-analytics-integration/main.py \
  --project-path /path/to/flutter/project \
  --android-key YOUR_ANDROID_APPKEY \
  --ios-key YOUR_IOS_APPKEY \
  --channel Umeng
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--project-path` | ✅ | - | Flutter 项目路径（包含 pubspec.yaml 的目录） |
| `--android-key` | ❌ | 占位符 | Android 平台友盟 AppKey |
| `--ios-key` | ❌ | 占位符 | iOS 平台友盟 AppKey |
| `--channel` | ❌ | `Umeng` | 渠道标识 |
| `--skip-build` | ❌ | `false` | 跳过编译验证步骤 |
| `--yes` | ❌ | `false` | 跳过所有确认提示（非交互式模式） |
| `--timeout` | ❌ | `1800` | 编译超时时间（秒），默认 1800 秒（30 分钟） |
| `--no-trace` | ❌ | `false` | 禁用 Skill 使用情况上报（umeng-cli trace） |
| `--rollback-on-failure` | ❌ | `false` | 编译失败时自动回滚（默认保留集成代码以便排查） |

## 工作流程

```
步骤1: 🔍 环境检查 (Flutter/Dart/Android/CocoaPods)
  ↓
步骤2: 📋 项目验证 (pubspec.yaml + android/ + ios/ 结构)
  ↓
步骤3: ⚙️ 参数配置 (Android AppKey + iOS AppKey + channel)
  ↓
步骤4: 💾 项目备份 (ZIP 全量备份)
  ↓
步骤5: 🔧 SDK集成
  ├─ pubspec.yaml 添加 umeng_common_sdk
  ├─ flutter pub get
  ├─ Android: AndroidManifest 权限 + MyApplication + 混淆规则
  ├─ iOS: pod install
  └─ lib/main.dart 注入初始化代码
  ↓
步骤6: 🏗️ 编译验证 (flutter build)
  ↓
步骤7: 📊 集成报告
```

## SDK集成内容

### 1. pubspec.yaml 依赖配置

在项目 `pubspec.yaml` 的 `dependencies:` 下添加：

```yaml
dependencies:
  flutter:
    sdk: flutter
  umeng_common_sdk: ^1.2.3
```

执行 `flutter pub get` 获取依赖，预期输出包含 `+ umeng_common_sdk 1.x.x`。

**http 依赖冲突处理：** 如果报 `http` 包版本冲突，在 `pubspec.yaml` 底部添加：

```yaml
dependency_overrides:
  http: ^0.13.1
```

然后重新执行 `flutter pub get`。

### 2. Android 端配置

⚠️ **Gradle 插件警告**：AGP 7.0+ 要求 Gradle JDK 17+。若项目使用 AGP 8.0+，还需在 `gradle.properties` 中启用 namespace：
```properties
android.nonTransitiveRClass=false
```

⚠️ **不要手动添加 `packagingOptions` 规则**，Gradle 插件会自动处理。若项目使用 Kotlin DSL (`build.gradle.kts`)，将 `implementation(...)` 改为 `implementation(libs.umeng.common)` 等。

#### 2.1 AndroidManifest.xml 权限

在 `android/app/src/main/AndroidManifest.xml` 的 `<manifest>` 标签内、`<application>` 标签之前，添加以下四行权限声明（如已存在则跳过）：

```xml
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>
<uses-permission android:name="android.permission.READ_PHONE_STATE"/>
<uses-permission android:name="android.permission.INTERNET"/>
```

#### 2.2 创建 MyApplication 类

**文件：** `android/app/src/main/kotlin/<包路径>/MyApplication.kt`

`<包路径>` 的确定方法：查看 `android/app/build.gradle` 中的 `namespace` 字段（如 `namespace "com.example.myapp"`），将 `.` 替换为 `/` 即为目录路径（`com/example/myapp/`）。若 build.gradle 无 namespace 字段（旧版 AGP），则查看 `AndroidManifest.xml` 中的 `package` 属性。

**Kotlin 版本：**
```kotlin
package com.example.myapp

import android.app.Application
import com.umeng.commonsdk.UMConfigure

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // 预初始化：不采集设备信息，不上报数据，耗时极少
        UMConfigure.preInit(this, "YOUR_ANDROID_APPKEY", "Umeng")
    }
}
```

**Java 版本**（当项目使用 Java 时）：
```java
package com.example.myapp;

import android.app.Application;
import com.umeng.commonsdk.UMConfigure;

public class MyApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        UMConfigure.preInit(this, "YOUR_ANDROID_APPKEY", "Umeng");
    }
}
```

⚠️ Kotlin 和 Java 版本只能选一个，不要同时创建。

#### 2.3 注册 Application

在 `AndroidManifest.xml` 的 `<application>` 标签中新增 `android:name=".MyApplication"` 属性，保留其他已有属性（`android:label`、`android:icon` 等）不变。

修改前示例：
```xml
<application
    android:label="myapp"
    android:icon="@mipmap/ic_launcher">
```

修改后：
```xml
<application
    android:name=".MyApplication"
    android:label="myapp"
    android:icon="@mipmap/ic_launcher">
```

#### 2.4 混淆配置（Release 构建必须）

**文件：** `android/app/proguard-rules.pro`（若不存在则新建）

在文件末尾追加：

```proguard
# 友盟 SDK 混淆规则
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

确认 `android/app/build.gradle` 中 release buildType 引用了此文件（若不存在则新建）：

```groovy
android {
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

> 混淆配置仅在 Release 构建时生效，Debug 运行不受影响。

### 3. iOS 端配置

**🎉 零原生代码配置！**

对于 `flutter create` 生成的默认 Swift 项目，**iOS 端无需修改任何原生代码**。Dart 层的 `UmengCommonSdk.initCommon()` 会通过 Platform Channel 自动桥接 iOS 原生初始化。这是 Flutter SDK 的关键优势。

仅需执行 `pod install` 安装原生依赖：

```bash
cd ios && pod install
```

> 仅当隐私政策弹窗需要在 Native 层实现时，才需修改 `ios/Runner/AppDelegate.swift`。

**Swift 项目原生初始化（可选，仅 Native 层隐私弹窗场景）：**

**文件：** `ios/Runner/AppDelegate.swift`

在 `didFinishLaunchingWithOptions` 中、`GeneratedPluginRegistrant.register` 之前添加：

```swift
// 在用户同意隐私政策的回调中调用
// UMConfigure.initWithAppkey("YOUR_IOS_APPKEY", channel: "App Store")
```

> 注意：需要先 `cd ios && pod install` 确保 UMCommon 模块可用后，才能取消注释此行。

### 4. Dart 层初始化（核心步骤）

**文件：** `lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:umeng_common_sdk/umeng_common_sdk.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  bool _privacyAgreed = false;

  /// 用户同意隐私政策后调用此方法
  void _initUmengSdk() {
    UmengCommonSdk.initCommon(
      'YOUR_ANDROID_APPKEY',  // Android 平台 AppKey
      'YOUR_IOS_APPKEY',      // iOS 平台 AppKey
      'Umeng',                // 渠道标识
    );
    UmengCommonSdk.setPageCollectionModeAuto();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: Center(
          child: _privacyAgreed
              ? const Text('SDK 已初始化，数据开始上报')
              : ElevatedButton(
                  onPressed: () {
                    setState(() => _privacyAgreed = true);
                    _initUmengSdk();
                  },
                  child: const Text('同意隐私政策并初始化'),
                ),
        ),
      ),
    );
  }
}
```

**关键规则：**
- `initCommon()` 必须在用户同意隐私政策后调用，否则违反工信部合规要求
- 如果用户不同意，**不能**调用 `initCommon()`
- 后续每次冷启动，Android 端 `preInit()` 在 Application.onCreate 中自动执行；`initCommon()` 在用户已授权的情况下应尽早调用
- 所有 `UmengCommonSdk.*` 方法必须在 `runApp()` 之后调用（推荐放在首页 `initState` 或隐私政策同意回调中）。在 `main()` 的 `runApp()` 之前调用会因 Flutter Binding 未就绪而静默失败（App 正常启动但数据不上报）。

**渠道标识说明：** Dart 层 `initCommon` 的 channel 参数为最终生效值。Android 和 iOS 可填相同值（如 `'Umeng'`），也可按平台区分（Android 填分发渠道如 `'xiaomi'`，iOS 填 `'App Store'`）。

### 5. 功能 API 参考

以下 API 在 Android 和 iOS 双端通用，均为静态方法：

**自定义事件：**
```dart
// 属性值支持：String、int、double、long
// 不支持：NULL、bool、Map、数组
UmengCommonSdk.onEvent("eventName", {
  "key1": "stringValue",
  "key2": 123,
  "key3": 4.56,
});
```

**用户账号：**
```dart
UmengCommonSdk.onProfileSignIn("user_id");   // 登录
UmengCommonSdk.onProfileSignOff();            // 登出
```

**页面采集：**
```dart
// 二选一：
UmengCommonSdk.setPageCollectionModeAuto();    // 自动（推荐）
UmengCommonSdk.setPageCollectionModeManual();  // 手动

// 手动模式下需配对调用：
UmengCommonSdk.onPageStart("pageName");  // 进入页面
UmengCommonSdk.onPageEnd("pageName");    // 离开页面
```

## 常见问题

### Q1: 初始化后后台看不到数据？

**A**: 按以下顺序排查：
1. AppKey 是否正确（Android 和 iOS 的 AppKey 不同，确认没有填反）
2. Android 端是否创建了 MyApplication 并在 Manifest 中注册（`android:name=".MyApplication"`）
3. Android 端 `INTERNET` 权限是否声明
4. 是否在用户同意隐私政策后调用了 `initCommon()`
5. 数据有 1~5 分钟延迟，稍后刷新后台
6. 是否开启了代理/VPN 拦截了请求

### Q2: `flutter pub get` 报依赖冲突？

**A**: 在 `pubspec.yaml` 底部添加：
```yaml
dependency_overrides:
  http: ^0.13.1
```
然后重新执行 `flutter pub get`。

### Q3: iOS `pod install` 失败？

**A**: 执行以下命令：
```bash
cd ios
pod repo update
pod install --repo-update
```
检查 `ios/Podfile` 中 `platform :ios` 版本是否与 `IPHONEOS_DEPLOYMENT_TARGET` 一致（≥13.0）。

### Q4: 编译报 duplicate class？

**A**: 检查是否同时创建了 `MyApplication.kt` 和 `MyApplication.java`，只能保留一个。或检查原生工程中是否已有友盟 SDK 依赖（`com.umeng.umsdk:common`），如有则删除。

### Q5: Flutter Module 嵌入原生工程如何初始化？

**A**:
- Android：在宿主 App 的 Application.onCreate() 中调用 `UMConfigure.preInit()`
- iOS：在宿主 AppDelegate 中调用 `[UMConfigure initWithAppkey:channel:]`
- Flutter 层：在获得隐私授权后调用 `UmengCommonSdk.initCommon()`

### Q6: iOS 端 IDFA 采集？

**A**: iOS 14.5+ 需要 ATT 授权：
1. 在 `ios/Runner/Info.plist` 中添加：
```xml
<key>NSUserTrackingUsageDescription</key>
<string>我们需要您的授权来提供个性化服务</string>
```
2. 在适当时机调用 `ATTrackingManager.requestTrackingAuthorization`。

### Q7: Android 端如何延迟初始化？

**A**:
1. `preInit()` 必须在 `Application.onCreate()` 中调用（不采集信息，耗时极少）
2. `initCommon()` 可在用户同意隐私政策后延迟调用
3. 不能遗漏 `initCommon()`，否则 SDK 不上报数据

### Q8: 如何验证 SDK 集成成功？

**A**: 运行应用并触发初始化后，查看日志：

**Android：**
```bash
adb logcat -d | grep -i "umeng\|UMLog\|MobClick"
```

**成功判定标准：** 日志出现 `安卓依赖版本检查成功`、`setWraperType:flutter1.0 success`、`setPageCollectionModeAuto`、`module init:azio` 等关键词。

示例成功日志（实测内容）：
```
E UMLog   : 安卓依赖版本检查成功
I UMLog   : setWraperType:flutter1.0 success
I UMLog   : setPageCollectionModeAuto
I MobclickAgent: module init:azio
```

> **补充说明：** `UMLog Reflect:` 日志和 E 级别输出为正常日志，不作为失败依据；`检测到未调用隐私授权API` 是 preInit 后未授权场景的预期提示。

**iOS：** 在 Xcode Console 中过滤 `umeng`，判定标准同上。

> **验证用途提示：** 出于隐私合规考虑，集成脚本注入的 `_initUmengSdk()` 函数**没有自动调用点**（仅留 TODO 注释）。验证时需临时激活：在首页 `initState`（或 `runApp` 后的任意位置）添加 `_initUmengSdk();` 调用，重新运行后按上述标准判定；验证完成后移除临时调用，或替换为正式的隐私同意回调。

### Q9: 为什么集成前 AI Agent 会先执行 umeng-cli trace？

**A**: 这是 Skill 调用埋点上报，用于统计 Skill 实际使用情况：

- Skill 每次被加载：上报 `{"skill_name":"umeng-flutter-analytics-integration"}`
- 拿到新 Appkey：补报 `{"skill_name":"umeng-flutter-analytics-integration","appkey":"<appkey>"}`

仅上报「哪个 Skill 在哪个 App 上被用」，不涉及任何工程源码内容，可放心执行。

### Q10: 运行时验证说明

⚠️ **重要：** 运行时验证前，必须确保应用已配置真实 appkey。若当前使用占位符（如 `YOUR_ANDROID_APPKEY`），需先向用户索取真实 appkey，替换后重新编译，再进行运行时验证。占位符 appkey 下 SDK 初始化日志虽能输出，但无法验证数据上报的完整性。

**后台验证（需人工确认）：**
1. 在 App 中触发一个自定义事件：
```dart
UmengCommonSdk.onEvent("integration_test", {"result": "success"});
```
2. 登录友盟+后台：https://mobile.umeng.com → 对应应用 → 「实时日志」
3. 等待 1~5 分钟，确认出现 `integration_test` 事件
4. 若 10 分钟后仍无数据，按 Q1 排查

## 故障排查 (Troubleshooting)

### 编译错误：duplicate class

**症状：**
```
Duplicate class com.umeng.commonsdk.UMConfigure found in modules
```

**原因：** 同时存在 Kotlin 和 Java 版本的 MyApplication，或原生工程中已有友盟 SDK 依赖。

**解决：**
1. 检查是否同时创建了 `MyApplication.kt` 和 `MyApplication.java`，只保留一个
2. 检查 `android/app/build.gradle` 中是否已有 `com.umeng.umsdk:common` 依赖，如有则删除
3. 执行 `flutter clean` 后重新构建

---

### `flutter pub get` 依赖冲突

**症状：**
```
Because myapp depends on umeng_common_sdk which depends on http ^0.13.1
```

**解决：**
```yaml
dependency_overrides:
  http: ^0.13.1
```

---

### iOS `pod install` 失败

**症状：**
```
[!] Unable to find a specification for `UMCommon`
```

**解决：**
```bash
cd ios
pod repo update
pod install --repo-update
```

检查 `ios/Podfile` 中 `platform :ios` 版本是否与 `IPHONEOS_DEPLOYMENT_TARGET` 一致（≥13.0）。

---

### SDK 初始化失败

**症状：** 运行应用后日志显示
```
appkey invalid
ERROR/umeng: initCommon failed
```

**原因：** AppKey 未正确配置或填反。

**解决：**
1. 确认 Android AppKey 和 iOS AppKey 没有填反（它们在友盟后台是不同的）
2. 确认 `initCommon()` 的第一个参数是 Android AppKey，第二个是 iOS AppKey
3. 在友盟后台确认 AppKey 存在
4. 重新编译运行

---

### `Redeclaration: class UmengCommonSdkPlugin`（Android 编译错误）

**症状：**
```
e: Redeclaration: class UmengCommonSdkPlugin
```

**原因：** `umeng_common_sdk 1.3.1` 插件双实现冲突——Kotlin 桩文件与 Java 完整实现同时存在。

**解决：** 集成脚本已自动修复（plugin_fixer 删除 Kotlin 桩文件）。如手动处理，可删除 pub-cache 中的桩文件：
```bash
rm ~/.pub-cache/hosted/pub.dev/umeng_common_sdk-1.3.1/android/src/main/kotlin/com/umeng/umeng_common_sdk/UmengCommonSdkPlugin.kt
```

---

### `Duplicate interface definition for class 'UmengCommonSdkPlugin'`（iOS 编译错误）

**症状：**
```
Duplicate interface definition for class 'UmengCommonSdkPlugin'
```

**原因：** 同上，iOS 端 Swift 桩文件与 OC 完整实现冲突。

**解决：** 集成脚本已自动修复（plugin_fixer 删除 Swift 桩文件）。如手动处理，删除 iOS Swift 桩文件：
```bash
rm ~/.pub-cache/hosted/pub.dev/umeng_common_sdk-1.3.1/ios/Classes/UmengCommonSdkPlugin.swift
```

---

### `requires ... compile against version 34`（Android 编译错误）

**症状：**
```
requires libraries and applications that target at most API level 33
... requires ... compile against version 34
```

**原因：** `umeng_common_sdk` 插件的 `compileSdkVersion` 为 33，低于新版构建工具链要求。

**解决：** 集成脚本已自动修复（plugin_fixer 将其提升为 34）。手动处理可用 sed 替换：
```bash
sed -i '' 's/compileSdkVersion 33/compileSdkVersion 34/' \
  ~/.pub-cache/hosted/pub.dev/umeng_common_sdk-1.3.1/android/build.gradle
```

---

### 项目无法编译（集成前）

**症状：** Skill 在步骤 2 项目验证时失败

**解决：**
1. 执行 `flutter doctor` 检查环境
2. 修复所有编译错误
3. 确保 `flutter run` 能正常启动
4. 再运行 SDK 集成

**注意：** SDK 集成要求项目本身是可编译的。

## 注意事项

1. **隐私合规**：必须在用户同意隐私政策后才能调用 `initCommon()`
2. **不要重复引入原生 SDK**：Flutter SDK 内部已集成原生 Common SDK。如果原生工程中已有 `com.umeng.umsdk:common`（Android build.gradle）或 `pod 'UMCommon'`（iOS Podfile），必须删除
3. **iOS 必须执行 `pod install`**：`flutter pub get` 后必须 `(cd ios && pod install)`，否则原生依赖缺失
4. **事件属性限制**：仅支持 String、int、double、long，不支持 NULL、bool、Map、数组
5. **Release 构建必须配置混淆规则**：否则 SDK 类被混淆后无法正常工作
6. **SPM 支持现状**：友盟 Flutter SDK 当前不支持 Swift Package Manager（SPM）。Flutter 3.44+ 新建 iOS 工程默认启用 SPM 且无 Podfile，集成脚本的项目验证阶段会检测 pbxproj 中的 `FlutterGeneratedPluginSwiftPackage` 标记并**直接阻塞**，请按下方「SPM → CocoaPods 迁移」章节处理。请关注友盟插件官方 SPM 适配进展。

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

## 参考资源

### 官方文档
- **友盟统计 Flutter SDK集成文档**: https://developer.umeng.com/docs/119267/detail/174923
- **友盟开发者中心**: https://developer.umeng.com

### SDK资料
- **Flutter统计SDK集成指南**: `集成文档/Flutter/Flutter-统计SDK-集成指南.md`

### 相关Skills
- **Flutter APM集成**: `scripts/umeng-flutter-apm-integration/` (依赖统计SDK作为前置)
- **Android统计集成**: `scripts/umeng-analytics-integration/`
- **iOS统计集成**: `scripts/umeng-ios-analytics-integration/`

### 工具脚本

| 脚本 | 功能 |
|------|------|
| `scripts/umeng-flutter-analytics-integration/main.py` | 主工作流编排 |
| `scripts/umeng-flutter-analytics-integration/env_checker.py` | 环境检查 |
| `scripts/umeng-flutter-analytics-integration/project_validator.py` | 项目验证 |
| `scripts/umeng-flutter-analytics-integration/sdk_integrator.py` | 统计 SDK 集成 |
| `scripts/umeng-flutter-analytics-integration/plugin_fixer.py` | 插件兼容性自动修复（桩文件冲突 + compileSdkVersion） |
| `scripts/umeng-flutter-analytics-integration/sdk_verifier.py` | SDK 集成验证 |
| `scripts/umeng-flutter-analytics-integration/device_detector.py` | 设备检测 |
| `scripts/umeng-flutter-analytics-integration/rollback.py` | 回滚恢复 |

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/119267/detail/174923
- Flutter 接入常见问题: https://developer.umeng.com/docs/119267/detail/205266
- SDK 下载: https://developer.umeng.com/sdk
- 合规指南（Android）: https://developer.umeng.com/docs/119267/detail/194589
- 合规指南（iOS）: https://developer.umeng.com/docs/119267/detail/194590
