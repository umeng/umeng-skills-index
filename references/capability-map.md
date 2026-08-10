# 能力总览表

| 子能力名 | 类别 | 一句话描述 | 鉴权方式 | 接口数 | 子文档路径 |
|---------|------|-----------|---------|--------|-----------|
| U-App 核心指标 | CLI 查询 | 账户维度所有 App 合计、单日快照（DAU/新增/启动/总用户）、活跃/新增/启动趋势、使用时长 | `umeng-aksk` | 9 | [./skills/uapp-core-index.md](./skills/uapp-core-index.md) |
| U-App 留存 | CLI 查询 | 指定 App 在时间段内的 1/3/7/14/30 日留存率（支持新增/活跃用户维度） | `umeng-aksk` | 1 | [./skills/uapp-retention.md](./skills/uapp-retention.md) |
| U-App 渠道版本 | CLI 查询 | 各渠道或版本的活跃/新增/启动单日表现、趋势对比、Top N 排名 | `umeng-aksk` | 4 | [./skills/uapp-channel-version.md](./skills/uapp-channel-version.md) |
| U-App 自定义事件 | CLI 查询 | 事件列表/触发次数/独立用户/参数列表/参数值分布/参数值趋势/参数值时长 | `umeng-aksk` | 7 | [./skills/uapp-event.md](./skills/uapp-event.md) |
| U-App 事件管理 | CLI 管理 | App 端事件创建 + 小程序端批量创建 + 事件列表查询（跨 uapp/umini 命名空间） | `umeng-aksk` | 4（2写+2读） | [./skills/uapp-event-manage.md](./skills/uapp-event-manage.md) |
| 小程序渠道 | CLI 查询 | 获客来源概览/渠道效果/活动效果/场景概览/场景列表（仅小程序/H5/小游戏） | `umeng-aksk` | 5 | [./skills/uapp-mini-channel.md](./skills/uapp-mini-channel.md) |
| 小程序营销 | CLI 管理 | 为小程序创建推广链接 + 查询已有推广场景列表（仅小程序/H5/小游戏） | `umeng-aksk` | 2（1写+1读） | [./skills/uapp-campaign.md](./skills/uapp-campaign.md) |
| 应用资产 | CLI 查询 | App 总数/App 列表/小程序列表，跨 uapp/umini 两个命名空间 | `umeng-aksk` | 3 | [./skills/uapp-assets.md](./skills/uapp-assets.md) |
| 小程序统计 | CLI 查询 | 概况/累计用户/留存/受访页面/入口页面/分享概况/页面分享/分享用户/事件列表/事件统计/事件属性/属性值分布 | `umeng-aksk` | 12 | [./skills/uapp-umini.md](./skills/uapp-umini.md) |
| U-APM 性能监控 | CLI 查询 | 崩溃率/ANR/卡顿/启动耗时/网络性能/页面加载/分钟级实时监控 | `aliyun-aksk` | 8 | [./skills/uapm.md](./skills/uapm.md) |
| U-APM 崩溃诊断 | CLI 查询 | 崩溃/ANR/卡顿列表筛选、单条详情、堆栈符号化、诊断工作流 | `aliyun-aksk` | 5 | [./skills/uapm-crash-diagnosis.md](./skills/uapm-crash-diagnosis.md) |
| Android 统计集成 | SDK 集成 | 自动将友盟 Android 统计 SDK 集成到项目（环境检查→项目验证→集成→编译→logcat 验证） | 无需鉴权 | — | [./skills/android-analytics-integration.md](./skills/android-analytics-integration.md) |
| iOS 统计集成 | SDK 集成 | 自动将友盟 iOS 统计 SDK 集成到项目（环境检查→项目验证→集成→编译→Xcode 验证） | 无需鉴权 | — | [./skills/ios-analytics-integration.md](./skills/ios-analytics-integration.md) |
| 推送集成 | SDK 集成 | 自动将友盟推送 SDK 集成到 Android 项目（环境检查→项目验证→集成→编译→logcat 验证） | 无需鉴权 | — | [./skills/push-integration.md](./skills/push-integration.md) |
| Android APM 集成 | SDK 集成 | 自动将友盟 Android APM SDK 集成到项目（环境检查→项目验证→Gradle插件配置→集成→编译→logcat 验证） | 无需鉴权 | — | [./skills/android-apm-integration.md](./skills/android-apm-integration.md) |
| iOS APM 集成 | SDK 集成 | 自动将友盟 iOS APM SDK 增量集成到已集成统计SDK的iOS项目（环境检查→前置验证→集成→编译→Xcode 验证） | 无需鉴权 | — | [./skills/ios-apm-integration.md](./skills/ios-apm-integration.md) |
| U-Web 统计集成 | SDK 集成 | 自动指导集成友盟 U-Web 统计 SDK 到 HTML/前端项目（代码片段生成→部署顺序校验→浏览器验证） | 无需鉴权 | — | [./skills/uweb-analytics-integration.md](./skills/uweb-analytics-integration.md) |
| Flutter 统计集成 | SDK 集成 | 自动将友盟统计 Flutter SDK 集成到项目（Android + iOS 双端：pubspec.yaml→Android 原生配置→Dart 初始化→编译→验证） | 无需鉴权 | — | [./skills/flutter-analytics-integration.md](./skills/flutter-analytics-integration.md) |
| Flutter APM 集成 | SDK 集成 | 自动将友盟 APM Flutter SDK 增量集成到已集成统计SDK的Flutter项目（Binding替换→NavigatorObserver→可选Native配置→编译→验证） | 无需鉴权 | — | [./skills/flutter-apm-integration.md](./skills/flutter-apm-integration.md) |
