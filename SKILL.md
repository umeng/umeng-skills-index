---
name: umeng-skills-index
version: 1.2.0
description: 友盟全能力技能套件，聚合 19 个子能力：11 个基于 umeng-cli 的数据查询（U-App 核心指标/留存/渠道版本/事件/事件管理/小程序渠道/营销/资产/Umini、U-APM 性能监控/崩溃诊断）和 8 个 SDK 自动集成（Android 统计/iOS 统计/推送/Android APM/iOS APM/U-Web 统计/Flutter 统计/Flutter APM）。当用户需要查询友盟统计数据（DAU/留存/崩溃率/事件/渠道/营销/启动耗时）、进行性能监控诊断、或自动集成友盟 SDK 到 Android/iOS/Flutter 项目时使用。
metadata:
  requires:
    bins: ["umeng-cli"]
  install: "npm install -g @umengfe/umeng-cli"
  homepage: "https://github.com/umeng/umeng-cli"
---

# 友盟全能力技能套件

> `umeng-cli` 是友盟提供的命令行程序，所有数据查询操作通过执行 `umeng-cli call` 命令完成。

本技能聚合友盟生态 **19 个子能力**，覆盖两大类：

- **数据查询**（11 个）：基于 `umeng-cli call` 调用友盟 OpenAPI，涵盖 U-App 核心指标、留存、渠道版本、自定义事件、事件管理、小程序渠道、营销活动、应用资产、小程序统计、U-APM 性能监控、崩溃诊断
- **SDK 自动集成**（8 个）：自动将友盟 SDK 集成到 Android/iOS/Web/Flutter 项目，含环境检查、编译验证、logcat/Xcode/浏览器验证

## 前置条件：安装 umeng-cli

> **执行任何命令（含下文埋点）之前，请务必先完成本节的安装与版本校验。**

本技能的所有命令均依赖 `umeng-cli` 命令行工具，且要求最低版本 **0.2.13**（自该版本起 `umeng-cli trace` 内置 3 秒超时保护，避免埋点阻塞主流程）。

### 安装

```bash
npm install -g @umengfe/umeng-cli
```

> 当前仅支持 npm 全局安装一种方式。

### 版本校验与自动升级（一键脚本）

```bash
REQUIRED="0.2.13"
CURRENT=$(umeng-cli --version 2>/dev/null | awk '{print $NF}')
if [ -z "$CURRENT" ] || [ "$(printf '%s\n' "$REQUIRED" "$CURRENT" | sort -V | head -1)" != "$REQUIRED" ]; then
  echo "⏫ umeng-cli 当前版本 [${CURRENT:-未安装}] 低于最低要求 ${REQUIRED}，正在自动升级..."
  npm install -g @umengfe/umeng-cli@latest
  echo "✅ 升级完成，新版本：$(umeng-cli --version)"
fi
```

> AI Agent 进入本技能后请**先执行**该脚本；通过后再继续埋点与业务调用。
> 更多说明请参考 [umeng-cli 项目主页](https://github.com/umeng/umeng-cli)

> **埋点上报**（请在已完成上述前置条件后执行）：
> ```bash
> umeng-cli trace '{"skill_name":"umeng-skills-index"}' >/dev/null 2>&1 || true
> ```
>
> **Appkey 维度打点：** 当本轮任务中出现 Appkey 的输入操作时，在拿到该 Appkey 之后、发起首个业务 API 调用之前，再追加执行一次带 appkey 的打点：
> ```bash
> umeng-cli trace '{"skill_name":"umeng-skills-index", "appkey":"<输入的Appkey>"}' >/dev/null 2>&1 || true
> ```
> 同一 Appkey 在同一会话中只打一次；若用户切换到新的 Appkey，需对新的 Appkey 再打一次。
>
> **子Skill 调用打点：** 当 AI Agent 根据用户需求确认进入某个子Skill 时（即准备调用该子Skill 的业务 API），在首个业务 API 调用之前执行：
> ```bash
> umeng-cli trace '{"skill_name":"<子Skill标识>"}' >/dev/null 2>&1 || true
> ```
> - `<子Skill标识>` = 子文档文件名（无 `.md` 扩展名），如 `uapp-core-index`、`uapm-crash-diagnosis`、`android-analytics-integration`
> - 同一会话中同一子Skill **只打一次**；后续对该子Skill 的重复调用不再打点
> - 若已获得 Appkey，可合并为一条：`umeng-cli trace '{"skill_name":"<子Skill标识>", "appkey":"<Appkey>"}' >/dev/null 2>&1 || true`
> - 若获得 Appkey 时已执行过不含 appkey 的子Skill 打点，**无需补打**（appkey 维度由上方的全局 Appkey 打点覆盖）
>
> **⚠️ 防阻塞执行规范：**
> - **禁止用 `&&` 串行多条 trace 命令**：第 1 条卡住会阻塞整条命令链
> - 一次任务只对**当前正在使用的 Appkey** 打一次；切换到新 Appkey 时再独立发一条
> - trace 失败不可阻塞业务流程（`umeng-cli` ≥ 0.2.13 已内置 3s 超时保护）

## 能力概览

| # | 子能力 | 类别 | 一句话描述 | 前置依赖 | 子文档 |
|---|--------|------|-----------|----------|--------|
| 1 | U-App 核心指标 | 查询 | DAU/新增/启动/总用户/使用时长，9 个只读接口 | — | [uapp-core-index](references/skills/uapp-core-index.md) |
| 2 | U-App 留存 | 查询 | 1/3/7/14/30 日留存率，1 个只读接口 | — | [uapp-retention](references/skills/uapp-retention.md) |
| 3 | U-App 渠道版本 | 查询 | 渠道/版本维度的活跃/新增/启动趋势与排名 | — | [uapp-channel-version](references/skills/uapp-channel-version.md) |
| 4 | U-App 自定义事件 | 查询 | 事件列表/次数/独立用户/参数分布，7 个只读接口 | — | [uapp-event](references/skills/uapp-event.md) |
| 5 | U-App 事件管理 | 管理 | 事件创建/批量创建/列表，4 个接口（2 写+2 读） | — | [uapp-event-manage](references/skills/uapp-event-manage.md) |
| 6 | 小程序渠道 | 查询 | 获客来源/渠道/活动/场景效果分析，5 个只读接口 | — | [uapp-mini-channel](references/skills/uapp-mini-channel.md) |
| 7 | 小程序营销 | 管理 | 推广链接创建与查询，2 个接口（1 写+1 读） | — | [uapp-campaign](references/skills/uapp-campaign.md) |
| 8 | 应用资产 | 查询 | App 总数/列表/小程序列表，3 个只读接口 | — | [uapp-assets](references/skills/uapp-assets.md) |
| 9 | 小程序统计 | 查询 | 概况/留存/页面/分享/事件，12 个只读接口 | — | [uapp-umini](references/skills/uapp-umini.md) |
| 10 | U-APM 性能监控 | 查询 | 崩溃率/启动耗时/网络性能/页面加载，8 个只读接口 | — | [uapm](references/skills/uapm.md) |
| 11 | U-APM 崩溃诊断 | 查询 | 崩溃列表/详情/堆栈/符号化，诊断工作流 | — | [uapm-crash-diagnosis](references/skills/uapm-crash-diagnosis.md) |
| 12 | Android 统计集成 | 集成 | 自动集成友盟 Android 统计 SDK 到项目 | — | [android-analytics-integration](references/skills/android-analytics-integration.md) |
| 13 | iOS 统计集成 | 集成 | 自动集成友盟 iOS 统计 SDK 到项目 | — | [ios-analytics-integration](references/skills/ios-analytics-integration.md) |
| 14 | 推送集成 | 集成 | 自动集成友盟推送 SDK 到 Android 项目 | #12 Android 统计集成 | [push-integration](references/skills/push-integration.md) |
| 15 | Android APM 集成 | 集成 | 自动集成友盟 Android APM SDK 到项目 | #12 Android 统计集成 | [android-apm-integration](references/skills/android-apm-integration.md) |
| 16 | iOS APM 集成 | 集成 | 自动集成友盟 iOS APM SDK 到项目 | #13 iOS 统计集成 | [ios-apm-integration](references/skills/ios-apm-integration.md) |
| 17 | U-Web 统计集成 | 集成 | 自动指导集成友盟 U-Web 统计 SDK 到 HTML/前端项目（代码部署→事件埋点→浏览器验证） | — | [uweb-analytics-integration](references/skills/uweb-analytics-integration.md) |
| 18 | Flutter 统计集成 | 集成 | 自动集成友盟统计 Flutter SDK 到项目（Android + iOS 双端） | — | [flutter-analytics-integration](references/skills/flutter-analytics-integration.md) |
| 19 | Flutter APM 集成 | 集成 | 自动集成友盟 APM Flutter SDK 到项目（Android + iOS 双端） | #18 Flutter 统计集成 | [flutter-apm-integration](references/skills/flutter-apm-integration.md) |

### 平台 / 产品消歧约定

> 本技能聚合多平台（Android / iOS）、多产品（统计 / 推送 / APM）能力。路由时遵循：
>
> 1. **平台默认**：用户未指明平台时，统计SDK默认Android，APM优先追问平台（不得已时默认Android），推送仅支持Android
> 2. **产品消歧**：含"集成/接入/SDK"动词时走SDK集成子能力；仅提"性能监控"而无集成动词时走uapm数据查询
> 3. **泛关键词**：路由表使用"Android 统计 SDK"而非"Android SDK"，以避免跨产品误匹配
> 4. **极泛化请求**：用户说"集成友盟SDK"而不指明类型/平台时，应触发澄清对话而非猜测路由
> 5. **Flutter 平台**：用户明确提到"Flutter"时，统计集成走 flutter-analytics-integration，APM 集成走 flutter-apm-integration；仅说"集成统计SDK"而未提 Flutter 时仍默认 Android
>
> 详见 [`references/scenario-routes.md`](references/scenario-routes.md) 和 [`references/trigger-keywords.md`](references/trigger-keywords.md)。

## 如何使用本技能

1. **想看完整能力清单** → 读 [`references/capability-map.md`](references/capability-map.md)
2. **想根据问题定位子能力** → 读 [`references/scenario-routes.md`](references/scenario-routes.md)
3. **想按关键词速查** → 读 [`references/trigger-keywords.md`](references/trigger-keywords.md)
4. **需要某个子能力的完整 API/工作流** → 读对应 `references/skills/*.md` 子文档

## 通用约定

### 鉴权方式

| 子能力 | 鉴权类型 | 说明 |
|--------|---------|------|
| #1–#9（U-App 系列） | `umeng-aksk` | 友盟 AK/SK，通过 `umeng-cli login` 自动管理 |
| #10–#11（U-APM 系列） | `aliyun-aksk` | 阿里云 AK/SK，通过 `umeng-cli login --provider aliyun` 管理 |
| #12–#19（SDK 集成） | 无需鉴权 | 仅操作本地项目文件 |

> **注意：** SDK 集成类子能力（#12-#19）核心功能无需鉴权，但 Skill 使用统计（trace 埋点）依赖 `umeng-cli login` 凭证。建议首次使用前执行一次 `umeng-cli login` 以确保使用数据完整；未登录不影响集成功能正常执行。

### 日期格式

- 所有日期参数使用 `YYYY-MM-DD` 格式（如 `2025-06-10`）
- `startDate` / `endDate` 跨度最大 90 天（友盟 OpenAPI 限制）
- "昨日"需由客户端计算：`date -v-1d +%Y-%m-%d`（macOS）或 `date -d yesterday +%Y-%m-%d`（Linux）

### 中文参数编码

- 当参数值含中文（如渠道名"应用宝"、事件显示名）时，JSON 内直接使用 UTF-8 中文即可
- `umeng-cli call` 内部会自动处理编码，**无需手动 URL encode**

### Appkey 获取

若用户未提供 appkey，可通过 [应用资产](references/skills/uapp-assets.md) 子能力的 `umeng.uapp.getAppList` 接口查询账户下所有 App 列表获取。
