## 友盟U-Web统计SDK集成Skill

## 功能说明

自动指导将友盟U-Web统计SDK集成到HTML/前端项目中，支持同步/异步代码、SPA路由、事件埋点等多种集成模式。

### 核心功能


1. ✅ **前置条件检查** — 确认siteid已获取、页面可访问
2. ✅ **集成模式选择** — 同步代码/异步代码（推荐）/SPA自动PV
3. ✅ **代码部署顺序验证** — _czc声明→_setAccount→_setAutoPageview→统计代码→业务埋点
4. ✅ **事件埋点集成** — _trackEvent/_trackPageview/_setUUid代码模板
5. ✅ **浏览器验证** — Chrome DevTools Network面板验证cnzz请求
6. ✅ **回滚机制** — 文本删除/替换即可回滚

## 前置要求

### 前置准备

1. **注册与创建站点**：在友盟官网注册账号 → 进入U-Web产品 → 点击"添加统计站点" → 填写网站名称、首页URL、域名 → 确认添加
   - ⚠️ **域名必须填写真实域名**，否则可能统计不到数据
2. **获取统计代码**：添加站点后，在【站点列表】→【统计代码】中获取代码片段，其中包含`siteid`（代码中的红色数字即为站点唯一标识）
3. **购买与激活**：U-Web为付费产品，需购买套餐并在订单激活页面进行激活后再集成。详见：https://developer.umeng.com/docs/67963/detail/428407

### 必需条件
- ✅ U-Web siteid（友盟官网添加站点后获取，纯数字）
- ✅ 可编辑的HTML/JS文件
- ✅ 浏览器（含DevTools，用于验证）

### 可选工具
- ⚠️ HTTP服务器（本地验证时需要）
- ⚠️ Node.js（使用Vue/React等现代框架时需要）

### 注意事项
- ⚠️ **IFRAME限制**：弹出窗口或IFRAME内放统计代码将无法统计来路，请确保统计代码部署在主文档中
- ⚠️ **域名一致**：代码部署的页面域名必须与U-Web后台注册的域名一致

## 使用方式

### 基本用法(交互式)

AI Agent引导：确认siteid → 选择集成模式 → 生成代码片段 → 指导插入位置 → 验证

### 集成模式说明

| 模式 | 适用场景 | 特点 |
|------|----------|------|
| **同步代码** | 简单静态页面 | 最简单，但阻塞页面渲染 |
| **异步代码（推荐）** | 生产环境 | 不阻塞渲染，推荐所有项目使用 |
| **SPA自动PV** | Vue/React/Angular | 平台侧开启开关，自动监听路由变化 |
| **SPA手动PV** | 需精细控制的SPA | 在路由回调中手动调用`_trackPageview` |

### 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `siteid` | ✅ | U-Web站点ID（纯数字，友盟官网获取） |
| 集成模式 | ✅ | 同步/异步/SPA自动PV/SPA手动PV |
| 框架类型 | ❌ | Vue/React/原生HTML（影响SPA集成代码） |

## 工作流程

```
步骤1: 🔍 前置检查（siteid格式验证，确认为纯数字）
  ├─ 检测到已有CNZZ/U-Mini HTML5代码 → 引导走迁入流程（见「升级与迁入 U-Web Plus」章节）
  └─ 无旧代码 → 继续
  ↓
步骤2: 📋 模式选择（同步/异步/SPA自动PV/SPA手动PV）
  ↓
步骤3: 📦 代码生成（基于模式+框架生成完整代码片段）
  ↓
步骤4: 📝 代码部署（指导插入位置 + 部署顺序验证）
  ├─ _czc全局变量声明
  ├─ _setAccount（多站点时）
  ├─ _setAutoPageview（需关闭自动PV时）
  ├─ 统计代码引入
  └─ 业务埋点调用
  ↓
步骤5: ✅ 用户确认（展示修改内容，确认无误）
  ↓
步骤6: 🔍 浏览器验证（DevTools Network面板检查cnzz请求）
  ↓
步骤7: 📋 生成集成报告
```

**关键检查点：**
- ✅ **步骤1完成后** — 确认siteid格式正确（纯数字）
- ✅ **步骤3完成后** — 确认代码模板中YOUR_SITEID已替换
- ✅ **步骤4（部署顺序）** — ⚠️ 严格按照声明→配置→统计代码→埋点的顺序
- ✅ **步骤5（确认点）** — 展示完整修改内容，用户确认后继续
- ✅ **步骤6验证时** — Network面板能看到cnzz相关请求且状态码200

## SDK集成内容

### 1. 异步代码集成（推荐）

⚠️ **推荐所有生产环境使用异步代码**，不阻塞页面渲染。

```html
<script>
(function() {
    var el = document.createElement('script');
    el.type = 'text/javascript';
    el.charset = 'utf-8';
    el.async = true;
    var ref = document.getElementsByTagName('script')[0];
    ref.parentNode.insertBefore(el, ref);
    el.src = 'https://w.cnzz.com/c.php?id=YOUR_SITEID&async=1';
})();
</script>
```

**重要**：添加异步代码后必须删除原同步代码，否则统计数据会重复计算。

### 2. 同步代码集成

在页面`</head>`或`</body>`标签前插入：

```html
<script type="text/javascript" src="https://v1.cnzz.com/z_stat.php?id=YOUR_SITEID&web_id=YOUR_SITEID"></script>
```

**注意**：统计全站需在所有页面添加（建议使用模板包含方式），将U-Web代码放在其他统计代码前面。

### 3. 事件埋点（_trackEvent）

```javascript
// 基础用法：分类 + 动作
_czc.push(["_trackEvent", "视频", "播放"]);

// 完整用法：分类 + 动作 + 标签 + 值
_czc.push(["_trackEvent", "首页", "疯狂抢购", "飞天茅台", 1499]);
```

**参数说明：**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `category` | 是 | string | 事件分类，如"视频"、"按钮" |
| `action` | 是 | string | 交互行为，如"播放"、"点击" |
| `label` | 否 | string | 详细描述，最大255字符 |
| `value` | 否 | int | 数值（整数，浮点自动取整） |

**HTML示例**：`<button onclick="window._czc && window._czc.push(['_trackEvent','首页','点击','按钮',1]);">点击</button>`

**约束限制**：
- 事件个数（category × action × label 的乘积）建议不超过 **10,000** 个
- 报表仅展示前 **1,000** 名事件
- String字段最大长度255字符

### 4. 虚拟PV统计（_trackPageview）

适用于AJAX加载、文件下载、SPA路由切换等场景：

```javascript
// 统计文件下载
_czc.push(["_trackPageview", "/download/app-v2.0.exe", "http://www.mysite.com/download/"]);

// 统计AJAX页面
_czc.push(["_trackPageview", "/ajax/content/page2"]);
```

**参数说明：**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `content_url` | 是 | string | 虚拟页面URL，以`/`开头的相对路径 |
| `referer_url` | 否 | string | 自定义来源页URL；不填按母页面来路计算；填空字符串`""`视为直接访问（直接输入网址或书签） |

**注意**：使用`_trackPageview`改写已有页面URL时，需同时关闭自动PV：

```html
<script>
    var _czc = _czc || [];
    _czc.push(["_setAutoPageview", false]);
</script>
<script src="https://v1.cnzz.com/z_stat.php?id=YOUR_SITEID&web_id=YOUR_SITEID"></script>
```

### 5. 多站点绑定（_setAccount）

同一页面向多个siteid上报数据时使用：

```javascript
var _czc = _czc || [];
_czc.push(["_setAccount", SITEID_A]);  // 指定接收API请求的siteid
_czc.push(["_trackEvent", "首页", "点击", "按钮"]); // 只上报给SITEID_A
```

⚠️ **约束**：`_setAccount`必须在其他API和统计代码之前部署。

### 6. 用户标识关联（_setUUid）

将U-Web访客ID与业务系统用户ID关联：

```javascript
// 在用户登录后调用
const userId = 'user_12345'; // 不超过128个字符
_czc.push(['_setUUid', userId]);
```

**适用场景**：登录用户行为分析、跨设备用户识别、用户画像构建

### 7. SPA路由集成

**Vue Router示例：**

```javascript
router.afterEach((to) => {
    window._czc && window._czc.push(["_trackPageview", to.fullPath]);
});
```

**React Router示例：**

```javascript
history.listen((location) => {
    window._czc && window._czc.push(["_trackPageview", location.pathname + location.search]);
});
```

**平台侧自动PV**：U-Web → 设置 → 插件市场 → 单页设置开关（5分钟生效）。

### 8. 延迟事件脚本（delayClick）

确保页面跳转前事件上报完成，避免因页面跳转导致数据丢失。

**适用场景**：`target="_self"` 的外链点击（同窗口跳转），点击后页面立即卸载导致事件上报中断。

**函数签名**：

```javascript
delayClick(e, o, dt, tjcb)
```

| 参数 | 说明 |
|------|------|
| `e` | Event对象 |
| `o` | this（当前元素） |
| `dt` | 延迟时间（毫秒），建议100ms |
| `tjcb` | 回调函数，在其中执行事件上报 |

**完整HTML使用示例**：

```html
<a onclick="delayClick(event, this, 100, function(){
    _czc.push(['_trackEvent', '外链点击', '点击', '合作网站']);
});" href="http://example.com" target="_self">访问合作网站</a>
```

**原理**：拦截链接默认跳转行为，延迟指定毫秒（如100ms），先完成事件上报回调再执行页面跳转。仅适用于`target="_self"`的链接。

> 💡 **建议**：当用户反馈"点击外链事件偶尔不上报"时，优先推荐使用`delayClick`方案。

### 9. Web云配SDK（可选扩展）

```html
<script src="https://s.cnzz.com/remote-config.js?id=YOUR_SITEID"></script>
<script>
window.urc.setDefaultValues({ buttonColor: 'blue', buttonText: '立即体验' });
window.urc.fetch({ active: true, callback: function(data) {
    var color = window.urc.getValue('buttonColor');
    // 应用到页面元素...
}});
</script>
```

| API | 说明 |
|-----|------|
| `window.urc.setDefaultValues(obj)` | 设置本地默认值 |
| `window.urc.fetch({active, callback})` | 获取远程配置（`active:true`立即生效） |
| `window.urc.getValue(key)` | 获取指定key的配置值 |
| `window.urc.active()` | 手动激活最近一次fetch的参数值 |

## 代码部署顺序规范

⚠️ **U-Web SDK对代码部署顺序有严格要求，顺序错误将导致埋点失效！**

正确顺序：
```
1. 全局变量声明 (_czc)
2. _setAccount（如有多站点）
3. _setAutoPageview（如需关闭自动PV）
4. 统计代码引入 (<script src="...z_stat.php...">)
5. 业务埋点调用 (_trackEvent, _trackPageview 等)
```

**完整模板：**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>U-Web 集成模板</title>
  <script>
    // ① 全局变量声明
    var _czc = _czc || [];
    // ② 多站点绑定（可选）
    _czc.push(["_setAccount", "YOUR_SITEID"]);
    // ③ 关闭自动PV（可选，使用_trackPageview时建议关闭）
    // _czc.push(["_setAutoPageview", false]);
    // ④ 自定义用户ID（可选，登录后调用）
    // _czc.push(["_setUUid", "user_123"]);
  </script>
</head>
<body>
  <!-- 页面内容 -->

  <!-- ⑤ 统计代码引入（放在body结束标签前） -->
  <script src="https://v1.cnzz.com/z_stat.php?id=YOUR_SITEID&web_id=YOUR_SITEID"></script>
</body>
</html>
```

## 验证集成正确性

### Network面板检查

在Chrome DevTools → Network中搜索"cnzz"，应能看到：

| 请求 | 说明 |
|------|------|
| `z_stat.php?id=xxx` | 统计代码加载成功 |
| `core.php?web_id=xxx` | 核心追踪逻辑 |
| `stat.htm?id=xxx&...` | PV或事件上报请求，状态码应为200 |

### 上报参数校验

在`stat.htm`请求的Query Parameters中检查：

| 参数 | 说明 |
|------|------|
| `id` | 应为你的siteid |
| `p` | 页面URL（PV统计时） |
| `ei` | URL编码的事件参数（事件统计时），格式为`分类\|动作\|标签\|值\|` |
| `t` | 页面标题 |
| `cnzz_eid` | 访客标识 |
| `umuuid` | Umeng访客标识 |

### 常见问题排查

| 问题 | 排查方向 |
|------|----------|
| 无数据上报 | 检查siteid是否正确、统计代码是否加载成功、Network中是否有cnzz请求 |
| PV双倍计数 | 检查是否同时存在同步和异步代码，或`_setAutoPageview`未正确关闭 |
| 事件不上报 | 检查`_czc`声明是否在统计代码前、`_setAccount`是否绑定正确 |
| SPA路由切换无PV | 确认平台侧单页设置开关已开启，或手动调用`_trackPageview` |

## 升级与迁入 U-Web Plus

如果用户已有 CNZZ 或 U-Mini HTML5 统计代码，需根据不同场景选择对应迁入路径。

### 迁入路径

| 场景 | 步骤 |
|------|------|
| **新客户** | 购买并激活U-Web Plus → 创建站点 → 部署统计代码 |
| **从U-Mini HTML5迁入** | 购买并激活U-Web Plus → 进入【站点迁入】→ **必须先下线旧HTML5代码**（避免重复统计）→ 部署新代码 |
| **从CNZZ迁入** | 购买对应SKU（如CNZZ订单未过期需补差价购买带补差价标识的SKU）→ 在【站点迁入】绑定CNZZ网站 → 自动升级至新SDK |
| **CNZZ + U-Mini HTML5同时使用** | 购买并激活 → 绑定CNZZ和U-Mini HTML5的同一网站 → **下线U-Mini HTML5代码** → 统一迁入完成自动升级 |

⚠️ **重要**：从U-Mini HTML5迁入时，必须先下线旧代码再部署新代码，否则会导致数据重复统计。

📖 详细指南：https://developer.umeng.com/docs/67963/detail/2847339

## 常见问题

### Q1: 无数据上报怎么办？

**A**: 排查顺序：确认siteid正确（纯数字）→ DevTools Network搜索"cnzz" → 检查`z_stat.php`请求是否加载 → 检查`stat.htm`请求是否上报 → 确认域名与后台注册域名一致。

### Q2: PV双倍计数？

**A**: 常见原因：同时存在同步和异步代码（删除其一）；或使用`_trackPageview`但未关闭自动PV（添加`_czc.push(["_setAutoPageview", false])`）。

### Q3: 事件不上报？

**A**: 检查部署顺序：`_czc`声明必须在统计代码之前；多站点时`_setAccount`必须在`_trackEvent`之前；确认`_czc`拼写正确。

### Q4: SPA路由切换无PV？

**A**: 推荐方案：U-Web平台→设置→插件市场→开启单页设置开关（5分钟生效）。手动方案：在路由回调中调用`_czc.push(["_trackPageview", path])`。

### Q5: 同步和异步代码能同时用吗？

**A**: **不能**。同时使用会导致PV双倍计数。选择一种即可，推荐使用异步代码。

### Q6: siteid和appkey有什么区别？

**A**: 
- `siteid`是U-Web网站统计的站点标识（纯数字），在友盟官网添加站点后获取
- `appkey`是友盟移动应用统计的应用标识
- U-Web使用siteid，移动端SDK使用appkey，两者独立

### Q7: 代码部署顺序错误会怎样？

**A**: `_czc`声明在统计代码之后→事件全部丢失；`_setAutoPageview`在统计代码之后→PV双倍计数；`_setAccount`在其他API之后→多站点绑定无效。

### Q8: Web云配不生效？

**A**: 确认`remote-config.js`的id参数正确；确认平台已创建配置项；`fetch({active:true})`立即生效，`active:false`下次打开生效；`getValue()`需在fetch回调执行后调用。

### Q9: 为什么集成前AI Agent会先执行umeng-cli trace？

**A**: 这是Skill调用埋点上报，用于统计Skill实际使用情况：

```bash
umeng-cli trace '{"skill_name":"uweb-analytics-integration"}' >/dev/null 2>&1 || true
```

仅上报「哪个Skill被使用」，**不涉及siteid、不涉及任何工程源码内容**，可放心执行。U-Web使用siteid而非appkey，不需要appkey维度打点。

## 参考资源

### 官方文档
- **U-Web产品文档**: https://developer.umeng.com/docs/67963/cate/67963
- **友盟开发者中心**: https://developer.umeng.com

### UWeb文档（本项目内）
- `UWeb/UWeb-SDK-集成指南.md` | `UWeb/UWeb-SDK-功能梳理.md` | `UWeb/UWeb-文档索引.md`

### 相关Skills
- **统计SDK集成(Android)**: `references/skills/android-analytics-integration.md`
- **统计SDK集成(iOS)**: `references/skills/ios-analytics-integration.md`
- **推送SDK集成**: `references/skills/push-integration.md`

## 技术支持

- 友盟官方文档: https://developer.umeng.com/docs/67963/cate/67963
- U-Web控制台: https://web.umeng.com
