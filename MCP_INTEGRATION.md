# MCP 集成说明 (MCP Integration)

> 本文说明 **麦当劳「真」随心配** 实际调用的麦当劳 MCP Server、Tool、调用流程与业务价值。
> 文中所有数量、门店编码、字段名均来自项目仓库内的真实接口快照，可逐项核对。

---

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| 名称 | `mcd-mcp` |
| 提供方 | 麦当劳中国（MCP 开放平台） |
| 传输协议 | Streamable HTTP |
| 接入地址 | `https://mcp.mcd.cn` |
| 鉴权方式 | 请求头 `Authorization: Bearer <MCP_TOKEN>`（用户在开放平台控制台申请） |
| 本项目可访问工具数 | **35 个**（全量清单见 `assets/mcp_tools_snapshot.json`） |
| 本项目实际调用 | **4 个**（均为只读查询类，见下） |

配置示例见 [`mcp-config.example.json`](./mcp-config.example.json)，**仅使用环境变量占位符**，仓库内不含任何真实 Token：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer ${MCD_MCP_TOKEN}" }
    }
  }
}
```

---

## 2. 实际调用的 Tool

### 2.1 `query-nearby-stores` —— 定位门店

| 项 | 内容 |
|---|---|
| 入参 | `beType=1`（到店自提）、`searchType=2`（关键词检索）、`city="上海"`、`keyword="人民广场"` |
| 返回 | 门店列表：`storeCode` / `storeName` / 地址 / 营业状态 |
| 本项目用途 | 拿到 `storeCode`，作为后续所有餐品查询的**必填前提** |
| 实际结果 | `storeCode = 1450713`，`storeName = 麦当劳上海黄浦华旭国际大厦餐厅`（已写入 `assets/materials.json` 的 `store` 字段） |

> 为什么必须先查门店：麦当劳菜单、价格、售罄状态都是**门店级**的，同一商品在不同门店可能价格不同或不可售。跳过这一步拿到的数据不可信。

### 2.2 `query-meals` —— 拉取真实在售菜单（核心素材来源）

| 项 | 内容 |
|---|---|
| 入参 | `storeCode=1450713`、`orderType=1`（到店自提）、`beType=1` |
| 返回 | 分类树 + 每个商品的 `code` / `name` / `image` / `price` / `originalPrice` |
| 本项目用途 | **唯一商品数据源**：素材库、货架、价格、官方图全部由它派生 |
| 实际结果 | **119 项**商品，落在 9 个分组：汉堡 14 / 炸鸡 8 / 小食 8 / 甜品冰品 9 / 饮品 13 / 麦咖啡 9 / 蘸酱 2 / 整份套餐 51 / 周边 5；其中**可单点 63 项** |
| 落盘文件 | `assets/menu_snapshot_20261023.json`（含 `fetched_at = 2026-10-23 14:22` 抓取时间戳） |

### 2.3 `query-meal-detail` —— 取餐品官方组成

| 项 | 内容 |
|---|---|
| 入参 | `storeCode=1450713`、`orderType=1`、`beType=1`、`code`（如 `1100`） |
| 返回 | `data.rounds[]`（选配轮次，单品为空）、`data.modification.items[].values[]`（**可特调食材**：编码 / 名称 / 默认是否选中）、600px 高清官方图 |
| 本项目用途 | 为 3D「一键载入官方结构」提供**官方食材清单**（14 款汉堡） |
| 实际结果 | 例：`1100 巨无霸` 的 `modification` 返回 `巨无霸酱 / 吉士 / 生菜 / 酸黄瓜 / 洋葱粒`（均 `selectedQuantity=1`），与官方产品描述一致 |

> **诚实边界**：MCP 的 `modification` 只列**可特调食材**，不含肉饼与面包胚；`rounds` 对单品为空，因此它**不提供层叠顺序**。本项目的处理是：
> ① 食材清单取自 `modification`（官方）；
> ② 层叠顺序按麦当劳官方产品页描述 + 汉堡通用结构整理，写入前端 `BURGER_LAYERS`（14 条映射）与 `assets/official_composition.json`；
> ③ 肉饼/鸡排数量按官方产品名补全（如「双层吉士」「不素之霸双层牛堡」）。
> 即：**成分是官方的，顺序是规范化的**，二者在代码与文档中都分开标注，不冒充官方层序。

### 2.4 `list-nutrition-foods` —— 营养数据

| 项 | 内容 |
|---|---|
| 入参 | 无 |
| 返回 | 各餐品的能量(kcal) / 蛋白质 / 脂肪 / 碳水化合物 / 钠 / 钙 |
| 本项目用途 | 单品营养 + 套餐/汉堡营养聚合 |
| 实际结果 | 63 项可单点商品中 **37 项**匹配到官方营养数据（覆盖率 58.7%）；未匹配项在界面标「营养暂缺」，并显示"营养覆盖 37/63 件"，**不做插值或臆测** |

### 2.5 未使用但已评估的 Tool

| Tool | 为何未使用 |
|---|---|
| `calculate-price` | 本项目是"搭配预演"而非真实下单，价格直接取 `query-meals` 现价更稳定；接入它需先构造完整订单结构，收益有限 |
| `create-order` / `cancel-order` / `mall-*` | 涉及交易写操作，与"创意搭配 + 投票"场景无关，且主动规避任何下单风险 |
| `available-coupons` / `query-my-coupons` | 属账户私有资产，需用户登录态，本项目不采集账户信息 |

---

## 3. 调用流程

```
① 定位门店
   query-nearby-stores(beType=1, searchType=2, city=上海, keyword=人民广场)
        └─► storeCode = 1450713

② 拉在售菜单（核心）
   query-meals(storeCode=1450713, orderType=1, beType=1)
        └─► 119 项商品 ──► assets/menu_snapshot_20261023.json
                              │
                              ├─(下载) 官方产品图 menu-img.mcd.cn ──► assets/mcd_photos/  (127 张 427×320 透明 PNG)
                              └─(归类) 按名称关键词 → 10 组 ──► assets/materials.json

③ 补营养
   list-nutrition-foods()
        └─► 营养表 ──(按名称匹配)──► materials.json[].nutrition  (覆盖 37/63)

④ 补汉堡结构（仅 3D 模式需要）
   query-meal-detail(storeCode=1450713, orderType=1, beType=1, code=汉堡编码)  ×14
        └─► modification 食材清单 ──► BURGER_LAYERS（成分官方 + 顺序规范化）

⑤ 前端消费
   浏览器 GET /api/materials  ──► 货架渲染（图片/价格/分组）
   用户点选                   ──► DOM 托盘 / Three.js 3D 堆叠
   前端本地聚合                ──► 价格 + 热量/蛋白/脂肪/碳水/钠
   POST /api/designs          ──► gallery/gallery.json（含自动生成的预览图）
   POST /api/vote             ──► 票数 +1（同昵称同作品仅一次，重复返回 409）
```

### 数据清洗细节（`scripts/refresh_menu_from_mcp.py`）

| 步骤 | 处理 |
|---|---|
| 图片下载 | 官方图为 PNG；少数为 GIF，取**首帧**转 PNG |
| 尺寸 | 统一 427×320，保留原始留白与透明背景 |
| 分组 | 按名称关键词归入 10 组，顺序即优先级（先判"堡"→汉堡，避免"鳕鱼堡"被归进鱼类） |
| 在售口径 | 以 MCP 快照为权威，**已下架的季节限定不再进货架**，避免展示买不到的商品 |
| 营养 | 先取 `list-nutrition-foods`，缺失回落旧库，仍缺则留空（界面标"营养暂缺"） |
| 可单点判定 | `buyable = !整份套餐 && !周边` → 63 项 |

---

## 4. 业务价值

1. **把"点餐接口"变成"创作素材库"**
   麦当劳 MCP 原本服务于"查菜单 → 下单"的线性流程。本项目把 `query-meals` 的商品粒度重新组织为**可按品类检索、可自由拼装的素材**，让同一份数据支撑"自定义套餐 + 3D 汉堡设计"两种创作场景——这是对官方能力的**场景外扩**，而非简单封装。

2. **真实数据 = 可信的创意**
   所有价格、图片、营养都来自官方接口，用户拼出来的东西**今天真的能买到**，报价也是真的。这解决了同类"汉堡 DIY"玩具最大的问题：画得好看但买不到、算得热闹但数字是编的。

3. **给「多人共创」一个低成本落地方式**
   零依赖 Python 服务 + 共享 JSON 画廊，一个局域网内 5–20 人即可同时搭配、发布、投票。门店做活动、社团做团建、课堂做 Demo，不需要任何后端部署。

4. **可复用的 MCP 落地样板**
   完整保留了"门店 → 菜单 → 详情 → 营养"四级调用的真实参数、返回结构、字段陷阱（`rounds` 为空、`modification` 只含可特调项、`orderType/beType` 必传）与降级方案，其他开发者可直接照抄这条链路。

---

## 5. 降级与容错

| 场景 | 行为 |
|---|---|
| MCP 连接器未启用 / Token 失效 | 页面改读仓库内置快照 `assets/materials.json`，功能完整、数据仍为官方（仅不刷新） |
| `query-meals` 超时 | 沿用上次成功快照，不清空货架 |
| 营养缺失 | 标「营养暂缺」，合计卡显示"覆盖 n/m 件"，不参与估算的部分明确排除 |
| 官方图 404 | 该卡片显示占位色块 + 商品名，不阻塞页面 |
| 服务端并发写画廊 | `gallery.json` 原子写入（临时文件 + `os.replace`），避免半截文件 |

---

## 6. 合规与安全

- **只读**：仅调用 4 个查询类 Tool，不调用任何下单、支付、领券、账户类接口；
- **无凭证入库**：仓库与文档中零真实 Token，配置示例仅 `${MCD_MCP_TOKEN}`；
- **不采集个人信息**：不读取手机号、地址、订单与积分；投票昵称由用户自填，仅存本地 `gallery.json`；
- **限流友好**：仅在"刷新菜单"时批量调用一次（约 130 次请求），日常运行读本地快照；
- **数据来源可追溯**：每个快照文件带 `fetched_at` 与 `storeCode`，可回溯到具体门店与时刻；
- **遵守官方规则**：使用范围遵循 [麦当劳 MCP 服务规则](https://cdn.mcd.cn/cms/pages/MCPServerRules.html)。

---

## 7. 可核验证据

| 证据 | 文件 | 说明 |
|---|---|---|
| 工具清单 | `assets/mcp_tools_snapshot.json` | MCP `tools/list` 原始返回，35 个工具 |
| 菜单原始返回 | `assets/menu_snapshot_20261023.json` | `query-meals` 结果（119 项 + 时间戳 + 门店） |
| 餐品详情原始返回 | `assets/meal_detail_raw.json` | `query-meal-detail` 结果（含 `modification` 与 traceId） |
| 营养原始返回 | `assets/nutrition_raw.json` | `list-nutrition-foods` 结果 |
| 门店原始返回 | `assets/stores_raw.json` | `query-nearby-stores` 结果 |
| 派生素材库 | `assets/materials.json` | 119 项 / 10 组 / 63 可单点 / 37 有营养 |
| 官方图 | `assets/mcd_photos/` | 127 张 PNG，全部由官方链接下载 |
| 重建脚本 | `scripts/refresh_menu_from_mcp.py` | 快照 → 素材库 → 图片的完整可复现流程 |
