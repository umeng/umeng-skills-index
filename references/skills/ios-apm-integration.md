## 友盟iOS APM性能监控SDK集成Skill

## 功能说明

自动将友盟iOS APM性能监控SDK增量集成到已集成UMCommon的iOS项目中,简化APM SDK集成流程。

### 核心功能

1. ✅ **前置条件检查** - 验证项目是否已通过ios-analytics-integration集成UMCommon
2. ✅ **CocoaPods配置** - 自动在Podfile中添加UMAPM依赖并执行pod install
3. ✅ **增量代码注入** - 在UMConfigure.initWithAppkey()之前注入APM配置代码
4. ✅ **编译验证** - 集成后编译验证(xcodebuild)
5. ✅ **回滚机制** - 提供zip备份恢复修改
6. ✅ **性能开关配置** - 支持自定义启用/禁用8项监控能力

### 支持的项目类型

- ✅ Swift项目 (AppDelegate)
- ✅ Objective-C项目 (AppDelegate)
- ✅ SwiftUI项目 (@main App文件)

### 前置要求

### 必需条件
- ✅ macOS系统
- ✅ Xcode开发工具
- ✅ CocoaPods工具
- ✅ **已通过 ios-analytics-integration Skill 集成了UMCommon**
- ✅ 可编译的iOS项目

### 可选工具
- ⚠️ 真机或模拟器 (仅验证APM日志时需要)


## 使用方式

### 基本用法(交互式)

```bash
python scripts/umeng-ios-apm-integration/main.py --project-path /path/to/ios/project
```

运行后会引导你输入:
- appkey: 友盟后台获取的应用标识（如已集成统计SDK则自动复用）
- channel: 应用分发渠道(如: App Store)

### 指定参数(非交互式)

```bash
python scripts/umeng-ios-apm-integration/main.py \
  --project-path /path/to/ios/project \
  --app-key YOUR_APP_KEY \
  --channel YOUR_CHANNEL
```

### 指定Target

```bash
python scripts/umeng-ios-apm-integration/main.py \
  --project-path /path/to/ios/project \
  --target MyApp
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--project-path` | ✅ | - | iOS项目路径(包含.xcodeproj的目录) |
| `--app-key` | ❌ | 自动复用 | 友盟AppKey(从已有UMConfigure.initWithAppkey中解析) |
| `--channel` | ❌ | `App Store` | 渠道标识 |
| `--target` | ❌ | 第一个Target | Target名称 |

## 工作流程

```
步骤1: 🔍 环境检查 (macOS/Xcode/CocoaPods)
  ↓
步骤2: 📂 项目验证 (结构检查 + .xcodeproj存在)
  ↓
步骤3: 📋 前置条件检查 (验证UMCommon已集成, UMConfigure.initWithAppkey存在)
  ↓
步骤4: ⌨️  参数配置 (appkey + channel + target, 自动复用已有配置)
  ↓
步骤5: 💾 备份项目 (zip压缩备份)
  ↓
步骤6: 📦 SDK增量集成 (Podfile修改 + pod install + APM代码注入)
  ↓
步骤7: ✅ 集成确认 (展示变更摘要供用户确认)
  ↓
步骤8: 🔨 编译验证 (xcodebuild, 失败自动回滚)
  ↓
步骤9: 📋 集成报告 (输出集成摘要、修改文件清单、备份路径、验证指引)
```

**关键检查点：**
- ✅ **步骤3完成后** - 确认UMCommon已正确集成
- ✅ **步骤5完成后** - 确认备份成功创建，可随时回滚
- ✅ **步骤7（确认点）** - 展示修改清单，用户确认后继续编译
- ✅ **步骤8失败时** - 提供回滚选项，不强制继续
- ✅ **步骤9完成后** - 运行 App，在 Xcode Console 中观察日志，出现 `[Reporter] SDK init success` 和 `UMAPM_NetworkEnable` 即表示 APM SDK 初始化成功

## SDK集成内容

### 1. CocoaPods依赖配置

在Podfile的target中添加:
```ruby
target 'MyApp' do
  # 友盟基础SDK (已存在)
  pod 'UMCommon'
  pod 'UMDevice'
  # 友盟APM性能监控SDK (新增)
  pod 'UMAPM'
end
```

**幂等检查**：
- 如果Podfile中已包含 `pod 'UMAPM'`，则跳过添加
- pod install后自动验证UMAPM框架是否正确安装：
  ```bash
  ls Pods/UMAPM
  # 应该能看到UMAPM目录及其内容
  ```

### 2. APM初始化代码

**⚠️ 关键要求：APM配置必须在 `UMConfigure.initWithAppkey()` 之前调用**

**Swift AppDelegate:**
```swift
import UMCommon
import UMAPM

func application(_ application: UIApplication,
                didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {

    // APM性能监控配置（必须在UMConfigure.initWithAppkey之前调用）
    let config = UMAPMConfig.default()
    config.crashAndBlockMonitorEnable = true
    config.launchMonitorEnable = true
    config.memMonitorEnable = true
    config.oomMonitorEnable = true
    config.networkEnable = true
    config.javaScriptBridgeEnable = true
    config.pageMonitorEnable = true
    config.logCollectEnable = true
    UMCrashConfigure.setAPMConfig(config)

    UMConfigure.initWithAppkey("YOUR_APPKEY", channel: "App Store")
    return true
}
```

**Objective-C AppDelegate:**
```objc
#import <UMCommon/UMCommon.h>
#import <UMAPM/UMAPMConfig.h>
#import <UMAPM/UMCrashConfigure.h>

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {

    // APM性能监控配置（必须在UMConfigure.initWithAppkey之前调用）
    UMAPMConfig* config = [UMAPMConfig defaultConfig];
    config.crashAndBlockMonitorEnable = YES;
    config.launchMonitorEnable = YES;
    config.memMonitorEnable = YES;
    config.oomMonitorEnable = YES;
    config.networkEnable = YES;
    config.javaScriptBridgeEnable = YES;
    config.pageMonitorEnable = YES;
    config.logCollectEnable = YES;
    [UMCrashConfigure setAPMConfig:config];

    [UMConfigure initWithAppkey:@"YOUR_APPKEY" channel:@"App Store"];
    return YES;
}
```

**SwiftUI App:**
```swift
import UMCommon
import UMAPM

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        // APM性能监控配置（必须在UMConfigure.initWithAppkey之前调用）
        let config = UMAPMConfig.default()
        config.crashAndBlockMonitorEnable = true
        config.launchMonitorEnable = true
        config.memMonitorEnable = true
        config.oomMonitorEnable = true
        config.networkEnable = true
        config.javaScriptBridgeEnable = true
        config.pageMonitorEnable = true
        config.logCollectEnable = true
        UMCrashConfigure.setAPMConfig(config)

        UMConfigure.initWithAppkey("YOUR_APPKEY", channel: "App Store")
        return true
    }
}

@main
struct MyApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    // ...
}
```

**代码注入逻辑说明：**
1. 查找 AppDelegate/App 文件中已存在的 `UMConfigure.initWithAppkey` 调用
2. 在其**之前**插入 APM 配置代码块
3. 同步添加 `import UMAPM`（Swift）或 `#import <UMAPM/UMAPMConfig.h>` + `#import <UMAPM/UMCrashConfigure.h>`（ObjC）
4. 幂等检查：若已存在 `UMAPMConfig` 或 `UMCrashConfigure.setAPMConfig` 则跳过注入

### 3. 配置开关说明

| 属性名 | 功能说明 | 默认值 |
|--------|----------|--------|
| `crashAndBlockMonitorEnable` | 崩溃与卡顿监控 | YES/true |
| `launchMonitorEnable` | 启动耗时监控 | YES/true |
| `memMonitorEnable` | 内存监控 | YES/true |
| `oomMonitorEnable` | OOM监控 | YES/true |
| `networkEnable` | 网络性能监控 | YES/true |
| `javaScriptBridgeEnable` | JS Bridge监控 | YES/true |
| `pageMonitorEnable` | 页面加载监控 | YES/true |
| `logCollectEnable` | 日志采集 | YES/true |

**重要说明：**
- ⚠️ 所有开关默认为开启状态，不调用配置代码也是全部开启
- ⚠️ 如需自定义监控能力，可将对应开关设为 `NO`/`false`
- ⚠️ iOS最低版本要求同UMCommon（通常为iOS 12.0+）

### 4. SDK运行验证

集成完成并编译通过后，运行 App 在 Xcode Console 中观察日志输出，出现以下关键词即表示 APM SDK 初始化成功：

**多层验证体系：**
- **基本验证**：`[Reporter] SDK init success`（确认 SDK 初始化成功）
- **APM 模块验证**：`UMAPM_NetworkEnable` 或 `UMAPM_MemEnable`（确认 APM 模块已激活）
- **可选参考**：`可接入免费的网络分析能力`（部分场景可能出现）

> ⚠️ **运行时验证前关键检查**：
>
> 1. 打开 AppDelegate 文件，检查 `UMConfigure.initWithAppkey` 中的 appkey 值
> 2. 若当前值为占位符（如 `YOUR_APPKEY`），必须先替换为友盟后台的真实 appkey
> 3. 替换后重新编译运行，再进行日志验证
>
> 占位符 appkey 下初始化日志虽可输出，但无法验证数据上报完整性。

> **提示**：如果未看到上述日志，请检查 APM 配置代码是否在 `UMConfigure.initWithAppkey()` 之前正确调用（参见上方「APM初始化代码」章节）。

## 常见问题

### Q1: 提示缺少Xcode?

**A**: 安装Xcode:
```bash
## 方法1: App Store搜索"Xcode"安装(推荐)

## 方法2: 仅安装命令行工具
xcode-select --install
```

### Q2: 提示缺少CocoaPods?

**A**: 安装CocoaPods:
```bash
## 方法1: 使用gem
sudo gem install cocoapods

## 方法2: 使用Homebrew
brew install cocoapods

## 安装后执行
pod setup
```

### Q3: UMCommon未集成（前置检查失败）?

**A**: APM SDK强依赖UMCommon基础组件,请先运行统计SDK集成:
```bash
python scripts/umeng-ios-analytics-integration/main.py --project-path /path/to/ios/project
```

集成完成后再重新运行APM集成。

### Q4: pod install失败?

**A**: 可能原因和解决方法：
1. **CocoaPods源无法访问** - 运行 `pod repo update` 更新源
2. **找不到UMAPM** - 确认Podfile中 `pod 'UMAPM'` 拼写正确（注意大小写）
3. **网络问题** - 删除Pods目录后重新运行 `pod install`
4. **需要镜像源** - 国内网络在Podfile顶部添加 `source 'https://cdn.cocoapods.org/'`

### Q5: 编译时报"framework not found"错误?

**A**: 通常是Pods依赖未正确安装：
1. 确认使用.xcworkspace打开项目（不是.xcodeproj）
2. 检查Pods目录是否存在且包含UMAPM
3. Clean Build Folder (⇧⌘K) 后重新编译
4. 重新运行 `pod install`

### Q6: User Script Sandboxing错误?

**A**: Xcode 15+默认启用User Script Sandboxing。Skill已自动关闭此设置。如果仍报错，手动在Target → Build Settings中搜索 "User Script Sandboxing" 并设为 `No`。

### Q7: iOS版本不兼容?

**A**: Skill已自动在Podfile的post_install中将低于14.0的deployment target统一修复为14.0。如果仍报错，检查Podfile是否包含对应的post_install块。

### Q8: SwiftUI项目没有AppDelegate怎么办?

**A**: Skill会自动处理：检测@main修饰的App文件，创建AppDelegate类（如未存在），添加@UIApplicationDelegateAdaptor，注入APM配置和初始化代码。

### Q9: 集成失败如何回滚? 多SDK共存如何处理?

**A**: 使用回滚脚本（使用zip备份）:
```bash
python scripts/umeng-ios-apm-integration/rollback.py \
  --project-path /path/to/ios/project \
  --backup-file /path/to/backup.zip
```

**⚠️ 多SDK共存回滚风险警告：**
- 当前采用全工程 zip 备份策略，备份时间点为 APM 集成前
- 如果项目已先集成了统计SDK，再集成APM，回滚操作会将整个工程恢复到 APM 集成前的状态，**统计SDK在APM集成之后的修改也会被覆盖**
- **建议**：多SDK共存场景下，优先使用 `git commit` 管理每次集成的变更，利用 git 的精细化回退能力实现多层次回滚，而非依赖脚本的 zip 备份

### Q10: 为什么集成前 AI Agent 会先执行 umeng-cli trace？

**A**: 这是 Skill 调用埋点上报，用于统计 Skill 实际使用情况：

- Skill 每次被加载：上报 `{"skill_name":"ios-apm-integration"}`
- 拿到 Appkey（从已集成的统计 SDK 复用）：补报 `{"skill_name":"ios-apm-integration","appkey":"<appkey>"}`

仅上报「哪个 Skill 在哪个 App 上被用」，不涉及任何工程源码内容，可放心执行。

## 参考资源

### 官方文档
- **友盟APM性能监控接入指南(iOS)**: https://developer.umeng.com/docs/193624/detail/194590
- **友盟开发者中心**: https://developer.umeng.com
- **iOS开发文档**: https://developer.apple.com/documentation/

### SDK资料
- **iOS统计SDK接入说明**: `SDK集成资料/ios/iOS统计SDK接入说明.md`

### 相关Skills
- **iOS统计SDK集成**: `scripts/umeng-ios-analytics-integration/` (APM SDK前置依赖)
- **Android APM集成**: `scripts/umeng-apm-integration/`

### 工具脚本

| 脚本 | 功能 |
|------|------|
| `scripts/umeng-ios-apm-integration/main.py` | 主工作流编排 |
| `scripts/umeng-ios-apm-integration/sdk_integrator.py` | APM SDK增量集成 |
| `scripts/umeng-ios-apm-integration/env_checker.py` | 环境检查 |
| `scripts/umeng-ios-apm-integration/project_validator.py` | 项目验证 |
| `scripts/umeng-ios-apm-integration/device_detector.py` | 真机/模拟器检测 |
| `scripts/umeng-ios-apm-integration/rollback.py` | 回滚恢复 |

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/193624/detail/194590
- iOS开发文档: https://developer.apple.com/documentation/

## 故障排查 (Troubleshooting)

### 编译错误：framework 'UMAPM' not found

**症状**：
```
ld: framework 'UMAPM' not found
clang: error: linker command failed with exit code 1
```

**原因**：Xcode找不到UMAPM框架，通常是因为Pods未正确安装或使用了错误的项目文件。

**解决步骤**：

1. **确认使用.xcworkspace打开项目**
   ```bash
   # ❌ 错误：使用.xcodeproj
   open MyApp.xcodeproj

   # ✅ 正确：使用.xcworkspace
   open MyApp.xcworkspace
   ```

2. **检查Pods目录**
   ```bash
   ls -la Pods/UMAPM
   ```

3. **Clean Build Folder** (⇧⌘K)，或命令行：
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/MyApp-*
   ```

4. **重新安装Pods**
   ```bash
   rm -rf Pods/ Podfile.lock
   pod install
   ```

---

### APM初始化顺序错误

**症状**：运行应用后Xcode Console无APM相关日志输出。

**原因**：`UMCrashConfigure.setAPMConfig()` 未在 `UMConfigure.initWithAppkey()` 之前调用。

**解决**：打开AppDelegate文件，确认APM配置代码位于 `UMConfigure.initWithAppkey()` 之前，如果顺序颠倒则调换后重新编译。

---

### pod install后UMAPM未安装

**症状**：
```
[!] Unable to find a specification for `UMAPM`
```

**解决**：
```bash
## 更新CocoaPods源
pod repo update

## 清理缓存后重试
rm -rf ~/Library/Caches/CocoaPods
pod install
```

如果仍无法找到，确认Podfile中拼写正确：`pod 'UMAPM'`（注意全大写）。

---

### import错误：No such module 'UMAPM'

**症状**：
```
No such module 'UMAPM'
```

**原因**：Swift项目中Pods模块未被正确识别。

**解决步骤**：
1. 确认使用.xcworkspace而非.xcodeproj
2. Clean Build Folder (⇧⌘K)
3. 删除DerivedData：`rm -rf ~/Library/Developer/Xcode/DerivedData/MyApp-*`
4. 重新打开.xcworkspace
5. 如仍报错，重新执行 `pod install`
