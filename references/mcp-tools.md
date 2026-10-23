# MCP 工具速查（面向 Agent 排障）

> 读者：需要判断"某个数据是官方来的还是本地推导的"的 Agent / 开发者。
> 面向评审的完整叙事见仓库根目录 `MCP_INTEGRATION.md`；本文只放**可查对的硬事实**。

## 0. 连接信息

| 项 | 值 |
|---|---|
| 服务名 | `mcd-mcp` |
| 协议 | Streamable HTTP |
| 地址 | `https://mcp.mcd.cn` |
| 鉴权 | `Authorization: Bearer ${MCD_MCP_TOKEN}` |
| 工具总数 | 35（全量清单：`assets/mcp_tools_snapshot.json`） |
| 本项目使用 | 4（全部只读） |

配置文件模板 `mcp-config.example.json`，**仓库内不含任何真实 Token**。

## 1. 调用时序（有依赖，不能乱序）

```
query-nearby-stores  ──► storeCode ──┬──► query-meals ──┬──► query-meal-detail (按 code 逐个)
                                     │                  └──► list-nutrition-foods（无参，全局）
                                     └──► 后续任何查询都必须带这个 storeCode
```

**为什么门店必须最先查**：麦当劳的菜单、价格、售罄状态都是门店级的。同一 SKU 在 A 店 34.5 元、在 B 店可能不售。

## 2. 四个工具逐个说

### 2.1 `query-nearby-stores`

| 参数 | 取值 | 说明 |
|---|---|---|
| `beType` | `1` | 1=到店自提 |
| `searchType` | `2` | 2=关键词检索（1 为按定位） |
| `city` | `"上海"` | 城市名 |
| `keyword` | `"人民广场"` | 商圈/地址关键词 |

返回门店列表，取 `storeCode`。本项目记录值：`1450713` / 麦当劳上海黄浦华旭国际大厦餐厅。

### 2.2 `query-meals`

| 参数 | 取值 |
|---|---|
| `storeCode` | 上一步拿到的门店编码 |
| `orderType` | `1`（到店自提） |
| `beType` | `1` |

返回分类树 + 商品 `code/name/image/price/originalPrice`。这是**唯一商品数据源**，
货架、价格、官方图全部由它派生。

真实结果：119 项，9 组 —— 汉堡 14 / 炸鸡 8 / 小食 8 / 甜品冰品 9 / 饮品 13 / 麦咖啡 9 / 蘸酱 2 /
整份套餐 51 / 周边 5，其中**可单点 63 项**（`buyable` 为真）。

### 2.3 `query-meal-detail`

| 参数 | 取值 |
|---|---|
| `storeCode` / `orderType` / `beType` | 同上 |
| `code` | 单品编码，如 `1100` |

返回 `data.rounds[]`（选配轮次，单品为空）、`data.modification.items[].values[]`（可特调食材）、600px 高清图。

**能力边界（必须知道）**：

- `modification` 只列**可特调食材**，不含肉饼与面包胚；
- `rounds` 对单品为空；
- 因此它**不提供层叠顺序**。

本项目处理方式：食材清单取 `modification`（官方），层叠顺序按官方产品页描述 + 通用汉堡结构整理，
写入前端 `BURGER_LAYERS`（14 条）与 `assets/official_composition.json`。
**成分是官方的，顺序是规范化的**——两者在代码与文档中都分开标注。

### 2.4 `list-nutrition-foods`

无参数，返回能量(kcal)/蛋白质/脂肪/碳水/钠/钙。

覆盖率真相：63 项可单点商品中 **37 项** 能匹配到官方营养（58.7%）。
未匹配项界面标「营养暂缺」并显示"营养覆盖 37/63 件"，**不做插值、不臆测**。

## 3. 未使用但评估过的工具

| 工具 | 不用原因 |
|---|---|
| `calculate-price` | 本场景是"搭配预演"不是真实下单，直接取 `query-meals` 现价更稳 |
| `create-order` / `cancel-order` / `mall-*` | 交易写操作，与创意搭配无关，主动规避下单风险 |
| `available-coupons` / `query-my-coupons` | 属账户私有资产，需登录态，本项目不采集 |

## 4. 失败与降级

| 情况 | 判断信号 | 处理 |
|---|---|---|
| 连接器未配置 | 工具不存在 | 直接读 `assets/materials.json` 快照，功能不降级 |
| Token 失效 | 401 | 提示用户去开放平台换 Token，期间用快照 |
| 门店不存在 | 返回空列表 | 换 `city`/`keyword` 重查，或沿用 `1450713` |
| 单品在目标门店不售 | 该 code 不在 `query-meals` 结果里 | 从货架剔除，不虚构替代品 |
| 营养缺失 | 匹配不到 | 标「营养暂缺」，绝不补 0 或插值 |

刷新素材库：

```bash
python scripts/refresh_menu_from_mcp.py --token $MCD_MCP_TOKEN
python scripts/refresh_menu_from_mcp.py --no-download   # 只重建索引，不重下图片
```

`OFFLINE=1` 时脚本拒绝联网，只做本地校验。
