## U-APM 崩溃诊断技能


查询友盟应用性能监控（U-APM）的崩溃详情数据、自定义异常上报与卡顿日志，包括 case 排名、日志实例列表、完整日志详情（设备 + 行为 + 地理位置）、原始与解析后日志下载，共 **5 个只读查询接口**。

> **趋势查询**不在本 Skill 范围内 — 请使用 `umeng-cli-uapm` 技能查询稳定性趋势（GetTodayStatTrend / GetStatTrend 等 8 个 OpenAPI 接口）。


## 鉴权方式

- **authType**: `aliyun-aksk`（ACS3-HMAC-SHA256 V3 签名，友盟 OpenAPI 标准鉴权）
- **baseUrl**: `https://apm.openapi.umeng.com`
- **API Version**: `2026-05-21`
- AK/SK 由 `umeng-cli login` 自动获取和注入，无需手动配置

### 登录状态检查

```bash
umeng-cli whoami
```

### 登录要求

当接口返回未登录或登录态过期时，需执行 `umeng-cli login --no-qr` 进行登录。

**AI Agent 执行登录的正确方式：**

> `umeng-cli login --no-qr` 会在输出登录链接后**阻塞等待用户在浏览器中完成登录**，因此 AI Agent 应以**后台模式**（`is_background: true`）运行此命令，立即拿到登录链接展示给用户，无需等待命令结束。命令会在用户完成登录后自动退出并保存凭证。

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

### 获取 dataSourceId（appKey）

U-APM 所有接口均以 `dataSourceId` 作为应用维度标识，其值等同于友盟统计后台中的 **appKey**。

> **⚠️ AI Agent 必须在此暂停并向用户索取 appKey（即 dataSourceId）：**
> 1. 询问用户："请提供要查询的应用 appKey（即 dataSourceId）"
> 2. 若用户不知道，引导其前往 https://www.umeng.com/ → 应用管理后台 → 「应用信息」或「集成设置」中复制
> 3. **未获得有效 appKey 前，禁止执行任何业务 API 调用**

## 通用调用格式

```bash
umeng-cli call '{
  "name": "apm.<Action>",
  "api": {
    "method": "GET",
    "baseUrl": "https://apm.openapi.umeng.com",
    "endpoint": "<pathname>",
    "authType": "aliyun-aksk",
    "version": "2026-05-21"
  }
}' '<参数JSON>'
```

- 本 Skill 的 5 个接口均为 `GET` 方法
- 参数 JSON 中所有字段均为必填（除非特别标注）

## 关键概念

本 Skill 涉及 3 个 ID + 2 个文件资源（rawLog、parsedLog），调用前请先理清它们的层级与边界，避免传错参数。

### errorId vs logId vs rawLog vs parsedLog

| 概念 | 来源接口 | 含义 | 粒度 | 典型样例 |
|------|---------|------|------|----------|
| `errorId`（崩溃 case ID） | `SearchErrorIds` 返回的 `id` | **崩溃聚类指纹**：同一异常类 + 同一堆栈摘要会聚成一个 case | 一类崩溃 | `10001234056789` |
| `logId`（日志实例 ID） | `SearchErrorLogIds` 返回的 `logId` | **单次崩溃上报记录**：每个真实用户的每次崩溃发生都会产生一条 logId | 一次上报 | `6a0aaa110cf2c98000000001` |
| `rawLog`（原始日志 zip） | `GetRawLogSearch` 返回的 `Data` URL | **OSS 签名下载链接**：含完整堆栈、日志上下文、用户行为流水的 zip 包（未符号化） | 单次崩溃的原始文件 | `.../UAPM_原始日志_xxx.zip?Signature=...` |
| `parsedLog`（解析后日志 zip） | `GetParsedLogSearch` 返回的 `Data` URL | **OSS 签名下载链接**：堆栈已符号化还原为源码符号，可直接阅读的 zip 包 | 单次崩溃的解析文件 | `.../UAPM_解析日志_xxx.zip?Signature=...` |

### 四者层级关系

```
errorId（一类崩溃）
  ├── logId 1（用户 A 周一上报）
  │     ├── GetErrorLogDetail   → 设备信息 + 行为轨迹 + 地理位置（结构化）
  │     ├── GetRawLogSearch     → zip 原始日志（完整文本，未符号化）
  │     └── GetParsedLogSearch  → zip 解析后日志（已符号化，可读堆栈）
  ├── logId 2（用户 B 周一上报）
  ├── logId 3（用户 C 周二上报）
  └── ...
```

### 关键差异说明

- **不要把 `errorId` 当 `logId` 传**：`GetErrorLogDetail` / `GetRawLogSearch` 同时需要 `ErrorId` + `LogId` 两个参数，两者**都要传，不可省略其一**。
- **errorId 只能从 `SearchErrorIds` 获取**：直接根据异常类名/堆栈猜的 ID 一定无效。
- **logId 与 errorId 一对多**：一个 case 下可能有数千条 logId，`SearchErrorLogIds` 默认只取近期；要批量分析建议 `PageSize=min(happenTimes, 20)`。
- **rawLog 与 GetErrorLogDetail 互补，不可替代**：
  - `GetErrorLogDetail` 返回**结构化字段**，适合自动分析（如统计设备分布）
  - `GetRawLogSearch` 返回**原始 zip**，适合人工/AI 阅读完整堆栈与日志上下文
  - 两者使用相同的 `ErrorId + LogId`，可同时调用

### ErrorType 与 CrashType 取值组合

5 个接口共用同一组 `ErrorType` + `CrashType` 枚举，可组合关系如下：

| ErrorType | CrashType | 适用场景 |
|-----------|-----------|----------|
| `crash` | `JAVA` / `NATIVE` / 不传 | 进程崩溃（Java 异常 / Native 段错误） |
| `anr` | `anr` | 主线程无响应 |
| `oom` | `JAVA` / `NATIVE` / 不传 | 内存溢出 |
| `exception` | `CUSTOM` | **自定义异常上报**：应用主动 catch 后通过 SDK 上报的非崩溃异常，不会导致进程退出 |
| `pa` | `""`（空字符串，必传） | **卡顿日志**：UI 卡顿 / 页面卡顿 / 滑动卡顿（jank）个案 |

> **绑定规则**：
> - `ErrorType=exception` 必须搭配 `CrashType=CUSTOM`，反之亦然；不可与其他 `CrashType` 值组合，否则返回空数据。
> - `ErrorType=pa` 必须显式传 `CrashType=""`（空字符串）；不可省略该字段，也不可传其他值。
>
> **CrashType 传参注意**：默认禁止传空字符串；**唯一例外**：`ErrorType=pa` 时必须传 `CrashType=""`。其他场景不限定时直接省略该字段。

### 交互阻断规则：日志类型确认优先于链路执行

下载类接口（`GetRawLogSearch` / `GetParsedLogSearch`）涉及两种互不兼容的日志格式，调用前必须确保类型已明确：

| 场景 | AI Agent 行为 |
|------|--------------|
| 用户**已明确**类型（如"下载解析后日志"） | 直接调用对应接口，无需问询 |
| 用户**未明确**类型（如"下载日志""拿日志""导出崩溃日志"） | **禁止直接调用**，必须先问询「解析后（已符号化，堆栈可读）」还是「原始（未符号化）」，获得答复后再调用 |

> **触发词覆盖**：下载 / 查看 / 导出 / 拿 / 获取 — 任何含"获取日志文件"意图的表述均适用此规则。
> **禁止**：不可因前序步骤（SearchErrorIds → SearchErrorLogIds → GetErrorLogDetail）的顺序执行惯性而跳过此确认。

## 接口路由表

### 查询类（3 个，返回 JSON 数据）

| Action | Endpoint | 关键入参 | 输出形态 |
|--------|----------|---------|----------|
| `SearchErrorIds` | `/stat/SearchErrorIds` | DataSourceId + ErrorType + 时间范围 | 崩溃 case 列表（含 `id`=errorId） |
| `SearchErrorLogIds` | `/stat/SearchErrorLogIds` | + ErrorId | 日志实例列表（含 `logId`） |
| `GetErrorLogDetail` | `/stat/GetErrorLogDetail` | + ErrorId + LogId | 单条日志结构化详情（设备/行为/位置） |

### 下载类（2 个，返回签名 URL，需 curl 下载 + unzip 解压）

| Action | Endpoint | 关键入参 | 输出形态 |
|--------|----------|---------|----------|
| `GetRawLogSearch` | `/stat/GetRawLogSearch` | + ErrorId + LogId | **原始（未符号化）**日志 OSS 签名 zip 下载 URL（15 天有效期） |
| `GetParsedLogSearch` | `/stat/GetParsedLogSearch` | + ErrorId + LogId | **解析后（已符号化）**日志 OSS 签名 zip 下载 URL（15 天有效期） |

> ⛔ **下载类接口 — 类型确认规则**
>
> `GetRawLogSearch`（原始 = 未符号化）vs `GetParsedLogSearch`（解析后 = 已符号化、堆栈可读）。
>
> 当用户以自然语言要求"下载/查看/导出/拿崩溃日志"但**未指明类型**时，AI Agent **必须先问询**用户选择「解析后」还是「原始」日志，获得明确答复后再调用对应接口。**禁止因前序步骤的顺序执行惯性而跳过此确认。**

---

## 操作

### 1. 获取崩溃 case 列表 (SearchErrorIds)

获取按崩溃次数/影响用户排序的崩溃 case 列表，用于发现 Top 崩溃问题。

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| DataSourceId | string | 是 | 数据源 ID（即 appKey） |
| ErrorType | string | 是 | 错误类型：`crash` / `anr` / `oom` / `exception` / `pa`（取值与组合规则见上文「关键概念 → ErrorType 与 CrashType 取值组合」） |
| CrashType | string | 否 | 崩溃类型：`JAVA` / `NATIVE` / `anr` / `CUSTOM` / `""`（默认不传=不限，禁止传空字符串；**例外**：`ErrorType=pa` 时必须传 `""`；详细绑定规则见上文） |
| DateType | string | 是 | 时间范围：`today` / `lastHour` / `last48Hours` / `last7Days` / `last15Days` |
| StartDay | string | 是 | 开始时间，格式 `yyyyMMdd HHmmss`（如 `20260506 000000`） |
| EndDay | string | 是 | 结束时间，格式 `yyyyMMdd HHmmss`（如 `20260520 235959`） |
| PageSize | integer | 是 | 返回条数（如 10） |
| OrderBy | string | 否 | 排序字段：`happenTimes`（崩溃次数） / `affectUsers`（影响用户数），默认 happenTimes |
| Order | string | 否 | 排序方向：`desc`（降序） / `asc`（升序），默认 desc |
| AppVersion | array | 否 | 版本过滤，JSON 数组格式如 `["1.0","2.0"]`，不传=不限 |

**调用示例：**

```bash
umeng-cli call '{
  "name": "apm.SearchErrorIds",
  "api": {
    "method": "GET",
    "baseUrl": "https://apm.openapi.umeng.com",
    "endpoint": "/stat/SearchErrorIds",
    "authType": "aliyun-aksk",
    "version": "2026-05-21"
  }
}' '{"DataSourceId":"<your_appkey>","ErrorType":"crash","CrashType":"JAVA","DateType":"last7Days","StartDay":"20260514 000000","EndDay":"20260521 235959","PageSize":10,"OrderBy":"happenTimes","Order":"desc"}'
```

**返回格式：**

```json
{
  "Code": 200,
  "HttpCode": 200,
  "Success": true,
  "traceId": "2167050717793636763...",
  "Data": "[{id=10001234056789, summary=java.lang.NullPointerException\nAttempt to invoke virtual method..., happenTimes=1520, affectUsers=1103, crashType=JAVA, errorType=crash, os=android, appVersion=2.1.0 - 20100(20100), firstHappenVersion=2.0.0, firstHappenTime=Thu Jul 15 15:01:29 CST 2021, lastHappenTime=Thu May 21 19:31:30 CST 2026, status=0, summaryMd5=c0944ff4..., hasOom=false, processors=[1, 10, 2], aggregationKey=未知, aggregationName=null}]"
}
```

> **注意**：`Data` 字段为 **Java toString 字符串**（非标准 JSON），AI Agent 需自行解析提取字段值。

**返回字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `Code` | integer | 状态码（200 成功） |
| `Data` | string | 业务数据（toString 字符串，需解析） |
| `HttpCode` | integer | HTTP 状态码 |
| `Success` | boolean | 是否成功 |
| `traceId` | string | 请求追踪 ID |

**Data 内业务字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 崩溃 case ID（即 errorId，传入下一步） |
| `summary` | string | 崩溃摘要（异常类名 + 消息 + 顶部堆栈） |
| `happenTimes` | long | 崩溃次数 |
| `affectUsers` | long | 影响用户数 |
| `crashType` | string | 崩溃类型 |
| `errorType` | string | 错误类型 |
| `os` | string | 操作系统（android/ios） |
| `appVersion` | string | 最新发生版本 |
| `firstHappenVersion` | string | 首次发生版本 |
| `firstHappenTime` | string | 首次发生时间（Java Date 字符串，如 `Thu Jul 15 15:01:29 CST 2021`） |
| `lastHappenTime` | string | 最后发生时间（Java Date 字符串） |
| `status` | integer | 状态：0=未修复 1=处理中 2=已忽略 3=已修复 |
| `summaryMd5` | string | 摘要 MD5 |
| `hasOom` | boolean/null | 是否 OOM |
| `processors` | array | 处理人 ID 列表 |
| `aggregationKey` | string | 聚合键 |
| `aggregationName` | string/null | 聚合名称 |

---

### 2. 获取日志实例列表 (SearchErrorLogIds)

获取某个崩溃 case 下的具体日志实例列表，用于选择要查看的日志。

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| DataSourceId | string | 是 | 数据源 ID |
| ErrorType | string | 是 | 错误类型（取值同 SearchErrorIds） |
| CrashType | string | 否 | 崩溃类型（取值同 SearchErrorIds） |
| DateType | string | 是 | 时间范围 |
| StartDay | string | 是 | 开始时间 |
| EndDay | string | 是 | 结束时间 |
| ErrorId | string | 是 | 崩溃 case ID（来自 SearchErrorIds 返回的 `id`） |
| PageSize | integer | 是 | 返回条数（建议取 min(happenTimes, 20)，确保拉到全部日志） |
| AppVersion | array | 否 | 版本过滤，JSON 数组格式如 `["1.0"]`，不传=不限 |

**调用示例：**

```bash
umeng-cli call '{
  "name": "apm.SearchErrorLogIds",
  "api": {
    "method": "GET",
    "baseUrl": "https://apm.openapi.umeng.com",
    "endpoint": "/stat/SearchErrorLogIds",
    "authType": "aliyun-aksk",
    "version": "2026-05-21"
  }
}' '{"DataSourceId":"<your_appkey>","ErrorType":"crash","CrashType":"JAVA","DateType":"last7Days","StartDay":"20260514 000000","EndDay":"20260521 235959","ErrorId":"10001234056789","PageSize":10}'
```

**返回格式：**

```json
{
  "Code": "200",
  "HttpCode": 200,
  "Success": true,
  "traceId": "0b52035217793642417...",
  "Data": "[{logId=6a0aaa110cf2c98000000001, sourceLogId=, serverTime=2026-05-20 23:57:47, errorId=10001234056789, isOom=null}]"
}
```

**返回字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `logId` | string | 日志实例 ID（传入下一步 GetErrorLogDetail） |
| `sourceLogId` | string | 原始日志 ID（可能为空字符串） |
| `serverTime` | string | 服务端接收时间（`yyyy-MM-dd HH:mm:ss`） |
| `errorId` | string | 所属崩溃 case ID |
| `isOom` | boolean/null | 是否 OOM |

---

### 3. 获取日志详情 (GetErrorLogDetail)

获取单条崩溃日志的完整设备信息、用户行为轨迹、地理位置等。

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| DataSourceId | string | 是 | 数据源 ID |
| ErrorType | string | 是 | 错误类型（取值同 SearchErrorIds） |
| CrashType | string | 否 | 崩溃类型（取值同 SearchErrorIds） |
| DateType | string | 是 | 时间范围 |
| StartDay | string | 是 | 开始时间 |
| EndDay | string | 是 | 结束时间 |
| ErrorId | string | 是 | 崩溃 case ID（来自 SearchErrorIds 返回的 `id`） |
| LogId | string | 是 | 日志实例 ID（来自 SearchErrorLogIds 返回的 `logId`） |
| PageSize | integer | 是 | 固定传 10 |

**调用示例：**

```bash
umeng-cli call '{
  "name": "apm.GetErrorLogDetail",
  "api": {
    "method": "GET",
    "baseUrl": "https://apm.openapi.umeng.com",
    "endpoint": "/stat/GetErrorLogDetail",
    "authType": "aliyun-aksk",
    "version": "2026-05-21"
  }
}' '{"DataSourceId":"<your_appkey>","ErrorType":"crash","CrashType":"JAVA","DateType":"last15Days","StartDay":"20260506 000000","EndDay":"20260521 235959","ErrorId":"10001234056789","LogId":"6a0aaa110cf2c98000000001","PageSize":10}'
```

**返回格式（节选核心字段）：**

```json
{
  "Code": 200,
  "HttpCode": 200,
  "Success": true,
  "traceId": "212cfb8617793646095...",
  "Data": "{country=中国, appVersion=2.1.0, deviceType=OPPO, deviceVersion=PLP110, os=android, osVersion=16, arch=arm64-v8a, mem=37.29, disk=81.05, battery=78.0, access=wifi, duration=1000, clientTime=2026-05-20 23:56:34, serverTime=2026-05-20 23:56:34, sourceLogId=6a0bbb22e4b077a700000001, stackMd5=abcdef1234567890..., channel=App Store, sdkVersion=2.0.7, appPackageName=com.example.app, region=广东省, city=湛江市, carrier=中国联通, jailbroken=false, temp=296.0, sessionId=A1B2C3D4..., pagesBehavior=[{...}], customDimensions=[{...}], logId=6a0aaa110cf2c98000000001, crashType=4, appKey=<your_appkey>, anrInfo=null, memInfo=MemTotal:...}"
}
```

**返回字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `logId` | string | 日志 ID |
| `crashType` | integer | 崩溃类型（4=Java Crash） |
| `deviceType` | string | 设备品牌 |
| `deviceVersion` | string | 设备型号 |
| `os` | string | 操作系统 |
| `osVersion` | string | OS 版本 |
| `arch` | string | CPU 架构 |
| `mem` | string | 内存使用率(%) |
| `disk` | string | 磁盘使用率(%) |
| `battery` | string | 电量(%) |
| `access` | string | 网络类型 |
| `duration` | long | 使用时长(ms) |
| `clientTime` | string | 客户端时间 |
| `serverTime` | string | 服务端时间 |
| `sourceLogId` | string | 原始日志 ID（可能为空） |
| `stackMd5` | string | 堆栈 MD5 |
| `channel` | string | 渠道 |
| `sdkVersion` | string | SDK 版本号 |
| `appPackageName` | string | 应用包名 |
| `jailbroken` | boolean | 是否越狱/root |
| `temp` | float/null | 设备温度 |
| `customDimensions` | array/null | 自定义维度 |
| `pagesBehavior` | string | 页面行为轨迹（JSON 字符串，需解析） |
| `country/region/city` | string | 地理位置 |
| `carrier` | string | 运营商 |
| `anrInfo` | string/null | ANR 信息（仅 ANR 类型有值） |
| `memInfo` | string | 完整内存信息 |
| `sessionId` | string | 会话 ID |
| `puid` | string | 用户 ID |
| `custom` | string | 自定义字段 |

---

### 4. 获取原始日志下载 URL (GetRawLogSearch)

获取原始日志的 OSS 签名 zip 下载 URL。下载后为 zip 压缩包，需解压获取 .log 文件。

**参数说明：**

参数与 GetErrorLogDetail 相同（DataSourceId + ErrorType + CrashType + DateType + StartDay + EndDay + ErrorId + LogId + PageSize）。

**调用示例：**

```bash
umeng-cli call '{
  "name": "apm.GetRawLogSearch",
  "api": {
    "method": "GET",
    "baseUrl": "https://apm.openapi.umeng.com",
    "endpoint": "/stat/GetRawLogSearch",
    "authType": "aliyun-aksk",
    "version": "2026-05-21"
  }
}' '{"DataSourceId":"<your_appkey>","ErrorType":"crash","CrashType":"JAVA","DateType":"last15Days","StartDay":"20260506 000000","EndDay":"20260521 235959","ErrorId":"10001234056789","LogId":"6a0aaa110cf2c98000000001","PageSize":10}'
```

**返回格式：**

```json
{
  "Code": 200,
  "HttpCode": 200,
  "Success": true,
  "traceId": "0bb6063117793646985...",
  "Data": "https://<bucket>.oss-cn-<region>.aliyuncs.com/ExportFile/rawLogSearch/.../UAPM_原始日志_20260521152208.zip?Expires=...&Signature=..."
}
```

**下载与解压（默认行为，AI Agent 应自动执行）：**

```bash
## 下载 zip 包
curl -o raw_log.zip "<data字段返回的URL>"

## 解压（跨平台）
## macOS / Linux:
unzip raw_log.zip -d ./raw_logs/
## Windows (PowerShell):
## Expand-Archive -Path raw_log.zip -DestinationPath ./raw_logs/
```

> **完成后必须**：主动告知用户解压后的文件路径，并提示是否打开查看。示例输出：“原始日志已下载并解压到 `./raw_logs/source_xxx.log`，是否需要打开查看？”

**错误码说明：**

| code | 含义 | 处理方式 |
|------|------|----------|
| 200 | 成功 | `Data` 为 zip 下载 URL |
| 310 | 原始日志保留期限为15天，查询起始时间超出该期限 | 调整 StartDay 到 15 天内 |
| 311 | 该应用原始日志下载功能已关闭 | 联系应用管理员开启 |
| 400 | 应用不存在（或 DataSourceId 错误） | 检查 DataSourceId 是否正确 |
| -1 | 日期格式不正确 | 确保格式为 `yyyyMMdd HHmmss` |

---

### 5. 获取解析后日志下载 URL (GetParsedLogSearch)

获取**解析后（已符号化）**日志的 OSS 签名 zip 下载 URL。下载后为 zip 压缩包，需解压获取 .log 文件。

> **与 GetRawLogSearch 的语义差异**：
> - `GetParsedLogSearch` 返回**解析后日志**：堆栈已符号化还原为源码类名/方法名/行号，人工或 AI 可直接阅读定位问题。
> - `GetRawLogSearch` 返回**原始日志**：未符号化的原始上报内容，需自行结合符号表还原。
> - 两者入参、调用格式、返回结构完全一致，仅 `endpoint` 与 `name` 不同。
>
> **交互约定**：遵循上文「关键概念 → 交互阻断规则」—— 用户未明确类型时**禁止直接调用**，必须先问询并获得答复。用户已明确类型则直接调用。

**参数说明：**

参数与 GetRawLogSearch 完全相同（DataSourceId + ErrorType + CrashType + DateType + StartDay + EndDay + ErrorId + LogId + PageSize）。

**调用示例：**

```bash
umeng-cli call '{
  "name": "apm.GetParsedLogSearch",
  "api": {
    "method": "GET",
    "baseUrl": "https://apm.openapi.umeng.com",
    "endpoint": "/stat/GetParsedLogSearch",
    "authType": "aliyun-aksk",
    "version": "2026-05-21"
  }
}' '{"DataSourceId":"<your_appkey>","ErrorType":"crash","CrashType":"JAVA","DateType":"last15Days","StartDay":"20260506 000000","EndDay":"20260521 235959","ErrorId":"10001234056789","LogId":"6a0aaa110cf2c98000000001","PageSize":10}'
```

**返回格式：**

```json
{
  "Code": 200,
  "HttpCode": 200,
  "Success": true,
  "traceId": "0bb6063117793646985...",
  "Data": "https://<bucket>.oss-cn-<region>.aliyuncs.com/ExportFile/parsedLogSearch/.../UAPM_解析日志_20260521152208.zip?Expires=...&Signature=..."
}
```

**下载与解压（默认行为，AI Agent 应自动执行）：**

```bash
## 下载 zip 包
curl -o parsed_log.zip "<data字段返回的URL>"

## 解压（跨平台）
## macOS / Linux:
unzip parsed_log.zip -d ./parsed_logs/
## Windows (PowerShell):
## Expand-Archive -Path parsed_log.zip -DestinationPath ./parsed_logs/
```

> **完成后必须**：主动告知用户解压后的文件路径，并提示是否打开查看。示例输出：“解析后日志已下载并解压到 `./parsed_logs/parsed_xxx.log`，是否需要打开查看？”

**错误码说明：**

| code | 含义 | 处理方式 |
|------|------|----------|
| 200 | 成功 | `Data` 为 zip 下载 URL |
| 310 | 解析后日志保留期限为15天，查询起始时间超出该期限 | 调整 StartDay 到 15 天内 |
| 311 | 该应用日志下载功能已关闭 | 联系应用管理员开启 |
| 400 | 应用不存在（或 DataSourceId 错误） | 检查 DataSourceId 是否正确 |
| -1 | 日期格式不正确 | 确保格式为 `yyyyMMdd HHmmss` |

---

## 调用链依赖关系

```
SearchErrorIds → id ────────→ SearchErrorLogIds.ErrorId
SearchErrorLogIds → logId ───→ GetErrorLogDetail.LogId
SearchErrorLogIds → logId ───→ GetRawLogSearch.LogId
SearchErrorLogIds → logId ───→ GetParsedLogSearch.LogId
SearchErrorIds → id ────────→ GetErrorLogDetail.ErrorId
SearchErrorIds → id ────────→ GetRawLogSearch.ErrorId
SearchErrorIds → id ────────→ GetParsedLogSearch.ErrorId
```

> 每一步的 `DataSourceId`、`ErrorType`、`CrashType`、`DateType`、`StartDay`、`EndDay` 保持一致即可。

## 典型工作流

> **前提**：以下场景均要求用户已提供 appKey（即 `dataSourceId`）。若尚未获取，请先回到上文「获取 dataSourceId（appKey）」段落向用户索取。

### 场景 1：查看 Top 崩溃并下载日志详情

```
1. SearchErrorIds (PageSize=10)
   → 展示 case 列表，用户选择感兴趣的 case（提取 id 作为 ErrorId）
2. SearchErrorLogIds (ErrorId=<上一步的id>, PageSize=min(happenTimes,20))
   → 展示日志实例列表，用户选择或自动取前 N 条（提取 LogId）
3. GetErrorLogDetail (ErrorId + LogId)
   → 展示完整设备信息、行为轨迹、地理位置
⛔ 若用户要下载日志且未指明类型 → 必须先问询「解析后 / 原始」→ 获得答复后再执行第 4 步
4. (可选) 下载日志：调用 GetRawLogSearch（原始）或 GetParsedLogSearch（解析后）(ErrorId + LogId)
   → 获取 zip URL → curl 下载 → 自动解压 → 告知文件路径
```

### 场景 2：端到端（趋势异常 → 定位崩溃 → 下载日志）

```
1. 用户："昨天崩溃率怎么样？" → 使用 umeng-cli-uapm 的 GetStatTrend 查询趋势
2. 发现崩溃率异常 → "崩溃最多的 case 是什么？" → 本技能 SearchErrorIds
3. 展示列表 → 用户："下前3条日志看看" → SearchErrorLogIds → GetErrorLogDetail ×3
4. 输出结构化日志 → 用户可接入 AI Coding 工具分析修复
⛔ 若用户要下载日志且未指明类型 → 必须先问询「解析后 / 原始」→ 获得答复后再执行第 5 步
5. (可选) 下载日志：调用 GetRawLogSearch（原始）或 GetParsedLogSearch（解析后）(ErrorId + LogId)
   → 获取 zip URL → curl 下载 → 自动解压 → 告知文件路径
```

### 场景 3：查看 Top 卡顿与卡顿日志详情

```
1. SearchErrorIds (ErrorType="pa", CrashType="", PageSize=10)
   → 展示卡顿 case 列表，用户选择感兴趣的 case（提取 id 作为 ErrorId）
2. SearchErrorLogIds (ErrorType="pa", CrashType="", ErrorId=<上一步的id>, PageSize=min(happenTimes,20))
   → 展示日志实例列表，用户选择或自动取前 N 条（提取 LogId）
3. GetErrorLogDetail (ErrorType="pa", CrashType="", ErrorId + LogId)
   → 展示完整设备信息、行为轨迹、地理位置
⛔ 若用户要下载日志且未指明类型 → 必须先问询「解析后 / 原始」→ 获得答复后再执行第 4 步
4. (可选) 下载日志：调用 GetRawLogSearch（原始）或 GetParsedLogSearch（解析后）(ErrorType="pa", CrashType="", ErrorId + LogId)
   → 获取 zip URL → curl 下载 → 自动解压 → 告知文件路径
```

> **关键提醒**：本场景 4 步全部必须显式传 `CrashType=""`；不可省略，否则会被服务端按崩溃路径处理返回空数据。

## 边界条件与错误处理

- **未登录 / 登录态过期**：响应码非 200 或提示 `unauthorized`，执行 `umeng-cli login --no-qr`（AI Agent 以后台模式运行并将链接展示给用户）
- **U-APM 免费版功能受限**：响应 `code=403` 且 `msg` 含「当前应用使用的是U-APM 免费版，不支持此功能，请升级至专业版后使用」时，**立即停止当前接口重试**，向用户输出：
  > 该接口需开通 U-APM 专业版后才能使用。请前往升级页面：https://www.umeng.com/market?tab=apm 完成开通后再次发起查询。
- **应用未授权**：返回 code=400 "应用不存在"，需到友盟后台为该应用添加 U-APM 接口权限
- **时间格式错误**：返回 code=-1，确保 StartDay/EndDay 格式为 `yyyyMMdd HHmmss`（日期与时间之间有空格）
- **日志过期（原始/解析后）**：返回 code=310，OSS 文件仅保留 15 天
- **日志下载功能关闭（原始/解析后）**：返回 code=311，需应用管理员在后台开启
- **data 为空数组**：代表该时段无崩溃上报，非错误

## 注意事项

- 本 Skill **仅限只读查询**，不包含符号表上传、告警配置等写入操作
- `DataSourceId` 即友盟统计后台的 **appKey**，到 https://www.umeng.com/ 后台查询
- 时间字段 `firstHappenTime` / `lastHappenTime` 返回 **Java Date 字符串**（如 `Thu Jul 15 15:01:29 CST 2021`），非标准格式，需解析提取
- `pagesBehavior` 字段为 **JSON 字符串**（非对象），使用时需先 `JSON.parse` / `json.loads` 解析，解析后结构如：
  ```json
  [{"start_time":"1779292577830","page_name":"com.example.app.MainActivity","page_lifecycle":"onStarted"}]
  ```
- `GetRawLogSearch`（原始/未符号化）与 `GetParsedLogSearch`（解析后/已符号化）均返回的是 **zip 压缩包** URL，下载后需 `unzip` 解压；两者参数完全一致，仅 `endpoint` 不同。当用户未指明下载类型时，AI Agent 必须先问询「解析后 / 原始」再调用。
- 所有接口均为 `GET` 方法
- 与 `umeng-cli-uapm` 的边界：本 Skill 专注崩溃个案诊断（case 列表 + 日志下载），聚合统计类需求（崩溃率趋势、启动性能、网络性能）请使用 `umeng-cli-uapm`
