## 友盟iOS统计SDK集成Skill

## 功能说明

自动将友盟iOS统计SDK集成到现有iOS项目中,简化SDK集成流程。

### 核心功能

1. ✅ **环境检查** - 自动检测macOS、Xcode、CocoaPods等开发工具
2. ✅ **项目验证** - 验证目标iOS项目完整性并尝试编译
3. ✅ **参数交互** - 引导用户输入appkey和channel,支持占位符模式
4. ✅ **SDK集成** - 自动完成Podfile配置、pod install、代码注入
5. ✅ **编译验证** - 集成后编译验证(xcodebuild)
6. ✅ **依赖验证** - pod install后自动验证SDK依赖是否正确安装
7. ✅ **智能错误提示** - 编译失败时提供针对性的解决建议
8. ✅ **回滚机制** - 提供回滚脚本恢复修改

### 支持的项目类型

- ✅ Swift项目 (AppDelegate)
- ✅ Objective-C项目 (AppDelegate)
- ✅ SwiftUI项目 (@main App文件)

### 前置要求

### 必需工具
- ✅ macOS系统
- ✅ Xcode开发工具
- ✅ CocoaPods工具
- ✅ 可编译的iOS项目


## 使用方式

### 基本用法(交互式)

```bash
python scripts/umeng-ios-analytics-integration/main.py --project-path /path/to/ios/project
```

运行后会引导你输入:
- appkey: 友盟后台获取的应用标识
- channel: 应用分发渠道(如: App Store, appstore)

### 指定参数(非交互式)

```bash
python scripts/umeng-ios-analytics-integration/main.py \
  --project-path /path/to/ios/project \
  --app-key YOUR_APP_KEY \
  --channel YOUR_CHANNEL
```

### 指定Target

```bash
python scripts/umeng-ios-analytics-integration/main.py \
  --project-path /path/to/ios/project \
  --target MyApp
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--project-path` | ✅ | - | iOS项目路径(包含.xcodeproj的目录) |
| `--app-key` | ❌ | 占位符 | 友盟AppKey |
| `--channel` | ❌ | `App Store` | 渠道标识 |
| `--target` | ❌ | 第一个Target | Target名称 |

## 工作流程

```
步骤1: 🔍 环境检查 (macOS/Xcode/CocoaPods)
  ↓
步骤2: 📂 项目验证 (结构检查 + 可选编译)
  ↓
步骤3: ⌨️  参数配置 (appkey + channel + target)
  ↓
步骤4: 💾 备份项目 (zip压缩备份)
  ↓
步骤5: 📦 SDK集成 (Podfile修改 + pod install + 代码注入)
  ↓
步骤6: 🔨 编译验证 (xcodebuild，失败自动回滚)
  ↓
步骤7: ✅ SDK验证 (预留，当前版本仅提供手动验证指引)
```

## SDK集成内容

### 1. CocoaPods依赖配置

在Podfile的target中添加:
```ruby
target 'MyApp' do
  # 友盟统计SDK
  pod 'UMCommon'
  pod 'UMDevice'
end
```

**说明**：
- v1.0仅包含核心统计SDK，不包含UMCCommonLog
- 使用直接导入方式，不使用条件编译
- 如果找不到UMCommon框架，应排查pod install环节

### 2. SDK初始化代码

**Swift AppDelegate:**
```swift
import UMCommon

func application(_ application: UIApplication, 
                didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    
    UMConfigure.initWithAppkey("YOUR_APPKEY", channel: "App Store")
    
    return true
}
```

**Objective-C AppDelegate:**
```objc
#import <UMCommon/UMCommon.h>

- (BOOL)application:(UIApplication *)application 
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    
    [UMConfigure initWithAppkey:@"YOUR_APPKEY" channel:@"App Store"];
    
    return YES;
}
```

**SwiftUI App:**
```swift
import UMCommon

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, 
                    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
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

### Q3: 项目编译失败?

**A**: SDK集成前项目必须可编译。请:
1. 在Xcode中打开项目
2. 修复所有编译错误
3. 确保能成功编译
4. 再运行SDK集成

### Q4: 使用占位符集成后怎么办?

**A**: 集成时需要替换为真实值:
1. 在友盟后台创建应用获取appkey
2. 打开AppDelegate或App文件
3. 替换`YOUR_UMENG_APPKEY`为真实appkey
4. 重新编译运行

### Q5: 如何验证SDK集成成功?

**A**: 当前版本的完成标准是**编译成功**：
1. Skill自动执行编译验证（步骤6）
2. 编译成功即表示SDK集成完成
3. 项目能够正常编译和运行

**手动验证（可选）**：
如需验证SDK是否正确上报数据，可以：
1. 在Xcode中打开.xcworkspace项目
2. 选择模拟器或真机作为运行目标
3. 点击Run (⌘R) 编译并运行
4. 查看Xcode控制台日志

**成功关键词**：
```
网络请求成功(Response Applog) {"success": "ok"}
```

**失败关键词**：
```
appkey is null
CIE10001
UMCommonSDK init failed
```

### Q6: 集成失败如何回滚?

**A**: 使用回滚脚本:
```bash
python scripts/umeng-ios-analytics-integration/rollback.py --backup-file /path/to/backup.zip
```

### Q7: 支持多Target项目吗?

**A**: 支持,使用`--target`参数指定:
```bash
python scripts/umeng-ios-analytics-integration/main.py --project-path /path/to/project --target MyApp
```

### Q8: SwiftUI项目没有AppDelegate怎么办?

**A**: 工具会自动处理:
- 检测@main修饰的App文件
- 创建AppDelegate类
- 添加@UIApplicationDelegateAdaptor
- 注入初始化代码

### Q9: 编译时报"framework not found"错误?

**A**: 这通常是因为Pods依赖未正确安装：
1. **确认使用.xcworkspace打开项目**（不是.xcodeproj）
2. 检查Pods目录是否存在且包含UMCommon
3. 尝试Clean Build Folder (⇧⌘K)
4. 删除DerivedData后重新打开项目
5. 重新运行 `pod install`

### Q10: pod install失败或UMCommon未安装?

**A**: 可能原因和解决方法：
1. **Podfile配置有误** - 检查Podfile文件内容
2. **CocoaPods源无法访问** - 运行 `pod repo update` 更新源
3. **网络问题** - 删除Pods目录后重新运行 `pod install`
4. **需要镜像源** - 如果使用国内网络，考虑配置CocoaPods镜像

**注意**：Skill会在pod install后自动验证依赖是否正确安装，如果检测到问题会提前提示。

### Q11: 为什么集成前 AI Agent 会先执行 umeng-cli trace？

**A**: 这是 Skill 调用埋点上报，用于统计 Skill 实际使用情况：

- Skill 每次被加载：上报 `{"skill_name":"umeng-ios-analytics-integration"}`
- 拿到新 Appkey：补报 `{"skill_name":"umeng-ios-analytics-integration","appkey":"<appkey>"}`

仅上报「哪个 Skill 在哪个 App 上被用」，不涉及任何工程源码内容，可放心执行。

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/119267/detail/118588
- iOS开发文档: https://developer.apple.com/documentation/

## 故障排查 (Troubleshooting)

### 编译错误：framework 'UMCommon' not found

**症状**：
```
ld: framework 'UMCommon' not found
clang: error: linker command failed with exit code 1
```

**原因**：Xcode找不到UMCommon框架，通常是因为Pods未正确安装或使用了错误的项目文件。

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
   cd /path/to/your/project
   ls -la Pods/UMCommon
   # 应该能看到UMCommon目录及其内容
   ```

3. **Clean Build Folder**
   - 在Xcode中：Product → Clean Build Folder (⇧⌘K)
   - 或命令行：
     ```bash
     rm -rf ~/Library/Developer/Xcode/DerivedData/MyApp-*
     ```

4. **重新安装Pods**
   ```bash
   cd /path/to/your/project
   rm -rf Pods/ Podfile.lock
   pod install
   ```

5. **重新打开Xcode**
   - 完全退出Xcode
   - 重新打开.xcworkspace文件

---

### pod install失败

**症状1：找不到UMCommon**
```
[!] Unable to find a specification for `UMCommon`
```

**解决**：
```bash
## 更新CocoaPods源
pod repo update

## 重新安装
pod install
```

**症状2：网络超时**
```
[!] Error installing UMCommon
[!] /usr/bin/curl -f -L -o ...
```

**解决**：
```bash
## 方法1: 清理缓存后重试
rm -rf ~/Library/Caches/CocoaPods
pod install

## 方法2: 使用镜像源（国内网络）
## 在Podfile顶部添加：
source 'https://mirrors.tuna.tsinghua.edu.cn/git/CocoaPods/Specs.git'
source 'https://cdn.cocoapods.org/'
```

**症状3：权限错误**
```
[!] You need at least git version 1.8.5
```

**解决**：
```bash
## 更新git
brew install git
```

---

### 编译错误：User Script Sandboxing

**症状**：
```
error: Sandbox: rsync(... deny file-write-create
```

**原因**：Xcode 15+默认启用User Script Sandboxing，可能影响Pods脚本。

**解决**：
- Skill已自动关闭此设置
- 如果仍报错，手动检查：
  1. 打开Xcode项目
  2. 选择Target → Build Settings
  3. 搜索 "User Script Sandboxing"
  4. 设置为 `No`

---

### 编译错误：iOS版本不兼容

**症状**：
```
error: The iOS Simulator deployment target 'IPHONEOS_DEPLOYMENT_TARGET' 
is set to 11.0, but the range of supported deployment target versions is 
12.0 to 17.0.
```

**解决**：
- Skill已自动在Podfile的post_install中修复
- 如果仍报错，检查Podfile是否包含：
  ```ruby
  post_install do |installer|
    installer.pods_project.targets.each do |target|
      target.build_configurations.each do |config|
        if config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'].to_f < 14.0
          config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '14.0'
        end
      end
    end
  end
  ```

---

### SDK初始化失败

**症状**：运行应用后日志显示
```
appkey is null
UMCommonSDK init failed
```

**原因**：AppKey未正确配置。

**解决**：
1. 检查代码中的AppKey是否正确
   ```swift
   // 确认不是占位符
   UMConfigure.initWithAppkey("YOUR_UMENG_APPKEY", channel: "App Store")
   //                                  ↑ 应该替换为真实AppKey
   ```

2. 在友盟后台确认AppKey存在
   - 登录友盟后台
   - 进入应用管理
   - 复制正确的AppKey

3. 重新编译运行

---

### 项目无法编译（集成前）

**症状**：Skill在步骤2项目验证时失败

**解决**：
1. 在Xcode中打开项目
2. 修复所有编译错误
3. 确保项目能够成功编译
4. 再运行SDK集成

**注意**：SDK集成要求项目本身是可编译的。
