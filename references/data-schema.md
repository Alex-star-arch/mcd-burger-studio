# 数据结构对照表

> 读者：要改数据、加商品、写脚本或调试前端的人。所有字段名均与仓库代码逐字一致。

## 1. `assets/materials.json`（唯一数据源）

顶层：

```json
{
  "updated_at": "2026-10-23 14:25",
  "source": "麦当劳 MCP query-meals + list-nutrition-foods（门店 1450713 …）",
  "store": { "storeCode": "1450713", "storeName": "麦当劳上海黄浦华旭国际大厦餐厅" },
  "total": 119,
  "group_counts": { "burger": 14, "chicken": 8, "side": 8, "dessert": 9,
                    "drink": 13, "coffee": 9, "sauce": 2, "combo": 51, "merch": 5 },
  "groups":  [ { "key": "burger", "cn": "汉堡", "emoji": "🍔", "color": "#C8772E" }, … ],
  "materials": [ … ]
}
```

单条素材：

```json
{
  "code": "511781",
  "name": "培根安格斯厚牛堡",
  "group": "burger",
  "group_cn": "汉堡",
  "emoji": "🍔",
  "color": "#C8772E",
  "price": 34.5,
  "originalPrice": 34.5,
  "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260309/product/MS_511781_320.png",
  "photo": "/assets/mcd_photos/511781.png",
  "nutrition": { "energyKcal": "707", "protein": "34", "fat": "44",
                 "carbohydrate": "43", "sodium": "1037", "calcium": "161" },
  "buyable": true
}
```

字段约定：

| 字段 | 类型 | 注意 |
|---|---|---|
| `code` | string | 主键，前端与 API 全部用它引用商品 |
| `group` | string | `burger/chicken/side/dessert/drink/coffee/sauce/combo/merch` |
| `price` | number | 门店现价；**可能为 `null`**（套餐类常有） |
| `image` | string | MCP 原始 CDN 地址，仅作溯源，页面**不加载**它 |
| `photo` | string | 本地官方图相对路径，页面实际用这个 |
| `nutrition` | object \| 缺省 | 值全是**字符串**；缺省表示官方无数据，界面标「营养暂缺」 |
| `buyable` | bool | `true` 才进 2D 货架（63 项） |

> 改数据后**不必重启服务**：`studio_server.load_materials()` 按 mtime 缓存，文件一变自动重载。

## 2. `assets/menu_snapshot_20261023.json`（MCP 原始快照）

```json
{
  "source": "麦当劳 MCP query-meals (orderType=1, beType=1)",
  "fetched_at": "2026-10-23 14:22:21",
  "storeCode": "1450713",
  "storeName": "麦当劳上海黄浦华旭国际大厦餐厅",
  "img_base": "https://menu-img.mcd.cn/pcm/prod/menu/",
  "meals": { "511781": ["培根安格斯厚牛堡", "20260309/product/MS_511781_320.png", 34.5, 34.5] }
}
```

`meals` 的值是紧凑数组：`[名称, 图片相对路径, 现价, 原价]`。`materials.json` 由它 + 营养接口派生。

## 3. `gallery/gallery.json`（作品与投票）

```json
{
  "designs": [
    {
      "id": "d1792737066633",
      "name": "巨无霸经典套餐",
      "author": "正浩",
      "created_at": "2026-10-23 14:31",
      "mode": "combo",
      "items": [ { "code": "1100", "qty": 1 }, { "code": "4810", "qty": 1 } ],
      "layers": ["1100", "4810", "9900008751"],
      "item_names": ["巨无霸", "薯条", "可乐"],
      "summary": { "price": 48.5, "kcal": 619, "protein": 29.0, "fat": 30.0,
                   "carb": 57.0, "sodium": 1057, "count": 3 },
      "preview": "/gallery/img_d1792737066633.jpg",
      "votes": 7,
      "voters": ["小明", "小红", "阿杰", "Lily", "Tom", "老王", "测试用户"]
    }
  ]
}
```

| 字段 | combo 模式 | component 模式 |
|---|---|---|
| `mode` | `"combo"` | `"component"` |
| `items` | `[{code, qty}]`，qty 1–9、总计 ≤30 | `[]` |
| `layers` | 按份数展开的 code 列表 | 组件 kind 列表，如 `["bunBottom","beef","cheese","bunTop"]` |
| `item_names` | 商品中文名 | 组件中文标签 |
| `preview` | `/gallery/img_<id>.jpg`；超 6MB 或被拒则 `""` | 同左 |
| `votes` | `len(voters)`，二者必须同步 | 同左 |

写入是"临时文件 + `os.replace`"的原子替换，且有 `threading.Lock` 保护，不会出现半截 JSON。

## 4. `BURGER_LAYERS`（前端内，14 套官方层序）

位于 `assets/burger_components_3d.html` 约第 904 行：

```js
var BURGER_LAYERS={
  "1100":["bunBottom","beef","cheese","lettuce","pickle","onion","sauce","beef","bunTop"],
  "1106":["bunBottom","beef","cheese","beef","cheese","bacon","tomato","lettuce","sauce","bunTop"],
  …
};
```

键是商品 `code`，值是**从下到上**的组件 `kind`。只有出现在这个映射里的汉堡，
在「汉堡设计」页才有"一键载入官方层序"按钮。

## 5. `Components3D.CATALOG`（19 种组件）

`assets/components3d.js` 导出：

```js
global.Components3D = { buildComponent, stackComponents, CATALOG, PRIORITY, NUTRITION, builders, COLORS, Tex };
```

```js
{ kind: "bunTop", label: "面包胚(上·带芝麻)", height: 0.78 }
```

- `height` 是**归一化后的相对高度**，用于 `stackComponents` 累加与相机取景。
- 全部 19 种：`bunTop bunBottom beef chicken grilled fish shrimp bacon egg cheese lettuce tomato onion pickle sauce fries nuggets pie icecream`。
- 标签对照：面包胚上/下、牛肉饼、鸡排、板烧鸡腿排、鱼排、虾仁、培根、煎蛋、芝士片、生菜、番茄片、洋葱圈、酸黄瓜、酱料、薯条(平放)、麦乐鸡、派、圆筒冰淇淋。
- 加载顺序必须是 `three.min.js` → `OrbitControls.js` → `GLTFLoader.js` → `components3d.js` → 内联脚本。

## 6. HTTP 请求体范例

**发布套餐**：

```http
POST /api/designs
{"name":"巨无霸经典套餐","author":"正浩","mode":"combo",
 "items":[{"code":"1100","qty":1},{"code":"4810","qty":1}],
 "summary":{"price":48.5,"kcal":619,"protein":29,"fat":30,"carb":57,"sodium":1057,"count":3},
 "preview":"data:image/jpeg;base64,…"}
```

**发布组件汉堡**：

```http
POST /api/designs
{"name":"双层芝士塔","author":"正浩","mode":"component",
 "layers":["bunBottom","beef","cheese","beef","cheese","bunTop"],
 "labels":["面包胚(下)","牛肉饼","芝士片","牛肉饼","芝士片","面包胚(上·带芝麻)"],
 "summary":{"kcal":780},"preview":"data:image/png;base64,…"}
```

**投票**：

```http
POST /api/vote
{"id":"d1792737066633","voter":"小明"}
```

响应与错误码：

| 码 | 场景 | 响应体 |
|---|---|---|
| 200 | 成功 | `{"votes":8,"voter":"小明"}` |
| 400 | 昵称空 / 未选单品 | `{"error":"请先填写昵称再投票"}` |
| 404 | 作品 id 不存在 | `{"error":"作品不存在"}` |
| 409 | 同一昵称重复投票 | `{"error":"你已经为该作品投过票啦","votes":7}` |

字段长度在服务端强制裁剪：`name` ≤24、`author`/`voter` ≤12、组件标签 ≤16、单次最多 20 条 items。
