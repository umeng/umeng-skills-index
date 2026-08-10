# 场景消歧义路由表

当用户问题可能匹配多个子能力时，按下表判断应进入的子能力。

| 典型用户问题 | 应进入的子能力 | 不要走的子能力 | 判断依据 |
|-------------|--------------|--------------|---------|
| "昨天 DAU 多少？" / "过去 7 天新增趋势" | uapp-core-index | uapp-umini | 问的是 App 级指标，非小程序 |
| "小程序昨天活跃多少？" / "小程序累计用户" | uapp-umini | uapp-core-index | 明确说"小程序"且问基础指标 |
| "次日留存率" / "7 日留存" | uapp-retention | uapp-umini | 问 App 留存（小程序留存走 uapp-umini） |
| "小程序新用户 7 日留存" | uapp-umini | uapp-retention | 明确说"小程序留存" |
| "事件 X 过去 7 天触发了多少次？" | uapp-event | uapp-event-manage | 查统计数据（只读），非管理 |
| "帮我创建一个事件 login_click" | uapp-event-manage | uapp-event | 写入操作（事件创建） |
| "应用宝渠道过去 7 天表现" | uapp-channel-version | uapp-mini-channel | App 渠道（非小程序推广渠道） |
| "小程序各推广渠道昨天带来多少用户？" | uapp-mini-channel | uapp-channel-version | 小程序推广渠道效果分析 |
| "帮小程序创建一条推广链接" | uapp-campaign | uapp-mini-channel | 写入操作（创建推广链接） |
| "推广链接 A 昨天带来多少新用户？" | uapp-mini-channel | uapp-campaign | 查推广效果统计（只读） |
| "崩溃率趋势" / "启动耗时分布" | uapm | uapm-crash-diagnosis | 聚合指标查询 |
| "最近崩溃列表" / "这条崩溃的堆栈是什么？" | uapm-crash-diagnosis | uapm | 单条崩溃详情/诊断 |
| "我有多少个 App？" / "列出所有应用" | uapp-assets | uapp-core-index | 查应用列表/资产（非指标） |
| "集成友盟统计 SDK 到我的 Android 项目" | android-analytics-integration | — | 明确说"集成 SDK" |
| "集成统计 SDK" / "集成友盟统计到我的项目" | android-analytics-integration | — | 明确说"集成统计SDK"但未说明平台时默认Android；若用户说明iOS则走ios-analytics-integration；若用户说明Flutter则走flutter-analytics-integration |
| "集成友盟推送到我的 App" | push-integration | — | 明确说"推送集成" |
| "集成APM到我的App" / "接入性能监控SDK" | android-apm-integration | uapm | 明确说"集成APM SDK"但未说明平台时优先追问平台，仅上下文无法推断时才默认Android；若用户说明iOS则走ios-apm-integration；若用户说明Flutter则走flutter-apm-integration |
| "集成APM到我的Android项目" / "接入Android性能监控SDK" | android-apm-integration | uapm | 明确说"集成APM SDK"到Android项目 |
| "集成APM到我的iOS项目" / "接入iOS性能监控SDK" | ios-apm-integration | uapm | 明确说"集成APM SDK"到iOS项目 |
| "集成U-Web到我的网站" / "网站添加友盟统计" / "集成网站统计SDK" | uweb-analytics-integration | — | 明确说"集成"+"Web/网站/HTML"则走uweb-analytics-integration |
| "集成CNZZ" / "添加CNZZ代码" | uweb-analytics-integration | — | CNZZ 与 U-Web 为同一产品线，Web统计需求走此能力 |
| "性能监控" / "我要做性能监控"（无"集成/接入/SDK"动词） | uapm | android-apm-integration | 仅含"性能监控"而无"集成/接入"动词时视为查询性能指标走uapm；含"集成/接入"动词时走SDK集成 |
| "集成友盟统计到 Flutter 项目" / "Flutter 集成统计 SDK" | flutter-analytics-integration | android-analytics-integration | 明确说"Flutter"且"统计SDK" |
| "集成 APM 到 Flutter 项目" / "Flutter 接入性能监控" | flutter-apm-integration | android-apm-integration | 明确说"Flutter"且"APM/性能监控" |
| "Flutter 集成友盟 SDK" | — | — | 过于泛化，需追问SDK类型(统计/APM) |
| "集成友盟SDK" / "帮我接入友盟" | — | 所有集成类 | 过于泛化，需触发澄清对话：询问(1)目标平台(Android/iOS/Flutter/Web)、(2)SDK类型(统计/推送/APM) |
