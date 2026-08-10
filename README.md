# Umeng+ Skills Index

友盟+ AI Agent 全能力技能套件，聚合数据查询、性能诊断与 SDK 自动集成能力。

当前版本：`1.2.0`

## 能力范围

- 11 个数据查询与诊断能力：U-App 核心指标、留存、渠道版本、自定义事件、事件管理、小程序渠道、营销活动、应用资产、小程序统计、U-APM 性能监控与崩溃诊断。
- 8 个 SDK 集成能力：Android/iOS/Flutter 统计、Android/iOS/Flutter APM、Android 推送与 U-Web 网站统计。
- 通过场景路由和关键词表，帮助 AI Agent 自动选择正确的子能力。

完整清单请查看 [能力地图](references/capability-map.md)，AI Agent 的主入口是 [SKILL.md](SKILL.md)。

## 前置条件

- Node.js 与 npm
- Python 3（仅 SDK 自动集成脚本需要）
- `umeng-cli >= 0.2.13`

安装命令：

```bash
npm install -g @umengfe/umeng-cli
umeng-cli --version
```

需要查询账号数据时，请按对应能力的说明完成登录：

```bash
umeng-cli login
umeng-cli login --provider aliyun
```

不要把 AccessKey、Secret、App Master Secret、Message Secret、Cookie、Token 或 Webhook 写入仓库、Issue 或日志。

## 安装 Skill

将本仓库克隆到你的 AI 编程工具所使用的 Skills 目录，并确保目录名为 `umeng-skills-index`：

```bash
git clone https://github.com/umeng/umeng-skills-index.git
```

不同 AI 工具的 Skills 目录和加载方式可能不同，请以对应工具的官方说明为准。安装后可以直接询问：

- “查询这个应用昨天的 DAU 和新增用户。”
- “排查 Android 应用的崩溃率上升问题。”
- “在 Flutter 项目中接入友盟统计。”
- “为网站接入 U-Web 并验证 SPA 页面统计。”

## 目录结构

```text
.
├── SKILL.md                    # AI Agent 主入口
├── references/
│   ├── capability-map.md       # 完整能力地图
│   ├── scenario-routes.md      # 场景路由
│   ├── trigger-keywords.md     # 触发关键词
│   └── skills/                 # 19 个子能力说明
└── scripts/                    # SDK 自动集成与验证脚本
```

## 使用数据说明

本 Skill 会按照 [SKILL.md](SKILL.md) 中的规则调用 `umeng-cli trace`，用于记录 Skill/子能力的使用情况；在业务需要且用户已经提供 AppKey 时，事件可能包含 AppKey。Trace 失败不会阻塞业务流程。

请在使用前阅读相关说明，并根据所在组织的数据与隐私要求决定是否执行。请勿在公开内容中提交任何鉴权凭证或用户数据。

## 安全与反馈

- 安全问题请参阅 [SECURITY.md](SECURITY.md)，不要通过公开 Issue 披露凭证或漏洞细节。
- 一般问题与改进建议请通过 GitHub Issues 提交，并先对日志和配置进行脱敏。
- 贡献代码前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

当前发布包未附带开源许可证。在友盟+ 明确添加许可证前，默认不授予复制、修改或再分发权限。

---

Umeng+ AI Agent skill collection for analytics queries, performance diagnostics, and SDK integration. See [SKILL.md](SKILL.md) for the agent entry point and [capability-map.md](references/capability-map.md) for all 19 capabilities.
