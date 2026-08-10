## 友盟应用资产查询技能


查询当前登录账号下的 **App 资产**（列表）、**小程序资产**（列表）、**账户资产合计**（App + 小程序）以及**被授权 App 资产**（其他账号共享给当前账号的应用清单），覆盖四类核心需求：

- **账户资产合计**：自有 App 数 + 自有小程序数（一次调用直出 `count`）
- **自有 App 资产**：App 列表（分页，客户端按 `{iphone, android, harmony, ipad}` 平台**白名单守卫**；纯 App 数走翻页 + 白名单过滤后 `.length`）
- **自有小程序资产**：小程序列表（分页，客户端按相同集合做平台**反向黑名单守卫**；纯小程序数走翻页 + 黑名单过滤后 `.length`）
- **被授权 App 资产**：被授权 App 列表（分页 + 排序，响应内 `data.count` 直出总数）

共 **4 个只读查询接口**，跨 2 个 OpenAPI 命名空间（`com.umeng.uapp` + `com.umeng.umini`）以及友盟官网域 `mobile.umeng.com`。本 Skill 为**资产发现型** —— `appkey` 是"输出"不是"输入"，无需用户提供任何应用标识即可工作。

> ⚠️ **重要事实校正**（v1.5.0）：
> 1. `umeng.uapp.getAppCount` 返回的 `count` 实际为"自有 App + 自有小程序"合计，**不是纯 App 数**；想拿纯 App 数 / 纯小程序数必须走对应列表接口翻页 + 客户端平台过滤后 `.length`。
> 2. `umeng.umini.getAppList.data.totalCount` **不可靠，已禁用**：实际值与翻页累计不一致；本 Skill 不再以此为权威小程序总数源。
> 3. `umeng.uapp.getAppList` 与 `umeng.umini.getAppList` 都可能返回平台错位的污染项，调用方必须按下文规则做白/黑名单守卫。


## 适用场景与触发词

- 用户询问"我一共注册了多少个应用？"
- 用户询问"列出我所有的 App / 我的 App 列表"
- 用户询问"我有多少小程序 / 我的小程序列表"
- 用户询问"同时列出我的 App 和小程序"
- 用户询问"我被授权了哪些 App / 别人共享给我的应用 / 我能查看哪些 App / 协作 App / 授权清单"
- 用户需要按平台（`android` / `iphone` / `harmony` / `wphone` / `mini_wechat` 等）过滤资产
- 用户在使用其他 skill 前需要先"发现"`appkey`
- 关键词：应用列表、App 列表、小程序列表、应用数量、小程序数量、应用资产、我的应用、我的小程序、有哪些 App、有哪些小程序、被授权的应用、别人授权给我的 App、协作 App、授权清单、我能看到哪些应用

## 鉴权方式

本 Skill 同时使用**两种鉴权方式**，按接口归属域名严格区分：

### 轨 1：`umeng-aksk`（OpenAPI 网关，3 个接口）

- **authType**: `umeng-aksk`（友盟 OpenAPI AK/SK 签名，HMAC-SHA1）
- **baseUrl**: `https://gateway.open.umeng.com/openapi`
- **endpoint 路径规则**：`param2/1/com.umeng.uapp/<接口名>` 或 `param2/1/com.umeng.umini/<接口名>`
- 适用接口：`getAppCount` / `uapp.getAppList` / `umini.getAppList`
- AK/SK 由 `umeng-cli login` 自动获取并加密缓存，无需手动配置 `apiKey` / `apiSecurity`

### 轨 2：`cookie`（友盟官网，1 个接口）

- **authType**: `cookie`（友盟官网登录 Cookie，会话鉴权）
- **baseUrl**: `https://mobile.umeng.com`
- **endpoint 路径规则**：`/ht/api/v3/<业务路径>`（注意 `/ht` 前缀必须显式带上，umeng-cli 不会做前端拦截器那层自动补全）
- 适用接口：`uapp.getGrantList`
- Cookie 由 `umeng-cli login` 与 AK/SK 同时获取，与 `umeng-cli/reference/website/appwin.md` 中的官网接口共享同一登录态
- 失效时同样走 `umeng-cli login --no-qr` 重新登录

> ⚠️ **两种鉴权方式不可混用**：用 `umeng-aksk` 调 mobile.umeng.com 会签名错误；用 `cookie` 调 gateway.open.umeng.com 会拒绝。

### 登录状态检查

```bash
umeng-cli whoami
```

### 登录要求

当接口返回未登录或登录态过期时，需要执行 `umeng-cli login --no-qr` 进行登录。

**AI Agent 执行登录的正确方式：**

> `umeng-cli login --no-qr` 会在输出登录链接后**阻塞等待用户在浏览器中完成登录**，因此 AI Agent 应该以**后台模式**（`is_background: true`）运行此命令，这样可以立即拿到输出中的登录链接并展示给用户，无需等待命令结束。命令会在用户完成登录后自动退出并保存凭证。

如果终端不支持显示二维码（如 AI Agent 终端、SSH 远程终端等），可以使用 `--no-qr` 参数，仅输出可点击的登录链接：

```bash
umeng-cli login --no-qr

## 输出:
## 🔄 正在生成登录链接...
## ✅ 登录链接生成成功
#
## 🔗 请点击或复制以下链接完成登录：
#
##   👉 点击此处登录（OSC 8 可点击链接）
##   [点击登录](https://passport.umeng.com/login?redirectURL=...)
##   https://passport.umeng.com/login?redirectURL=...
#
## ⏳ 等待登录...
## ✅ 授权成功！
## ✅ 登录完成！
```

## 不需要 appkey

本 Skill **不接受 `appkey` 作为入参** —— 所有 4 个接口都以"当前登录账号"为作用域，返回账号下全部 App / 小程序 / 被授权 App。`appkey`（或小程序的 `dataSourceId`）是本 Skill 的**输出**，通常用作下游 Skill（`umeng-cli-uapp-core-index` / `umeng-cli-uapp-channel-version` / `umeng-cli-uapp-retention` / `umeng-cli-uapp-event` 等）的输入。

## 通用调用格式

按鉴权方式拆分为两小节：

### A. OpenAPI 网关调用（3 个接口）

```bash
umeng-cli call '{
  "name": "<接口名>",
  "api": {
    "method": "GET",
    "baseUrl": "https://gateway.open.umeng.com/openapi",
    "endpoint": "param2/1/<namespace>/<接口名>",
    "authType": "umeng-aksk"
  }
}' '<参数JSON>'
```

- `<namespace>` 为 `com.umeng.uapp` 或 `com.umeng.umini`
- 适用：`getAppCount` / `uapp.getAppList` / `umini.getAppList`

### B. 官网 mobile 调用（1 个接口）

```bash
umeng-cli call '{
  "name": "<接口名>",
  "api": {
    "method": "GET",
    "baseUrl": "https://mobile.umeng.com",
    "endpoint": "/ht/api/v3/<业务路径>",
    "authType": "cookie",
    "headers": {"accept": "application/json"}
  }
}' '<参数JSON>'
```

- endpoint **必须**带 `/ht` 前缀
- 适用：`uapp.getGrantList`

> 4 个接口均为 `GET` 方法。

## 核心概念

### 三类资产并列

| 资产类型 | 域 / 命名空间 | 总数获取 | 列表接口 |
|---------|---------|----------|----------|
| **账户资产合计**（App + 小程序） | `com.umeng.uapp`（OpenAPI） | **`umeng.uapp.getAppCount` 一次调用直出合计 `count`** | —（合计仅出总数，不出列表） |
| 自有 App（`iphone` / `android` / `harmony` / `ipad`） | `com.umeng.uapp`（OpenAPI） | 无独立 App 数接口；走 `getAppList` 翻页 + 白名单过滤后 `.length` | `umeng.uapp.getAppList`（白名单守卫） |
| 自有小程序（微信 / 支付宝 / 字节 / 百度 / QQ / H5 等） | `com.umeng.umini`（OpenAPI） | 无独立总数接口；**`totalCount` 已禁用**，走 `getAppList` 翻页 + 黑名单过滤后 `.length` | `umeng.umini.getAppList`（黑名单守卫） |
| **被授权 App**（Android / iOS / HarmonyOS / WindowsPhone） | `mobile.umeng.com`（官网 cookie） | 走 `getGrantList.data.count`（**首页响应直出**） | **`umeng.uapp.getGrantList`** |

> 💡 **getAppCount 语义务必看准**：`count` = 自有 App + 自有小程序，**不是纯 App 数**。想拿纯 App / 纯小程序数请走对应列表接口 + 平台过滤。
>
> 💡 **自有 vs 被授权**：`getAppList` 返回“账号自己注册的 App”；`getGrantList` 返回“账号被他人授权能看的 App”。两者可能部分重叠也可能完全不交，合并时需按 `appkey` 去重。

### 分页参数差异表 ⚠️

**这是本 Skill 最容易出错的地方** —— 两个命名空间的分页参数名**完全不同**：

| 维度 | `umeng.uapp.getAppList` | `umeng.umini.getAppList` |
|------|-------------------------|--------------------------|
| 页码参数 | `page`（从 1 开始） | `pageIndex`（从 1 开始） |
| 页大小参数 | `perPage`（最大 100） | `pageSize`（默认 30） |
| 响应总页数 | `totalPage` ✅ | 无直接字段（由 `totalCount` 和 `pageSize` 客户端换算） |
| 响应总条数 | **无 `totalCount`** ❌（要取总数走 `getAppCount`） | `appListDTO.totalCount` ✅ |
| 响应当前页 | `page` | `appListDTO.currentPage` |
| 数据数组 | `appInfos[]`（根级） | `appListDTO.data[]`（嵌套一层） |

### 响应字段别名表

两个 `getAppList` 的 DTO 字段**语义相同但命名不同**，客户端合并列表时需做字段映射：

| 含义 | `uapp.getAppList.appInfos[]` | `umini.getAppList.appListDTO.data[]` |
|------|------------------------------|--------------------------------------|
| 唯一标识（即 AppKey） | `appkey` | `dataSourceId` |
| 应用名称 | `name` | `appName` |
| 平台 | `platform`（`android` / `iphone`） | `platform`（`mini_wechat` / `mini_alipay` / `mini_bytedance` / `mini_baidu` / `mini_qq` / `mini_game_wechat` / `html_5` 等） |
| 一级分类 | `category` | `firstLevel` |
| 二级分类 | 无 | `secondLevel` |
| 创建时间 | `createdAt` | `gmtCreate` |
| 更新时间 | `updatedAt` | 无 |
| 是否游戏 | `useGameSdk`（boolean） | 无（小程序通过 `mini_game_wechat` 等平台标识） |
| 是否关注 | `popular`（0/1） | 无 |
| 账号名 | 无 | `userName` |

## 接口路由表

| 接口 | 鉴权 | Endpoint（绝对 URL） | 功能 |
|------|------|----------|------|
| `umeng.uapp.getAppCount` | `umeng-aksk` | `https://gateway.open.umeng.com/openapi/param2/1/com.umeng.uapp/umeng.uapp.getAppCount` | **获取账户资产合计（自有 App + 自有小程序）**一次调用直出 `count` |
| `umeng.uapp.getAppList` | `umeng-aksk` | `https://gateway.open.umeng.com/openapi/param2/1/com.umeng.uapp/umeng.uapp.getAppList` | 获取账户下自有 App 列表（分页，`page`/`perPage`；客户端按 `{iphone,android,harmony,ipad}` 白名单守卫） |
| `umeng.umini.getAppList` | `umeng-aksk` | `https://gateway.open.umeng.com/openapi/param2/1/com.umeng.umini/umeng.umini.getAppList` | 获取账户下自有小程序列表（分页，`pageIndex`/`pageSize`；客户端按相同集合反向黑名单守卫；**响应 `data.totalCount` 不可靠已禁用**） |
| **`umeng.uapp.getGrantList`** | **`cookie`** | `https://mobile.umeng.com/ht/api/v3/app/home/grant/list` | **获取账户被授权的 App 列表**（分页 + 排序，含他人共享给当前账号的 App；响应内 `data.count` 直出总数） |

### 与本 skill 相邻能力的边界

| 能力 | 归属 Skill | 说明 |
|------|-----------|------|
| 被授权应用的指标查询（DAU/启动等） | `umeng-cli-uapp-core-index` | 本 Skill 的 `getGrantList` 仅出"被授权 App 清单"，不出指标；拿到 `appkey` 后由 core-index Skill 查询 |
| App 某日 / 趋势 DAU / 新增 / 启动等核心指标 | `umeng-cli-uapp-core-index` | 本 Skill 仅出"应用清单"，不出任何指标 |
| App 版本列表 / 渠道列表（按 appkey） | `umeng-cli-uapp-channel-version` | 本 Skill 仅管账户层级，不管 App 内部渠道/版本 |
| App 留存率 | `umeng-cli-uapp-retention` | — |
| App 自定义事件 | `umeng-cli-uapp-event` | — |
| APM（崩溃/性能） | `umeng-cli-uapm` | — |
| 小程序指标（`getOverview` / `getTotalUser` / `getRetentionByDataSourceId` 等） | 未来独立 `umeng-cli-umini-*` Skill | 本 Skill 仅覆盖小程序"清单+数量"，不覆盖小程序指标 |

---

## 操作

### 1. 获取账户资产合计数（App + 小程序） (getAppCount)

获取当前账户下**自有 App 与自有小程序**的合计数量。**无需任何参数**，一次调用直出。

> ⚠️ **语义警示**：响应 `count` **不是纯 App 数**，而是“自有 App + 自有小程序”合计。这是后端接口的真实口径，与接口名中的"App"字面不一致，调用时请以本说明为准。

**参数说明**：无

**调用示例**：

```bash
umeng-cli call '{
  "name": "umeng.uapp.getAppCount",
  "api": {
    "method": "GET",
    "baseUrl": "https://gateway.open.umeng.com/openapi",
    "endpoint": "param2/1/com.umeng.uapp/umeng.uapp.getAppCount",
    "authType": "umeng-aksk"
  }
}' '{}'
```

**返回格式**：

```json
{
  "count": 893
}
```

**返回字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | integer | 账户下自有 App 数 + 自有小程序数 的**合计**（不区分哪类） |

> 💡 **拿哪个数走哪个接口**：
> - 要“**账户资产合计**”→ 走本接口 `getAppCount`（一次直出，最快）
> - 要“**纯 App 数**”→ 走 §2 `uapp.getAppList` 翻页 + 白名单过滤后 `.length`
> - 要“**纯小程序数**”→ 走 §3 `umini.getAppList` 翻页 + 黑名单过滤后 `.length`
>
> ⚠️ 不要用 `totalPage × perPage` 估算；不要读 `umini.getAppList.data.totalCount`（不可靠已禁用）。

---

### 2. 获取 App 列表 (uapp.getAppList)

分页获取账户下 App 列表。

> ⚠️ **平台白名单守卫**：接口返回的 `appInfos[]` 可能包含平台错位的污染项，客户端必须按白名单 `{iphone, android, harmony, ipad}` 过滤，不在白名单内的项视为接口污染丢弃。

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页号，从 1 开始 |
| perPage | integer | 否 | 10 | 每页记录数（**最大 100**） |

**调用示例**：

```bash
## 默认首页
umeng-cli call '{
  "name": "umeng.uapp.getAppList",
  "api": {
    "method": "GET",
    "baseUrl": "https://gateway.open.umeng.com/openapi",
    "endpoint": "param2/1/com.umeng.uapp/umeng.uapp.getAppList",
    "authType": "umeng-aksk"
  }
}' '{}'

## 指定第 2 页，每页 100 条
umeng-cli call '{"name":"umeng.uapp.getAppList","api":{"method":"GET","baseUrl":"https://gateway.open.umeng.com/openapi","endpoint":"param2/1/com.umeng.uapp/umeng.uapp.getAppList","authType":"umeng-aksk"}}' '{"page":2,"perPage":100}'

## 白名单守卫（推荐）：仅保留 platform ∈ {iphone,android,harmony,ipad}
umeng-cli call '{"name":"umeng.uapp.getAppList","api":{"method":"GET","baseUrl":"https://gateway.open.umeng.com/openapi","endpoint":"param2/1/com.umeng.uapp/umeng.uapp.getAppList","authType":"umeng-aksk"}}' '{"page":1,"perPage":100}' \
  | jq '.appInfos |= map(select(.platform | IN("iphone","android","harmony","ipad")))'
```

**返回格式**：

```json
{
  "appInfos": [
    {
      "appkey": "4f83c5d852701564c0000011",
      "name": "友盟SDK",
      "platform": "android",
      "category": "工具",
      "createdAt": "2012-04-10 10:00:00",
      "updatedAt": "2026-04-28 09:00:00",
      "useGameSdk": false,
      "popular": 1
    }
  ],
  "totalPage": 9,
  "page": 1
}
```

**返回字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `appInfos[].appkey` | string | 应用 ID（AppKey），下游 skill 的输入 |
| `appInfos[].name` | string | App 名称 |
| `appInfos[].platform` | string | 平台枚举：**必须为 `iphone` / `android` / `harmony` / `ipad` 四值之一**；接口可能返回非 App 类型的污染项，客户端必须按白名单守卫 |
| `appInfos[].category` | string | 应用分类（单级） |
| `appInfos[].createdAt` | string | 创建时间 |
| `appInfos[].updatedAt` | string | 更新时间 |
| `appInfos[].useGameSdk` | boolean | 是否为游戏 |
| `appInfos[].popular` | integer | 是否关注（0/1） |
| `totalPage` | integer | 总页数 |
| `page` | integer | 当前页号 |

**关键提示** ⚠️：

- 🔴 **`platform` 必须白名单守卫**：返回结果中 `platform` **不在** `{iphone, android, harmony, ipad}` 中的项为接口污染，**必须丢弃**（获取纯 App 数 / 按平台过滤 / 下发下游 Skill 前都应先守卫）。
- ⚠️ **本接口响应没有 `totalCount` 字段**。若需要 “纯 App 数”，**必须**翻页全量 + 白名单过滤后 `.length`，不要用 `(totalPage-1) × perPage + appInfos.length` 估算，也不要读 `getAppCount.count`（那是 App + 小程序的合计）。

---

### 3. 获取小程序列表 (umini.getAppList)

分页获取账户下小程序列表。

> ⚠️ **平台反向黑名单守卫**：接口返回的 `data.data[]` 可能混入 App 类型项目（`platform` 落入 `{iphone, android, harmony, ipad}`），客户端必须做**反向黑名单过滤** —— `platform` 落入这 4 个 App 平台的项为接口污染，必须丢弃。
>
> ⚠️ **`data.totalCount` 已禁用**：该字段与翻页累计不一致，本 Skill **不再以此为权威小程序总数源**；纯小程序数走“翻页全量 + 黑名单过滤后 `.length`”。

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| pageIndex | integer | 否 | 1 | 页号，从 1 开始（**注意不是 `page`**） |
| pageSize | integer | 否 | 30 | 每页记录数（**注意不是 `perPage`**） |

**调用示例**：

```bash
## 默认首页
umeng-cli call '{
  "name": "umeng.umini.getAppList",
  "api": {
    "method": "GET",
    "baseUrl": "https://gateway.open.umeng.com/openapi",
    "endpoint": "param2/1/com.umeng.umini/umeng.umini.getAppList",
    "authType": "umeng-aksk"
  }
}' '{}'

## 正常分页（第 1 页，每页 100）
umeng-cli call '{"name":"umeng.umini.getAppList","api":{"method":"GET","baseUrl":"https://gateway.open.umeng.com/openapi","endpoint":"param2/1/com.umeng.umini/umeng.umini.getAppList","authType":"umeng-aksk"}}' '{"pageIndex":1,"pageSize":100}'

## 黑名单守卫（推荐）：排除 platform ∈ {iphone,android,harmony,ipad}
umeng-cli call '{"name":"umeng.umini.getAppList","api":{"method":"GET","baseUrl":"https://gateway.open.umeng.com/openapi","endpoint":"param2/1/com.umeng.umini/umeng.umini.getAppList","authType":"umeng-aksk"}}' '{"pageIndex":1,"pageSize":100}' \
  | jq '.data.data |= map(select(.platform | IN("iphone","android","harmony","ipad") | not))'
```

**返回格式**：

```json
{
  "data": {
    "data": [
      {
        "dataSourceId": "5e8c6dea978eea071c37c682",
        "appName": "示例小程序",
        "platform": "mini_wechat",
        "firstLevel": "公共交通与出行",
        "secondLevel": "公共交通",
        "gmtCreate": "2020-03-10 10:00:00",
        "userName": "alice@example.com"
      }
    ],
    "totalCount": 42,
    "currentPage": 1
  },
  "msg": "",
  "code": 0,
  "success": true
}
```

**返回字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.data[].dataSourceId` | string | 小程序的 AppKey（下游 skill 的输入） |
| `data.data[].appName` | string | 小程序名称 |
| `data.data[].platform` | string | 小程序平台（见下文枚举表）；**接口可能混入 `iphone`/`android`/`harmony`/`ipad` 的 App 污染项**，客户端必须反向黑名单过滤 |
| `data.data[].firstLevel` | string | 一级分类 |
| `data.data[].secondLevel` | string | 二级分类 |
| `data.data[].gmtCreate` | string | 创建时间 |
| `data.data[].userName` | string | 账号名 |
| `data.totalCount` | integer | ⚠️ **不可靠，禁用**：实际值与翻页累计 `.length` 经常不一致；本 Skill 不再以此为权威小程序总数源，请勿读取 |
| `data.currentPage` | integer | 当前页号 |

**关键提示** ⚠️：

- 🔴 **`platform` 必须反向黑名单守卫**：`platform` 落入 `{iphone, android, harmony, ipad}` 的项为接口污染，**必须丢弃**（获取纯小程序数 / 按平台过滤 / 下发下游 Skill 前都应先守卫）。
- 🔴 **`totalCount` 不可靠已禁用**：想要“纯小程序数”？走翻页全量 + 黑名单过滤后 `.length`，不要读 `data.totalCount`，也不要读 `getAppCount.count`（那是 App + 小程序的合计）。
- ⚠️ **末页判定**：翻页循环时不能依赖 `totalCount` 预算总页数；改为“某页返回 `data.data` 长度 < `pageSize` 则视为末页”的推进式累计。

---

### 4. 获取被授权 App 列表 (uapp.getGrantList)

分页获取当前账号**被授权**的 App 列表——包含**其他账号通过友盟后台共享给当前账号**的 App，与 `uapp.getAppList`（仅返回账号自己注册的 App）互补。

> ⚠️ **本接口为官网内部接口**（非 OpenAPI 公开接口），鉴权走 `cookie`，endpoint **必须**带 `/ht` 前缀。

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页号，从 1 开始 |
| pageSize | integer | 否 | 30 | 每页记录数，**只接受枚举值：30 / 60 / 90 / 120**（其他值后端可能回退默认） |
| sortBy | string | 否 | — | 排序字段名，常见取值：`todayLaunch` / `todayNewUser` / `todayActiveUser` / `todayTotalUser` / `launch` / `newUser` / `activeUser` / `totalUser`；**不传则不附带**（避免传空字符串） |
| sortType | string | 否 | — | 排序方向：`asc` / `desc`；仅在 `sortBy` 已传时生效 |

**调用示例**：

```bash
## 默认首页（默认排序）
umeng-cli call '{
  "name": "umeng.uapp.getGrantList",
  "api": {
    "method": "GET",
    "baseUrl": "https://mobile.umeng.com",
    "endpoint": "/ht/api/v3/app/home/grant/list",
    "authType": "cookie",
    "headers": {"accept": "application/json"}
  }
}' '{}'

## 指定第 2 页，每页 60
 umeng-cli call '{"name":"umeng.uapp.getGrantList","api":{"method":"GET","baseUrl":"https://mobile.umeng.com","endpoint":"/ht/api/v3/app/home/grant/list","authType":"cookie","headers":{"accept":"application/json"}}}' '{"page":2,"pageSize":60}'

## 按“历史累计用户数”降序，取 Top 120
umeng-cli call '{"name":"umeng.uapp.getGrantList","api":{"method":"GET","baseUrl":"https://mobile.umeng.com","endpoint":"/ht/api/v3/app/home/grant/list","authType":"cookie","headers":{"accept":"application/json"}}}' '{"page":1,"pageSize":120,"sortBy":"totalUser","sortType":"desc"}'
```

**返回格式**：

```json
{
  "code": 200,
  "msg": "成功",
  "sCode": 200,
  "sMsg": "成功",
  "status": true,
  "timestamp": 1717891200000,
  "traceId": "abc123def456",
  "data": {
    "count": 42,
    "page": 1,
    "pageSize": 30,
    "list": [
      {
        "appkey": "4f83c5d852701564c0000011",
        "name": "示例应用",
        "account": "alice@example.com",
        "platform": "android",
        "auth": true,
        "star": false,
        "appLevel": 1,
        "todayLaunch": 12345,
        "todayNewUser": 678,
        "todayActiveUser": 9012,
        "todayTotalUser": 345678,
        "launch": 98765432,
        "newUser": 1234567,
        "activeUser": 234567,
        "totalUser": 3456789
      },
      {
        "appkey": "5a83c5d852701564c0000022",
        "name": "只读共享 App",
        "account": "bob@example.com",
        "platform": "iphone",
        "auth": false,
        "star": true,
        "appLevel": 0,
        "todayLaunch": "*",
        "todayNewUser": "*",
        "todayActiveUser": "*",
        "todayTotalUser": "*",
        "launch": "*",
        "newUser": "*",
        "activeUser": "*",
        "totalUser": "*"
      }
    ]
  }
}
```

**返回字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 业务状态码，200 表示成功 |
| `msg` | string | 状态消息 |
| `status` | boolean | 请求是否成功 |
| `traceId` | string | 请求追踪 ID，用于日志排查 |
| `data.count` | integer | **被授权 App 总数**（首页响应直出，无需翻页） |
| `data.page` | integer | 当前页号 |
| `data.pageSize` | integer | 当前请求的每页条数 |
| `data.list[].appkey` | string | 应用 AppKey（下游 skill 的输入） |
| `data.list[].name` | string | 应用名称 |
| `data.list[].account` | string | 应用所属账号（其他人的邮箱或账号） |
| `data.list[].platform` | string | 平台：`iphone` / `android` / **`harmony`** / **`wphone`**（注意特有 harmony/wphone，`getAppList` 不返回这两个平台） |
| `data.list[].auth` | boolean | **当前账号是否拥有该 App 的完整权限**；`false` 时所有指标字段会脱敏为字符串 `"*"` |
| `data.list[].star` | boolean | 是否已收藏 |
| `data.list[].appLevel` | integer | 应用等级（0 或 1） |
| `data.list[].todayLaunch` | number \| `"*"` | 今日启动次数；**无权限时为 `"*"`** |
| `data.list[].todayNewUser` | number \| `"*"` | 今日新增用户数 |
| `data.list[].todayActiveUser` | number \| `"*"` | 今日活跃用户数 |
| `data.list[].todayTotalUser` | number \| string \| `"*"` | 今日累计用户数 |
| `data.list[].launch` | number \| `"*"` | 历史总启动次数 |
| `data.list[].newUser` | number \| `"*"` | 历史总新增用户数 |
| `data.list[].activeUser` | number \| `"*"` | 历史活跃用户数 |
| `data.list[].totalUser` | number \| string \| `"*"` | 历史累计用户数 |

**关键提示** ⚠️：

- 🔴 **`"*"` 脱敏值**：指标字段在 `auth: false` 时会返回字符串 `"*"`（不是 number）。**切勿直接做数值运算**（加、除、汇总、排序均会产生 `NaN` 或字符串拼接），必须先做 `typeof === 'number'` 守卫。
- 🔴 **`/ht` 前缀必须**：endpoint 写成 `/api/v3/app/home/grant/list`（不带 `/ht`）会直接 404。
- 🟡 **平台枚举**：`platform` 取值为 `iphone` / `android` / `harmony` / `wphone`，比 `uapp.getAppList` 多出 `harmony` / `wphone`；被授权清单中的鸿蒙应用只能走本接口拿到。
- 🟡 **内部接口、非公开 OpenAPI**：本接口面向友盟官网内部使用，未记录于公开 OpenAPI 文档，**字段可能随官网迭代变更**；如需高 SLA 场景请优先使用 `getAppList`。
- 🟢 **总数一次拿到**：首页响应的 `data.count` 即为被授权 App 总数，类似 `umini.getAppList.totalCount`，无需独立的计数接口。

---

## 公共约束

### 分页差异速查（核心）

| 接口 | 页码字段 | 页大小字段 | 总数字段 | 数据数组路径 |
|------|----------|------------|----------|---------------|
| `uapp.getAppList` | `page` | `perPage`（最大 100） | **无**（纯 App 数走翻页 + 白名单过滤后 .length；`getAppCount.count` 是 App+小程序合计） | `appInfos[]`（根级） |
| `umini.getAppList` | `pageIndex` | `pageSize`（默认 30） | **无**（`data.totalCount` **不可靠已禁用**；纯小程序数走翻页 + 黑名单过滤后 .length） | `data.data[]`（嵌套） |
| `uapp.getGrantList` | `page` | `pageSize`（枚举 30/60/90/120） | `data.count` ✅ | `data.list[]`（嵌套） |
| `getAppCount` | — | — | `count`（直出）——语义为 **App + 小程序合计** | — |

### 平台枚举与客户端过滤

本 Skill 接口**不支持服务端按平台过滤**，且**必须按以下规则在客户端做平台守卫**：

- `uapp.getAppList`：**白名单**仅保留 `platform ∈ {iphone, android, harmony, ipad}` 的项
- `umini.getAppList`：**黑名单**反向排除 `platform ∈ {iphone, android, harmony, ipad}` 的项
- `uapp.getGrantList`：接口原生仅返回 App 类平台（`iphone`/`android`/`harmony`/`wphone`），无需预过滤

枚举参考：

| 过滤需求 | `uapp.appInfos[].platform`（白名单之后才有效） | `umini.data.data[].platform`（已排除 `{iphone,android,harmony,ipad}` 后才有效） | `uapp.getGrantList.data.list[].platform` 取值 |
|----------|----------------------------------|-----------------------------------|--------------------------------------------------|
| Android App | `android` | — | `android` |
| iOS（iPhone） App | `iphone` | — | `iphone` |
| iPad App | `ipad`（**仅 uapp.getAppList 返回**） | — | — |
| HarmonyOS App | `harmony`（uapp 与 getGrantList 都返回） | — | `harmony` |
| WindowsPhone App | — | — | `wphone`（**仅 getGrantList 返回**） |
| 微信小程序 | — | `mini_wechat` | — |
| 支付宝小程序 | — | `mini_alipay` | — |
| 字节跳动小程序 | — | `mini_bytedance` | — |
| 百度小程序 | — | `mini_baidu` | — |
| QQ 小程序 | — | `mini_qq` | — |
| 微信小游戏 | — | `mini_game_wechat` | — |
| H5 | — | `html_5` | — |

**jq 客户端过滤示例**：

```bash
## 【白名单守卫】uapp.getAppList：仅保留有效 App 平台
umeng-cli call '...uapp.getAppList...' '{"page":1,"perPage":100}' \
  | jq '.appInfos |= map(select(.platform | IN("iphone","android","harmony","ipad")))'

## 【白名单 + 单平台】过滤 Android App（先白名单再按单平台筛选）
umeng-cli call '...uapp.getAppList...' '{"page":1,"perPage":100}' \
  | jq '.appInfos | map(select(.platform | IN("iphone","android","harmony","ipad"))) | map(select(.platform == "android"))'

## 【黑名单守卫】umini.getAppList：反向排除 4 个 App 平台
umeng-cli call '...umini.getAppList...' '{"pageIndex":1,"pageSize":100}' \
  | jq '.data.data |= map(select(.platform | IN("iphone","android","harmony","ipad") | not))'

## 【黑名单 + 单平台】过滤所有微信系小程序
umeng-cli call '...umini.getAppList...' '{"pageIndex":1,"pageSize":100}' \
  | jq '.data.data | map(select(.platform | IN("iphone","android","harmony","ipad") | not)) | map(select(.platform | startswith("mini_wechat") or . == "mini_game_wechat"))'

## 【黑名单 + 模糊】所有小程序（旧 `--platform mini`）
umeng-cli call '...umini.getAppList...' '{"pageIndex":1,"pageSize":100}' \
  | jq '.data.data | map(select(.platform | IN("iphone","android","harmony","ipad") | not)) | map(select(.platform | startswith("mini")))'
```

### 翻页全量遍历

本 Skill 接口**不提供"一次拉完所有"**的能力。客户端如需全量（`getAppCount.count` 是 App+小程序 合计，**不能**用来预算任一列表接口的总页数）：

- 自有 App：首次调用 `page=1, perPage=100` 拿首页，后续递增 `page` 循环拉取，**某页 `appInfos.length < perPage` 则视为末页**；每页先做白名单过滤后再累计。也可参考首页响应的 `totalPage` 作为辅助预算，但服务端未守卫的总数不作为总数权威。
- 自有小程序：**不要读 `data.totalCount`**（不可靠已禁用）；首次调用 `pageIndex=1, pageSize=100` 拿首页，后续递增 `pageIndex` 循环拉取，**某页 `data.data.length < pageSize` 则视为末页**；每页先做黑名单过滤后再累计。
- 被授权 App：首次调用 `pageSize=120, page=1` 拿 `data.count` → 计算 `ceil(count / 120)` → 循环 `page=2..N`（`pageSize` 只能取 30/60/90/120，推荐 120）

### 输出格式

`umeng-cli call` 原生输出 JSON。旧 skill 的 `--output table` / `--output json` 开关不再存在，**Markdown 表格由 LLM 按需在摘要时整理**。

## 典型工作流

### 工作流 1：账户资产合计（App + 小程序，1 次调用直出）

```
需求："我账户下一共多少应用？" / "我的应用资产总数？"
1. getAppCount()   ← 无参
2. 读响应 count（语义：App + 小程序 合计）
3. 回复："你在友盟一共有 <count> 个应用（含自有 App + 自有小程序）。"
```

> ⚠️ 若用户明确问“纯 App 数”或“纯小程序数”，请走工作流 1A / 1B，不要直接返回 getAppCount.count。

### 工作流 1A：纯 App 数（翻页 + 白名单过滤）

```
需求："我有多少 App（不含小程序）？"
1. 首页：uapp.getAppList(page=1, perPage=100)
2. 循环拉全：page=2..N，某页 appInfos.length < 100 则末页停止
3. 每页白名单过滤：platform ∈ {iphone, android, harmony, ipad}
4. .length 计数 → 回复："你有 <N> 个 App。"
```

### 工作流 2：纯小程序数（翻页 + 黑名单过滤）

```
需求："我有多少小程序？"
1. 首页：umini.getAppList(pageIndex=1, pageSize=100)
2. 循环拉全：pageIndex=2..N，某页 data.data.length < 100 则末页停止
3. 每页黑名单过滤：platform ∉ {iphone, android, harmony, ipad}
4. .length 计数 → 回复："你有 <N> 个小程序。"

⚠️ 不要读 data.totalCount（不可靠已禁用）；不要用 getAppCount.count 减去 App 数推算（App+小程序 合计与各列表接口应独立看）。
```

### 工作流 3：App + 小程序合并清单（对应旧 --list-all）

```
需求："把我所有的 App 和小程序都列出来"
1. 并行拉取：
   uapp.getAppList(page=1..N, perPage=100)        ← 末页判定：appInfos.length < 100
   umini.getAppList(pageIndex=1..N, pageSize=100) ← 末页判定：data.data.length < 100（不读 totalCount）
2. 各自平台守卫：
   - uapp 边：仅保留 platform ∈ {iphone, android, harmony, ipad}
   - umini 边：仅保留 platform ∉ {iphone, android, harmony, ipad}
3. 合并两份 data，字段映射：
   - uapp.appInfos[].appkey ↔ umini.data.data[].dataSourceId → 统一字段 "key"
   - uapp.appInfos[].name ↔ umini.data.data[].appName → 统一字段 "name"
   - uapp.appInfos[].platform ↔ umini.data.data[].platform → 统一字段 "platform"
4. 摘要：总 App 数 / 总小程序数 / 按平台分组计数
```

### 工作流 4：按平台过滤（对应旧 --platform）

```
需求："列出我所有的 Android App"
1. uapp.getAppList 翻页拉全（末页判定：appInfos.length < 100）
2. 白名单守卫：platform ∈ {iphone, android, harmony, ipad}
3. jq/客户端过滤 platform == "android" 的项
4. 摘要：Android App 数量、名称与 appkey 列表

需求："列出我的微信小程序"
1. umini.getAppList 翻页拉全（末页判定：data.data.length < 100；不读 totalCount）
2. 黑名单守卫：platform ∉ {iphone, android, harmony, ipad}
3. 客户端过滤 platform == "mini_wechat"
4. 摘要：微信小程序数量与 dataSourceId 列表
```

### 工作流 5：被授权应用清单（本 Skill 净增量能力）

```
需求："我被授权了哪些 App？" / "别人共享给我的应用"
1. getGrantList(page=1, pageSize=120)   ← 首页同时拿到 data.count 与首页列表
2. 若 data.count > 120：计算总页数 ceil(count / 120) → 循环 page=2..N
3. 合并后可选：按 platform 分组（android / iphone / harmony / wphone）
4. 摘要：被授权 App 总数、名称与 appkey 列表、所属账号（account）

⚠️ 指标字段汇总（如“总启动次数”）前必须先用 typeof === 'number' 过滤 "*" 脱敏值。

需求："我能看到哪些鸿蒙应用？"
1. getGrantList(page=1, pageSize=120) 拿首页 + count
2. 翻页拉全
3. jq：.data.list[] | select(.platform == "harmony")
4. 摘要：鸿蒙应用数量与 appkey
```

### 工作流 6：自有 + 被授权合并清单

```
需求："我能看到的所有 App（含自有 + 被授权）"
1. uapp.getAppList(page=1..N, perPage=100)     ← 并行，末页判定 + 白名单守卫
   getGrantList(page=1, pageSize=120)         ← 并行
2. 两边翻页拉全（uapp 某页 < 100 末页；getGrantList 依 `data.count` 预算）
3. 以 appkey 为去重键合并：
   - 双边都有的 → 表示“自有且本人主账号”，以 getAppList 为准
   - 仅 getGrantList 有的 → “被授权 App”
4. 摘要：总数、自有数、被授权数、按平台分组
```

## 边界条件与错误处理

- **账户下无任何 App**：`getAppCount` 返回 `count=0`（合计也为 0）；`uapp.getAppList` 返回 `appInfos=[]`，`totalPage=0`
- **账户下无任何小程序**：`umini.getAppList` 返回 `data.data=[]`（**不要看 `data.totalCount`**，已禁用）
- **账户未被任何人授权**：`getGrantList` 返回 `data.list=[]`，`data.count=0`
- **`getAppCount.count` 语义**：合计 = 自有 App + 自有小程序，**不是纯 App 数**；要纯 App 数 / 纯小程序数走对应列表接口翻页 + 平台守卫 + `.length`
- **`uapp.getAppList` 平台白名单守卫必做**：`platform ∉ {iphone, android, harmony, ipad}` 的项视为接口污染，**计数 / 下游使用前必须丢弃**
- **`umini.getAppList` 平台反向黑名单守卫必做**：`platform ∈ {iphone, android, harmony, ipad}` 的项视为接口污染，**计数 / 下游使用前必须丢弃**
- **`umini.getAppList.data.totalCount` 不可靠已禁用**：与翻页累计不一致；纯小程序数走翻页 + 黑名单过滤后 `.length`，**不要读 `totalCount`**
- **末页判定法**：`uapp.getAppList` / `umini.getAppList` 翻页循环时，**当某页数据数组长度 < 请求 pageSize/perPage 时即视为末页**；不要依赖 `totalCount` / `getAppCount.count` 预算总页数
- **`page` / `pageIndex` 越界**：返回空数组；`getGrantList` 可由 `data.count` 预判最大页数，`uapp/umini.getAppList` 改用末页判定法推进
- **`perPage > 100`**：`uapp.getAppList` 会被服务端截断到 100；客户端应主动限制在 100 以内
- **`getGrantList.pageSize` 取值**：仅 30/60/90/120 有效，其他值后端可能回退默认；不要传 `pageSize=1000000` 这种变体参数（那属于 `listnew` 变体，本 Skill **未封装**）
- **`getGrantList.sortBy` 不要传空字符串**：需要默认排序时直接省略该参数，不要传 `""`（后端可能报错）
- **`getGrantList` 响应中的 `"*"`**：所有指标字段在 `auth: false` 时为字符串 `"*"`；做汇总/排序前必须 `typeof === 'number'` 过滤，否则产生 `NaN` 或字符串拼接
- **混淆分页参数**：`uapp.getAppList` 传 `pageIndex`/`pageSize` 会被忽略并退化为默认首页；`umini.getAppList` 传 `page`/`perPage` 同理；`getGrantList` 使用“`page`+`pageSize`”，与 `umini` 部分重叠但页码字段不同，**调用前必须看准接口**
- **混用鉴权方式**：OpenAPI 3 个接口必须走 `umeng-aksk`；`getGrantList` 必须走 `cookie`；互换会直接签名错误或 401
- **禁止用 `getAppCount.count` 反推纯 App 数 / 纯小程序数**：合计减去任意一边都依赖另一边的真实计数；务必走列表接口翻页 + 平台守卫 + `.length`
- **按平台过滤**：接口不支持服务端过滤；客户端用 jq / LLM 后处理（uapp 端先白名单守卫；umini 端先黑名单守卫）
- **未登录 / 登录态过期**：执行 `umeng-cli login --no-qr`（AI Agent 以后台模式运行并将链接展示给用户）；**这同时刷新 AK/SK 与 Cookie 两个凭证**
- **小程序与 App 合并**：`appkey` 与 `dataSourceId` 都是"AppKey"，但**分别在不同命名空间**注册，合并清单时无需去重
- **自有 vs 被授权合并**：`uapp.getAppList` 和 `getGrantList` 都返回 App 范畴的 `appkey`，同一 App 可能同时出现在两个接口（如本人账号是该 App 的主账号），合并时**需按 `appkey` 去重**

## 典型问法 → 接口/参数映射

| 典型问法 | 调用 | 参数 & 后处理 |
|----------|------|---------------|
| "我账户下一共多少应用？" / "我的应用资产合计？" | `getAppCount` | 无参；读 `count`（**App + 小程序合计**） |
| "我有多少 App（不含小程序）？" | `uapp.getAppList` | 翻页拉全（末页判定）+ 白名单 `{iphone,android,harmony,ipad}` 过滤后 `.length` |
| "我有多少小程序？" | `umini.getAppList` | 翻页拉全（末页判定）+ 黑名单（排除上述 4 个 App 平台）过滤后 `.length`；**不读 `data.totalCount`** |
| "我被授权了多少个 App？" | `getGrantList` | `page=1,pageSize=30`；读 `data.count` |
| "列出我所有的 App" | `uapp.getAppList` | `page=1,perPage=100`（可能需翻页）+ 白名单守卫 |
| "列出我所有的 Android App" | `uapp.getAppList` + 客户端过滤 | 先白名单守卫，再 `platform == "android"` |
| "列出我所有的 iOS App" | `uapp.getAppList` + 客户端过滤 | 先白名单守卫，再 `platform == "iphone"` |
| "我的小程序列表" | `umini.getAppList` | `pageIndex=1,pageSize=100` + 黑名单守卫 |
| "我的微信小程序" | `umini.getAppList` + 客户端过滤 | 先黑名单守卫，再 `platform == "mini_wechat"` |
| "我的字节跳动小程序" | `umini.getAppList` + 客户端过滤 | 先黑名单守卫，再 `platform == "mini_bytedance"` |
| "同时列出我的 App 和小程序" | `uapp.getAppList` + `umini.getAppList` | 两边各自做平台守卫后客户端合并（字段别名） |
| "我被授权了哪些 App？" | `getGrantList` | `page=1,pageSize=120`（可能需翻页） |
| "别人共享给我的应用" / "我的协作应用清单" | `getGrantList` | 同上 |
| "列出我能看到的鸿蒙 App" / "我能看到哪些 harmony 应用" | `getGrantList` + 客户端过滤 | `.platform == "harmony"` |
| "列出我能看到的所有 App（含自有 + 被授权）" | `uapp.getAppList` + `getGrantList` | 客户端以 `appkey` 去重合并 |
| "下一页" | 对应的列表接口 | `page+1` 或 `pageIndex+1` |
| "某 App 的 DAU / 启动次数 / 留存" | 指向 `umeng-cli-uapp-core-index` / `-retention` 等 | 用本 Skill 拿到的 `appkey` 作为输入 |
| "小程序的累计用户 / 分享数据" | 指向未来 `umeng-cli-umini-*` Skill | 用本 Skill 拿到的 `dataSourceId` 作为输入 |

### 旧 skill 参数等价对照

旧 `uapp-assets` 的 CLI 参数与新接口的等价关系：

| 旧 CLI 参数 | 新接口调用 |
|-------------|------------|
| `--count` | `getAppCount`（等价直出 App 总数） |
| `--list-apps` | `uapp.getAppList`（默认首页） |
| `--list-apps --page N` | `uapp.getAppList`，`page=N` |
| `--list-apps --per-page M`（最大 100） | `uapp.getAppList`，`perPage=M` |
| `--list-apps --platform android` | `uapp.getAppList` + 客户端 jq 先白名单守卫再 `select(.platform == "android")` |
| `--list-apps --platform iphone` | 同上，先白名单守卫再 `.platform == "iphone"` |
| `--list-apps --platform ios` | 同上，先白名单守卫再 `.platform == "iphone"`（`ios` 是别名） |
| `--list-minis` | `umini.getAppList`（默认首页） |
| `--list-minis --page N` | `umini.getAppList`，`pageIndex=N`（**注意不是 `page`**） |
| `--list-minis --per-page M` | `umini.getAppList`，`pageSize=M`（**注意不是 `perPage`**） |
| `--list-minis --platform mini` | `umini.getAppList` + 客户端 jq 先黑名单守卫再 `select(.platform \| startswith("mini"))` |
| `--list-minis --platform mini_bytedance` | 同上，先黑名单守卫再 `.platform == "mini_bytedance"` |
| `--list-all` | 并行 `uapp.getAppList` + `umini.getAppList`，客户端合并（见工作流 3） |
| `--output json` | `umeng-cli call` 原生输出即 JSON，无需额外开关 |
| `--output table` | 由 LLM 按需从 JSON 整理为 Markdown 表格 |
| `--config <path>` | 不再支持；登录态由 `umeng-cli login` 管理 |

> 💡 **`getGrantList`（被授权 App 列表）为本 Skill 净增量能力**，旧 `uapp-assets` skill **不覆盖**该能力，无对应的旧 CLI 参数。

## 注意事项

- 本 Skill **仅覆盖 4 个只读查询接口**：`getAppCount` + `uapp.getAppList` + `umini.getAppList` + `uapp.getGrantList`；不涉及任何写入或编辑
- 4 个接口均为 `GET` 方法；**均不需要 `appkey`**（账户级接口）
- **鉴权方式区分**：OpenAPI 3 个接口用 `umeng-aksk`，`getGrantList` 用 `cookie`；**混用会失败**（签名错误或 401）
- **分页参数命名严格区分**：`uapp.getAppList` 用 `page`/`perPage`，`umini.getAppList` 用 `pageIndex`/`pageSize`，`getGrantList` 用 `page`/`pageSize`；混用会被忽略
- **账户资产合计走 `getAppCount`**：响应 `count` = 自有 App + 自有小程序合计，**不是纯 App 数**；纯 App / 纯小程序数走对应列表接口翻页 + 客户端平台过滤后 `.length`
- **`uapp.getAppList` 必须做白名单守卫**：仅保留 `platform ∈ {iphone, android, harmony, ipad}`；不在白名单的项为接口污染
- **`umini.getAppList` 必须做反向黑名单守卫**：排除 `platform ∈ {iphone, android, harmony, ipad}`；落入黑名单的项为接口污染
- **`umini.getAppList.data.totalCount` 不可靠已禁用**：与翻页累计不一致，禁止读取；纯小程序数必须走翻页 + 黑名单过滤后 `.length`
- **末页判定法**：两个 `getAppList` 翻页循环都以"某页数据数组长度 < 请求页大小"判定末页，不依赖 `totalCount` / `getAppCount.count` 预算总页数
- **被授权 App 总数走 `getGrantList.data.count`**：首页响应直出，无需独立计数接口
- **字段别名**：`appkey`（uapp / getGrantList） ↔ `dataSourceId`（umini） / `name`（uapp / getGrantList） ↔ `appName`（umini） / `createdAt`（uapp） ↔ `gmtCreate`（umini）；合并清单时记得映射
- **自有 vs 被授权语义边界**：`uapp.getAppList` 仅返回“账号自己注册的 App”；`getGrantList` 返回“账号被他人授权能看的 App”；两者可能部分重叠也可能完全不交，合并时需按 `appkey` 去重
- **`getGrantList` 为官网内部接口**：非公开 OpenAPI，字段稳定性低于 OpenAPI；如有 SLA 要求请优先使用 `getAppList`
- **`getGrantList` 的 `"*"` 脱敏值**：`auth: false` 时指标字段为字符串 `"*"`，做汇总/排序前必须 `typeof === 'number'` 过滤
- **`/ht` 前缀必须**：`getGrantList` 的 endpoint 必须带 `/ht`（不同于 OpenAPI 的 `param2/1/...` 路径）
- **平台过滤**：接口无服务端过滤参数，由客户端 jq / LLM 后处理；`uapp.getAppList` 平台白名单为 `{iphone, android, harmony, ipad}`（其中 `ipad` 仅本接口返回），`umini` 平台以 `mini_*` / `html_5` 开头需做黑名单守卫，**`getGrantList` 额外返回 `harmony` / `wphone`**（`wphone` 仅本接口返回）
- **`perPage` 上限 100**：`uapp.getAppList` 服务端截断；`umini` 未见明确上限但建议同值；`getGrantList.pageSize` 仅枚举 30/60/90/120
- **小程序指标查询不在本 Skill**：`umeng.umini.getOverview` / `getTotalUser` / `getRetentionByDataSourceId` 等归未来的 `umeng-cli-umini-*` Skill
- **App 指标查询不在本 Skill**：DAU / 新增 / 启动 / 留存 / 渠道 / 版本 / 事件 / APM 等均由对应 `umeng-cli-uapp-*` / `umeng-cli-uapm` 处理；被授权 App 的指标查询同样走 core-index 等 Skill（本 Skill 只负责出“被授权 appkey”）
- **不封装 listnew 变体**：`/ht/api/v3/app/home/grant/listnew`（AI 简报全量拉取变体、必传 `ai=1`、常传 `pageSize=1000000`）**未在本 Skill 封装范围**；如需全量拉取请走工作流 5 的翻页方案

## 快速参考

| # | 接口 | 鉴权 | Endpoint（绝对 URL） | 必填参数 | 可选参数 | 用途 |
|---|------|------|----------|----------|----------|------|
| 1 | `umeng.uapp.getAppCount` | `umeng-aksk` | `https://gateway.open.umeng.com/openapi/param2/1/com.umeng.uapp/umeng.uapp.getAppCount` | — | — | **账户资产合计**（直出 `count`，= 自有 App + 自有小程序，**不是纯 App 数**） |
| 2 | `umeng.uapp.getAppList` | `umeng-aksk` | `https://gateway.open.umeng.com/openapi/param2/1/com.umeng.uapp/umeng.uapp.getAppList` | — | `page`（默认 1）/ `perPage`（默认 10，最大 100） | 自有 App 列表（响应 `appInfos[]` + `totalPage` + `page`，**无 totalCount**；客户端按 `{iphone,android,harmony,ipad}` 白名单守卫） |
| 3 | `umeng.umini.getAppList` | `umeng-aksk` | `https://gateway.open.umeng.com/openapi/param2/1/com.umeng.umini/umeng.umini.getAppList` | — | `pageIndex`（默认 1）/ `pageSize`（默认 30） | 自有小程序列表（响应 `data.data[]` + `data.currentPage`；客户端按相同集合反向黑名单守卫；**`data.totalCount` 不可靠已禁用**，纯小程序数走翻页 + 黑名单过滤后 `.length`） |
| 4 | **`umeng.uapp.getGrantList`** | **`cookie`** | `https://mobile.umeng.com/ht/api/v3/app/home/grant/list` | — | `page`（默认 1）/ `pageSize`（枚举 30/60/90/120）/ `sortBy` / `sortType`（`asc`/`desc`） | **被授权 App 列表**（响应 `data.list[]` + `data.count`，含 `harmony` / `wphone` 平台，指标字段可能为 `"*"`） |

> 完整 uapp namespace 其他接口（如 `getYesterdayData` / `getRetentions` / `event.list` 等）请参考 [umeng-cli/reference/openapi/uapp.md](../../../umeng-cli/reference/openapi/uapp.md)；完整 umini namespace 接口请参考 [umeng-cli/reference/openapi/umini.md](../../../umeng-cli/reference/openapi/umini.md)。
> `getGrantList` 官网接口完整字段定义与风险分析请参考 [openapi-doc/API_ANALYSIS_grant_list.md](../../../openapi-doc/API_ANALYSIS_grant_list.md)（本接口为官网内部接口，未记录于 OpenAPI 公开文档）。
> App 核心指标查询请使用 [umeng-cli-uapp-core-index](../umeng-cli-uapp-core-index/SKILL.md)；渠道/版本请使用 [umeng-cli-uapp-channel-version](../umeng-cli-uapp-channel-version/SKILL.md)；留存请使用 [umeng-cli-uapp-retention](../umeng-cli-uapp-retention/SKILL.md)；事件请使用 [umeng-cli-uapp-event](../umeng-cli-uapp-event/SKILL.md)；APM 请使用 [umeng-cli-uapm](../umeng-cli-uapm/SKILL.md)。
