# WorkBuddy 对话上下文导出（workbuddy.md）

> **用途**：本文件用于核验本项目是否符合「麦当劳程序员创意开发大赛 · WorkBuddy 专项奖励」的联动条件。
> **核验要点**：① 项目由作者在**腾讯 WorkBuddy** 中真实开发；② 开发过程中 WorkBuddy **真实调用了麦当劳 MCP**（`mcd-mcp`）；③ 全程对话上下文、工具调用与产出文件均可追溯。
> **隐私处理**：已隐去 MCP Token、本机路径中的用户名等敏感信息；不含任何真实凭证。

---

## 0. 基本信息

| 项 | 内容 |
|---|---|
| 项目名称 | 麦当劳「真」随心配（McDonald's Make-It-Your-Way） |
| 开发者 | 万正浩（GitHub: [@Alex-star-arch](https://github.com/Alex-star-arch)） |
| 开发工具 | **腾讯 WorkBuddy 桌面版 · Agent 模式**（全程，无其他 IDE 参与编码） |
| 开发周期 | 2026-10-20 12:11 → 2026-10-23 16:00（约 4 天，含 3 次大版本重构） |
| 使用的麦当劳 MCP | `mcd-mcp`（Streamable HTTP，`https://mcp.mcd.cn`），35 个工具可访问，实际调用 4 个 |
| 项目仓库 | `https://github.com/Alex-star-arch/{{REPO_NAME}}`（公开） |

---

## 1. WorkBuddy 能力使用清单

| WorkBuddy 能力 | 在本项目中的实际用途 | 可核验痕迹 |
|---|---|---|
| **Agent 模式（自主多轮执行）** | 从需求到交付全自动推进：读需求 → 查代码 → 改文件 → 起服务 → 截图自检 → 汇报 | 本文 §2 时间线；`screenshots/` 逐轮产物 |
| **MCP 连接器（mcd-mcp）** | 真实调用 `query-nearby-stores` / `query-meals` / `query-meal-detail` / `list-nutrition-foods` | `assets/menu_snapshot_20261023.json`、`assets/meal_detail_raw.json`、`assets/nutrition_raw.json`、`assets/mcp_tools_snapshot.json` |
| **文件读写与编辑** | 重写主前端（`burger_components_3d.html`，约 75 KB）、组件几何库（`components3d.js`）、零依赖服务端（`studio_server.py`） | 上述文件内容与修改时间 |
| **命令执行（Bash / PowerShell）** | 启动本地服务、跑 Python 数据脚本、curl 接口自测、`taskkill` 重启服务 | `scripts/*.py`、服务访问日志 |
| **无头浏览器视觉回归** | 用 headless Chrome 截图逐轮验证桌面 1440 / 平板 820 / 手机 390 三档布局 | `screenshots/01-08*.png` |
| **远程算力调度（SSH）** | 通过 SSH 驱动济南超算 A100 平台，跑 InstantMesh 官方图 → 3D 模型批量实验（历史版本） | `assets/mcd_models_hq/`（A100 产出 GLB） |
| **Skill 机制** | 产出 `SKILL.md`（`agent_created: true`），使项目可在 WorkBuddy 对话内直接使用 | `SKILL.md` 头部元数据 |
| **项目记忆** | 自动沉淀开发日志（踩坑、决策、待办），跨会话续接 | `.workbuddy/memory/2026-10-20 ~ 23.md` |
| **结果交付（present_files）** | 每轮交付自动打开预览页与截图，供用户即时验收 | 每轮对话末尾的交付记录 |

> 说明：本项目**没有使用其他 AI 编程工具**。所有代码均由 WorkBuddy 的 Agent 生成并写入磁盘，作者负责提出需求、判断方案与验收结果。

---

## 2. 开发时间线（对话上下文摘要）

| 时间 | 用户需求（对话轮次） | WorkBuddy 的动作 | 产出 |
|---|---|---|---|
| 10-20 12:11 | 立项：基于麦当劳 MCP 做「自由组合 + 可视化 + 多人参与 + 展示投票」的创意 Skill | 配置并启用 `mcd-mcp` 连接器；`query-nearby-stores` 定位门店 `1450713`；`query-meals` 拉取在售菜单；`list-nutrition-foods` 补营养；写素材库构建脚本 | `assets/materials.json`（119 项 / 10 组）、`assets/mcd_photos/`、零依赖服务 `studio_server.py` |
| 10-20 15:00 | 汉堡改 3D、可搭配材料也要 3D 呈现 | 写 Three.js 引擎与 3D 工作室页；官方图作为贴图 | `assets/burger_studio_3d.html`、`assets/burger3d.js` |
| 10-20 17:00 | 3D 外观与真实差距大 | `query-meal-detail` 拉 14 款汉堡官方组成；WebSearch 核对形态（鱼排方形/鸡排圆形）；重构几何 | 官方组成映射、`official_composition.json` |
| 10-21 全天 | 想要"照片级真实"的 3D 单品 | 通过 SSH 驱动 A100 跑 InstantMesh，官方图 → GLB 批量生成；本地做连通分量碎片裁剪 | `assets/mcd_models*/`（123 个 GLB） |
| 10-22 15:00 | 生菜形态不真实 / 扩展小食组件 / 单品摆放错位 | 重建生菜为平铺褶皱叶盘；新增麦乐鸡/薯条/冰淇淋/派/板烧/虾仁等组件；修 3D 落地与朝向 | `components3d.js` v2（19 种组件） |
| 10-22 16:45 | 汉堡要竖直站立、顶胚朝上；小吃初始姿态不对 | 数值测量包围盒 + 姿态对比截图，确认 `rotation.x = +π/2`；逐款修正 | 单品站立全部正确 |
| 10-22 17:28 | 所有汉堡都要能拆解；再查 MCP 有没有新食材 | 补全 14 款汉堡的拆解映射；再查 MCP 加入玉米杯/烤翅/薯饼/牛奶/怡泉/咖啡/雪碧 | 拆解覆盖 10/10（后扩至 14） |
| 10-23 09:00 | 小吃模型不闭合，重点修怡泉/雪碧/冰淇淋 | 定位为 GLB 单面壳，改走 A100 InstantMesh 重生成（用户明确否决自建模型） | `assets/mcd_models_hq/` 6 件高质量 GLB |
| 10-23 14:20 | 单品改 2D 官方图；支持自由组合套餐 + 价格营养；作品可发布投票 | 重调 MCP 拉最新菜单快照；重写前端为三标签页；重写服务端加发布/投票/预览图 | `burger_components_3d.html`（重写）、`studio_server.py`（重写） |
| 10-23 15:00 | 备份 + 整体美化 + 响应式 + 更名「麦当劳『真』随心配」 | 备份 274 MB；统一设计系统；三档响应式；全站更名 | `_backup/20261023_150040/`、`screenshots/01-08*.png` |
| 10-23 15:31 | **本次**：撰写大赛报名全套文件（重点 WorkBuddy 专项） | 抓取官方规则 → 核对必需文件 → 重写 README / MCP_INTEGRATION / workbuddy.md → 推送 GitHub | 本文件及同批文档 |

---

## 3. 代表性对话上下文（逐字节选）

> 以下为用户原话（节选，未改写），保留真实需求描述与 WorkBuddy 的响应要点。

### 3.1 立项与真实数据接入（10-20）

**用户**：
> 基于麦当劳 MCP 做创意开发：要能自由组合设计个性化汉堡、可视化呈现、多人参与设计、展示与投票。

**WorkBuddy**：
1. 读取已配置的 `mcd-mcp` 连接器 → 确认 35 个工具可用，写入 `assets/mcp_tools_snapshot.json`；
2. 调用 `query-nearby-stores`（`beType=1, searchType=2, city=上海, keyword=人民广场`）→ 得到 `storeCode=1450713`；
3. 调用 `query-meals`（`storeCode=1450713, orderType=1, beType=1`）→ 119 项在售商品；
4. 调用 `list-nutrition-foods` → 营养表；
5. 写 `scripts/build_materials.py` 生成分类素材库，并下载 127 张官方产品图到 `assets/mcd_photos/`；
6. 写零依赖服务端 `scripts/studio_server.py` 与前端页，起服务后交付 `http://localhost:8765`。

### 3.2 视觉真实度迭代（10-22）

**用户**：
> 优化生菜的3D模型（不应该是一个立着的环形，具体请参考现实中的生菜）……扩展汉堡可组合的食材组件范围，将麦乐鸡、薯片、冰淇淋、派等小食也纳入可选组件。修复单品模式中选中汉堡后的展示问题：汉堡当前并非平放在展示台上，而是侧面嵌入展示台内部……调用MCP查询是否还提供了其他汉堡和组件（如板烧等），若有则将其加入可用的汉堡与组件列表中。

**WorkBuddy**：把生菜从 3×Torus（立着的环）改成**平铺褶皱叶盘**（RingGeometry 水平铺开 + 外缘正弦起伏 + 6 片翘起叶尖）；新增 5 种组件与配套纹理；用包围盒数值测量定位"沉入台面"根因（模型中心被强制 `y=0`），改为 `gy = -min.y` 精确贴地；再次调用 MCP 确认板烧鸡腿堡（`1406`）等商品并接入。

### 3.3 姿态纠错（10-22）

**用户**：
> 目前汉堡虽然是竖直站立的但是全是倒着的，没有实现顶胚朝上

**WorkBuddy**：定位到 InstantMesh 的叠层轴约定（顶胚在模型 `-Z` 端），把 `rotation.x` 由 `-π/2` 改为 `+π/2`；再逐款用包围盒三轴尺寸 + 双列对比截图验证，确认薯条/可乐/冰淇淋/苹果片同为 `+90°` 约定。

### 3.4 拒绝自建模型，改走算力平台（10-23）

**用户**：
> 雪碧、咖啡、怡泉、玉米杯、冰淇淋、可乐等这些小食不能用自建模型，用官方图片转3D模型

**用户（补充）**：
> 汉堡使用的是算力平台的转3D方法，可以参考

**WorkBuddy**：放弃程序化回转体方案，改在济南超算 A100 平台（经 SSH 驱动）跑 InstantMesh：清洗官方图 → 保留原始画布留白 → 100 步推理 → 产出 6 件 GLB，接入前端 `HQ_GLB` 白名单，原方案降级为兜底。

### 3.5 形态重构：单品改 2D + 套餐 + 投票（10-23）

**用户**：
> 请将单品模式改为2D展示，所有单品图片统一使用通过调用MCP获取的麦当劳官方图片。单品模式的功能调整为：支持自由组合不同单品生成自定义套餐，并保留各单品以及组合后的价格与营养值显示。单品模式生成的套餐与组件模式生成的汉堡均需支持发布，供其他用户进行投票。

**WorkBuddy**：重调 `query-meals` 取 14:22 最新快照（119 项）→ 重写前端为「套餐搭配 / 汉堡设计 / 作品画廊」三标签页 → 重写服务端加入 `POST /api/designs`（预览图落盘）、`POST /api/vote`（昵称去重，重复 409）→ 用 `?selftest=1` 钩子跑通"客户端合成预览图 + 发布成功"。

### 3.6 体验打磨与更名（10-23）

**用户**：
> 目前核心功能已基本完成。请先备份当前版本，然后对界面进行整体美化：从用户视角出发优化视觉与交互体验，使界面更美观舒适、信息层级清晰、配色与排版协调统一。同时实现响应式适配，确保在手机等移动设备上打开时布局完整、元素不错乱、操作便捷。另外将网站名称统一更改为"麦当劳'真'随心配"，并同步更新页面标题、导航及各处相关文案。

**WorkBuddy**：先做 274 MB 全量备份；统一设计令牌（红 `#DA291C` / 金 `#FFC72C` / 奶油底）；右栏改为「清单 → 合计 → 发布」常驻可见；≤1024px 改为底部标签栏 + 货架抽屉 + 圆形浮动按钮；用 iframe 夹具绕开无头浏览器最小窗口宽度限制，验证真机 390px 布局；全站更名并 `grep` 复核零残留。

---

## 4. 关键工具调用记录（脱敏示例）

以下为 WorkBuddy 实际发起过的调用类型与参数形态（Token 已替换为占位符）：

```jsonc
// ① WorkBuddy 连接器配置（真实写入 ~/.workbuddy/mcp.json，本文档不含真实 Token）
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer ${MCD_MCP_TOKEN}" }
    }
  }
}

// ② 门店定位
mcp__mcd-mcp__query-nearby-stores { beType: 1, searchType: 2, city: "上海", keyword: "人民广场" }
// ⇐ storeCode: "1450713", storeName: "麦当劳上海黄浦华旭国际大厦餐厅"

// ③ 在售菜单
mcp__mcd-mcp__query-meals { storeCode: "1450713", orderType: 1, beType: 1 }
// ⇐ 119 项商品（code / name / image / price / originalPrice）

// ④ 餐品官方组成（14 款汉堡）
mcp__mcd-mcp__query-meal-detail { storeCode: "1450713", orderType: 1, beType: 1, code: "1100" }
// ⇐ modification.values: 巨无霸酱 / 吉士 / 生菜 / 酸黄瓜 / 洋葱粒

// ⑤ 营养
mcp__mcd-mcp__list-nutrition-foods { }
// ⇐ energy / protein / fat / carbohydrate / sodium / calcium

// ⑥ 本地服务与自测（WorkBuddy 命令执行）
Bash: python scripts/studio_server.py --port 8765     （后台运行）
Bash: curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8765/api/materials
Bash: chrome --headless=new --screenshot=... "http://127.0.0.1:8765/?combo=1100,4810,4437"
```

---

## 5. 可核验证据

| 证据 | 位置 | 时间戳 | 证明什么 |
|---|---|---|---|
| 开发日志（4 天） | `.workbuddy/memory/2026-10-20.md` ~ `2026-10-23.md` | 10-20 ~ 10-23 | WorkBuddy 逐轮推进、踩坑与决策的完整记录 |
| MCP 工具清单 | `assets/mcp_tools_snapshot.json` | 10-20 | `mcd-mcp` 真实可访问，35 个工具 |
| 菜单原始快照 | `assets/menu_snapshot_20261023.json` | `fetched_at 2026-10-23 14:22` | 真实调用 `query-meals` 门店 `1450713` |
| 餐品详情原始返回 | `assets/meal_detail_raw.json` | 10-20 13:31（含 traceId） | 真实调用 `query-meal-detail` |
| 营养原始返回 | `assets/nutrition_raw.json` | 10-20 | 真实调用 `list-nutrition-foods` |
| 门店原始返回 | `assets/stores_raw.json` | 10-20 | 真实调用 `query-nearby-stores` |
| 派生素材库 | `assets/materials.json` | `updated_at 2026-10-23 14:25` | 数据链路可复现（119 项 / 63 可单点 / 37 有营养） |
| 官方图 | `assets/mcd_photos/`（127 张） | 10-23 | 图片全部由官方 `menu-img.mcd.cn` 下载 |
| 界面截图 | `screenshots/01-08*.png` | 10-23 15:19 | WorkBuddy 用无头浏览器做的逐轮视觉回归 |
| 版本备份 | `_backup/20261023_150040/` | 10-23 15:00 | 按用户要求先备份再改版 |
| Skill 定义 | `SKILL.md`（`agent_created: true`） | 10-23 | 由 WorkBuddy Agent 生成并可复用 |

> 本文件由 WorkBuddy 在 2026-10-23 的对话中，根据上述真实上下文整理导出。

---

## 6. 与 WorkBuddy 专项奖励要求的对应

| 官方要求 | 本项目情况 | 结论 |
|---|---|---|
| 参赛项目须真实使用腾讯 WorkBuddy 智能体 | 全程在 WorkBuddy Agent 模式下开发，4 天 10+ 轮迭代，代码/文档/截图均由 Agent 产出 | ✅ |
| 提交 `workbuddy.md` 对话上下文文件 | 即本文件，含时间线、逐字对话节选、工具调用记录、证据索引 | ✅ |
| 项目须真实使用麦当劳 MCP 能力 | 调用 4 个查询类 Tool，原始返回已落盘可核验 | ✅ |
| 文件名与格式符合要求 | `workbuddy.md`（小写、根目录、Markdown） | ✅ |

---

## 7. 声明

- 本项目为作者**原创**作品，未抄袭、未盗用他人项目；
- 文中所有对话均为真实发生并已脱敏，**不含任何真实 Token、密钥、账号凭证或他人个人信息**；
- 项目为参赛作品，非麦当劳官方产品；餐品信息、价格与供应状态以麦当劳官方渠道实时结果为准。
