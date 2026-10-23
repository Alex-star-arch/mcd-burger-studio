---
name: mcd-burger-studio
description: 麦当劳「真」随心配 —— 把麦当劳 MCP 的真实在售菜单当积木，让用户自由搭配套餐或逐层叠出个性化汉堡：官方单品图 2D 拼盘 + 程序化 3D 组件堆叠双视图，价格与营养实时聚合，作品可发布到本地画廊供他人投票打榜。当用户想用麦当劳素材拼套餐、设计创意汉堡、做 3D 汉堡可视化、发起或参与汉堡作品投票时使用。
version: 2.0.1
author: 万正浩
license: MIT
tags: [麦当劳, McDonald's, MCP, 汉堡设计, 套餐搭配, 3D, 可视化, 投票, 画廊, skill]
agent_created: true
---

# 麦当劳「真」随心配 · McBurger Studio

一个跑在本机的零依赖小站：左边货架是麦当劳**真实在售**单品（价格、营养、官方图全部来自麦当劳 MCP），
用户把它们拖进托盘拼成套餐，或在 3D 场景里逐层叠成汉堡，成品可以发布到画廊让其他人投票。

- **不需要联网也能跑**：127 张官方图、119 项素材、13 个组件模型全部已入库。
- **不需要装任何包**：只用 Python 标准库，`python scripts/run.py` 即可。
- **不是官方产品**：仅供创意演示，价格与供应以麦当劳官方渠道为准。

---

## 一、30 秒上手

```bash
python scripts/run.py          # 自动挑端口 → 探活成功 → 打印访问地址
```

输出形如：

```
🍔 麦当劳「真」随心配 已启动
   本机访问: http://127.0.0.1:8765
   局域网访问: http://192.168.1.23:8765   (同一 WiFi 下其他设备可直接打开投票)
```

Agent 拿到地址后**直接把 URL 交给用户**，并说明三个标签页各自能做什么。服务需常驻，用后台方式拉起。

---

## 二、三个标签页（页面即全部功能）

| 标签 | 用户能做什么 | 关键交互 |
|---|---|---|
| 🍱 **套餐搭配** | 从 7 组货架挑官方单品放进托盘，自由组合成自定义套餐 | 点卡片加入；托盘内每项有 `−` `+` `✕`，份数上限 9、整单上限 30；右栏实时聚合**实付价 / 热量 / 蛋白 / 脂肪 / 碳水 / 钠** |
| 🧩 **汉堡设计** | 在 3D 场景里逐层叠汉堡，19 种组件随便加、随便删、随便换序 | 14 款经典汉堡可一键载入官方层序；拖拽旋转、滚轮缩放；相机按堆叠总高自动取景 |
| 🏆 **作品画廊** | 浏览全部作品、按票数排名、给喜欢的作品投票 | 按昵称去重投票；卡片可「载入」回到对应模式继续改；点图看大图 |

两种模式都能**发布**：前端用 canvas 把官方单品图合成为预览图（3D 模式直接截取渲染画面），
`POST /api/designs` 落盘到 `gallery/`，随后出现在画廊里参与排名。

移动端（≤1024px）：底部标签栏 + 底部抽屉选单品 + 圆形浮动「选单品」按钮（滚动到发布卡时自动淡出，避免遮挡）。

**自检钩子**：打开 `http://127.0.0.1:8765/?selftest=1` 会自动合成一张预览图并试发布一条作品，用于验证链路。

---

## 三、HTTP 接口（6 个，全部零鉴权本地调用）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 主应用（单文件 SPA） |
| GET | `/api/ping` | 探活，返回 `{"ok":true,"time":...}` |
| GET | `/api/materials` | 素材库全量 JSON（119 项，含价格/营养/官方图路径/是否可单点） |
| GET | `/api/gallery` | 全部作品，按票数降序 |
| POST | `/api/designs` | 发布作品：`{name, author, mode:"combo"\|"component", items\|layers, labels, summary, preview}` |
| POST | `/api/vote` | 投票：`{id, voter}`；同一昵称重复投返回 **409** |

静态资源走 `/assets/*` 与 `/gallery/*`，路径被限制在项目根目录内（越界返回 403）。

---

## 四、数据资产（全部已入库，离线可用）

| 资产 | 数量 | 用途 |
|---|---|---|
| `assets/materials.json` | 119 项（63 项可单点） | 唯一数据源：编码、名称、分组、价格、营养、官方图路径 |
| `assets/mcd_photos/` | **127 张**官方透明 PNG | 2D 货架卡片 + 托盘缩略图 + 发布预览合成 |
| `assets/components3d.js` | **19 种**程序化组件 | 面包胚上/下、牛肉饼、鸡排、板烧鸡腿排、鱼排、虾仁、培根、煎蛋、芝士片、生菜、番茄片、洋葱圈、酸黄瓜、酱料、薯条、麦乐鸡、派、冰淇淋 |
| `assets/burger_components_3d.html` | **14 套**官方层序 | 巨无霸/双层吉士/麦香鸡/麦香鱼/板烧/安格斯等一键还原 |
| `assets/mcd_component_models/` | 13 个 GLB | 组件模型的真实几何备份，供后续替换程序化几何（**当前前端未加载**） |
| `assets/vendor/` | three.min.js + OrbitControls.js + GLTFLoader.js | 本地化 Three.js r128，免 CDN |

7 组货架分组：汉堡 14 · 炸鸡 8 · 小食 8 · 甜品冰品 9 · 饮品 13 · 麦咖啡 9 · 蘸酱 2。

> **诚实说明**：3D 组件当前由 `components3d.js` 程序化生成（细分曲面 + 顶点噪声 + 芝麻/焦痕/融化细节），
> 不是官方 3D 模型；`GLTFLoader.js` 与 `mcd_component_models/*.glb` 已就位但尚未接入加载流程。
> 官方只提供成品/套餐粒度的图，没有组件级素材，这是能力边界，不是 bug。

---

## 五、麦当劳 MCP 集成（4 个工具）

服务名 `mcd-mcp`，streamablehttp，`https://mcp.mcd.cn`，鉴权头见 `mcp-config.example.json`（`MCD_MCP_TOKEN` 占位，**永不入库真实值**）。

| 工具 | 关键参数 | 拿到什么 |
|---|---|---|
| `query-nearby-stores` | `beType=1, searchType=2, city, keyword` | `storeCode` |
| `query-meals` | `storeCode, orderType=1, beType=1` | 在售菜单：分类、餐品编码、名称、图片、价格 |
| `query-meal-detail` | `storeCode, orderType=1, beType=1, code` | 单品官方组成（用于还原真实分层，如巨无霸=双层牛肉+芝士+生菜+酸黄瓜+洋葱+酱+三层包） |
| `list-nutrition-foods` | — | 热量/蛋白/脂肪/碳水/钠/钙 |

刷新素材：`python scripts/refresh_menu_from_mcp.py --token $MCD_MCP_TOKEN`
（已落盘快照 `assets/menu_snapshot_20261023.json`，门店 1450713 上海黄浦华旭国际大厦餐厅，2026-10-23 14:22）
加 `--no-download` 只重建索引不下载图片。

**降级**：MCP 不可用 / 离线评审 / 容器无外网时，一律回落 `assets/materials.json` 快照（同源真实数据），
功能零损失——只是菜单停留在快照时点，不再是"此刻在售"。

---

## 六、Agent 执行流程（照做即可，不要自由发挥）

1. **探活**：`python scripts/run.py --check` 看依赖与资产是否齐全（不启服务）。
2. **启动**：后台运行 `python scripts/run.py --port 8765`，等它打印 URL（内部已轮询 `/api/ping`）。
3. **交付链接**：把 `http://127.0.0.1:<端口>` 发给用户，并附一句"三个标签分别做什么"。
4. **接需求**：用户说"30 元以内""不要牛肉""来个巨无霸改版"时，从 `/api/materials` 读数据做筛选，
   直接给出具体组合（名称 + 编码 + 价格 + 热量合计），而不是让用户自己找。
5. **要投票**：提示用户把「局域网访问」地址发给同一 WiFi 下的其他人；或直接对 `/api/vote` 代投。
6. **收尾**：需要复核交付质量时跑 `python scripts/selfcheck.py`（8 项断言，不依赖网络）。

> 只有在用户明确要求"刷新菜单/换门店/看实时价格"时才调用 MCP；否则**默认走快照**，避免无谓外部依赖。

---

## 七、配置项（命令行参数优先，其次环境变量，最后默认值）

| 键 | 默认 | 说明 |
|---|---|---|
| `--port` / `PORT` | `8765` | 被占用时 `run.py` 自动顺延，最多试 20 个 |
| `--host` / `HOST` | `127.0.0.1` | 需局域网投票时用 `0.0.0.0`（`run.py --lan` 快捷开关） |
| `--no-open` | 关 | 默认启动后尝试用系统浏览器打开，CI/无头环境加此参数 |
| `MCD_MCP_TOKEN` | 空 | 仅刷新素材时需要 |
| `STORE_CODE` | `1450713` | 默认门店；换城市先用 `query-nearby-stores` 取 |
| `OFFLINE` | `0` | `1` 表示永不调用 MCP，只读快照 |
| Python | ≥3.8 | 零第三方依赖 |

---

## 八、文件结构（只列真实存在且被引用的）

```
SKILL.md                          ← 本文件，唯一权威说明
README.md                         ← 参赛说明 + 安装为 Skill
MCP_INTEGRATION.md                ← MCP 调用细节与证据
CHANGELOG.md                      ← 版本记录
LICENSE / CONTEST_DECLARATION.md  ← 许可与参赛声明
mcp-config.example.json           ← MCP 连接器配置模板
scripts/
  run.py                          ← 一键启动（探端口 → 起服务 → 探活 → 打印 URL）
  selfcheck.py                    ← 交付前 8 项断言
  studio_server.py                ← HTTP 服务本体（零依赖）
  refresh_menu_from_mcp.py        ← 从 MCP 重建 materials.json
  seed_gallery.py                 ← 预置画廊作品
  build_materials.py / fetch_menu.py / mcp_*.py   ← 开发期 MCP 探索脚本
assets/
  burger_components_3d.html       ← 前端单文件 SPA（三标签）
  components3d.js                 ← 19 种程序化组件几何
  materials.json                  ← 素材库快照
  mcd_photos/                     ← 127 张官方产品图
  mcd_component_models/           ← 13 个组件 GLB（备用）
  vendor/                         ← three.min.js / OrbitControls.js / GLTFLoader.js
gallery/gallery.json              ← 作品与投票持久化
references/                       ← 渐进披露：MCP 细节 / 数据结构 / 用户旅程 / 排障
examples/prompts.md               ← 3 条示例指令 → 期望行为
```

---

## 九、边界与合规

- **只用真实在售单品**，不臆造麦当劳不存在的 SKU；价格/营养以 MCP 或快照为准，页面标注"仅供参考"。
- **图片版权归麦当劳所有**，仅用于本次大赛演示；本项目非官方产品，不代表麦当劳立场。
- 组件级 3D 是**程序化重建**（依据官方成品形态与配色），用于让食材可被独立编辑，不等于官方配方。
- 不采集用户隐私：昵称仅存于本地 `gallery/gallery.json`，不上传任何服务器。

---

## 十、排障速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 端口被占用 | 上一次服务没退 | `run.py` 会自动顺延；或 `--port 8766` |
| 页面白屏 | 直接双击 HTML 打开（缺 `/assets/` 路由） | 必须经 HTTP 访问，不能 `file://` |
| 3D 区域空白 | WebGL 被禁用 / 无 GPU | 换 Chrome/Edge；虚拟机开软件渲染 |
| 图片 404 | 只拷贝了 HTML 没拷 `assets/` | 整目录使用，勿单文件搬运 |
| 发布成功但画廊没图 | 预览图超 6MB 被丢弃 | 正常现象，卡片会显示占位块 |

更多见 `references/troubleshooting.md`。
