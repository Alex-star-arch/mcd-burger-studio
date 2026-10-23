---
name: mcd-burger-studio
description: 麦当劳「真」随心配——基于麦当劳 MCP 真实在售素材，让用户自由组合设计个性化汉堡，提供 3D 可视化（汉堡本体与全部食材一律使用麦当劳官方产品图，零自定义/占位几何与贴图，并按官方规范顺序排列）、多人参与设计与作品画廊投票打榜。用户想用麦当劳素材做创意汉堡、3D 可视化叠汉堡、发起/参与汉堡设计比赛或投票时使用。
version: 1.0.0
author: 万正浩
license: MIT
tags: [麦当劳, McDonald's, MCP, 汉堡设计, 创意, 可视化, 投票, 画廊]
agent_created: true
---

# 麦当劳「真」随心配 (McDonald's Make-It-Your-Way)

一个围绕「麦当劳 MCP」的真实创意 Skill：把麦当劳在售餐品当作设计素材，让用户像叠汉堡一样自由组合，实时可视化呈现，并支持多人参与设计、作品画廊展示与投票打榜。

## 核心能力（对应需求四要素）
1. **自由组合设计**：调用麦当劳 MCP 拉取真实在售菜单，分类为 汉堡/牛肉/炸鸡/鱼虾/芝士/卷/蔬果/小食/酱料/甜品/饮料 等素材，用户随意叠层设计个性化汉堡。
2. **可视化呈现（官方素材 3D）**：汉堡本体与全部食材（牛肉/芝士/蔬菜/水果/饮品/小食/甜品等）**一律使用麦当劳官方产品图**（`assets/mcd_photos/*.png`，123 款透明 PNG），**不使用任何自定义或占位几何/贴图**——每个被选中的产品以官方照片作为 3D 布告板(billboard)在轨道可控场景中呈现，单一整只汉堡直接呈现官方整图（其内部牛肉/芝士/蔬菜/水果的排列由官方产品图本身保证）。排序严格遵循 **`assets/official_composition.json`** 的官方规范顺序（分类 priority + 经典汉堡组成顺序），并提供「⬆ 按官方规范排序」按钮。支持鼠标拖拽旋转、滚轮缩放；并聚合热量/蛋白/脂肪/价格。
3. **多人参与**：所有用户共用同一画廊（`gallery/gallery.json`）；通过本地工作室服务，任何人都能打开页面设计、发布自己的作品。
4. **展示与投票**：画廊按票数实时排名，访客可为喜欢的作品投票（按昵称去重），形成创意打榜。

## 麦当劳 MCP 集成（必须真实调用）
本 Skill 真实使用已配置的 `mcd-mcp`（streamablehttp, https://mcp.mcd.cn）。流程：
1. `mcp__mcd-mcp__query-nearby-stores`（beType=1, searchType=2, city=用户所在城市, keyword=区域）→ 取 `storeCode`。
2. `mcp__mcd-mcp__query-meals`（storeCode, orderType=1, beType=1）→ 取真实在售菜单（分类、餐品编码、名称、图片、价格）。
3. `mcp__mcd-mcp__query-meal-detail`（storeCode, orderType=1, beType=1, code）→ 取餐品**官方组成**（用于还原真实汉堡分层，如巨无霸=双层牛肉+芝士+生菜+酸黄瓜+洋葱粒+特制酱+三层芝麻面包）。
3. `mcp__mcd-mcp__list-nutrition-foods` → 取营养数据，关联到素材用于热量/蛋白聚合。
4. （可选）`mcp__mcd-mcp__calculate-price` → 对设计作品做更精确计价。

> 若麦当劳 MCP 连接器不可用或调用失败，**回退**到仓库内置快照 `assets/materials.json`（同样来自上述真实接口，已落盘），保证 Skill 仍可演示。

## 工作流（Agent 执行步骤）
当用户说「设计汉堡 / 做个麦当劳创意汉堡 / 开汉堡设计大赛」等时：

### 步骤 A：准备素材库
- 优先用上面的 MCP 三步拉取真实菜单；用 `scripts/build_materials.py` 生成/更新 `assets/materials.json`（分类+配色+营养）。
- 兜底：直接使用内置 `assets/materials.json`。

### 步骤 B：两种使用模式，询问用户偏好
- **模式 1 · 3D 网页工作室（推荐，完整 3D 可视化+多人+投票）**：启动本地服务
  `python scripts/studio_server.py --port 8765`（用 run_in_background 保持存活），然后把 `http://localhost:8765` 交给用户。页面包含「设计工坊」与「作品画廊」两个标签页：设计工坊里左侧素材库每款食材均为 **官方产品图**，点选即把该食材加入中央的 **实时 3D 预览**（每项以官方照片布告板在轨道场景里按官方规范顺序呈现），右侧实时营养/价格聚合，并可点「⬆ 按官方规范排序」；画廊里每款作品也以官方产品图并排呈现，可投票与「载入」回工坊。
- **模式 2 · 离线 3D 展示**：直接用浏览器打开 `assets/demo3d.html`（已内联真实素材数据），查看多款 3D 汉堡作品，适合快速演示/评审，无需启动服务。
- **模式 3 · 对话式设计（无浏览器）**：Agent 直接引导用户选择素材编码/名称，调用 `assets/burger_renderer.py` 的 `render_burger_svg(codes)` 生成 2D SVG 预览，写入 `*.svg`/HTML；把作品追加到 `gallery/gallery.json`（结构见下）并用 `present_files` 展示；投票则更新对应作品的 `votes`/`voters`。

### 步骤 C：画廊数据结构（与网页服务共用）
```json
{
  "designs": [
    {
      "id": "d<时间戳>",
      "name": "麦门至尊塔",
      "author": "正浩",
      "created_at": "2026-10-20 12:00",
      "layers": ["1440", "521903", "9900016076"],
      "votes": 3,
      "voters": ["小明", "小红", "阿杰"]
    }
  ]
}
```
- `layers` 为从下到上的麦当劳素材编码（来自 `materials.json`）。
- 投票时把投票人昵称加入 `voters` 并 `votes = len(voters)`；同一昵称不可重复投票。

## 组件级 3D 设计（2D→3D 转化 + 食材分离）⭐ 进阶能力
针对"界面只展示套餐整体、无法单独设计单汉堡、无法分离食材"的痛点，本 Skill 额外提供组件级 3D 设计工作室（`assets/burger_components_3d.html`，服务路由 `/components`），两种模式：
1. **单品模式（官方图转 3D）**：用 `assets/img2mesh.js` 把每个官方透明 PNG 转为 **带倒角的恒定厚度立体切片**（受光 `MeshStandardMaterial` + 官方贴图 UV），旋转时呈现真实体积与光影（不再是纸片或鼓包）；每个官方单品成为可独立旋转/摆放的实体，点击即加入场景、可叠加多个，**打破套餐绑定**。
2. **组件模式（汉堡拆解设计）**：用 `assets/components3d.js` 把汉堡拆成 **可分离的组件 3D 模型**（面包胚上/下、牛肉饼、鸡排、鱼排、芝士片、生菜、番茄、洋葱圈、酸黄瓜、酱料、培根、煎蛋）——采用**高保真食物几何**重建（细分曲面 + 顶点噪声 + 芝麻/面包糠/焦痕/融化下垂等真实表面细节），每个组件独立生成、可单独删除/重排/自由组合，并按 `official_composition.json` 的官方规范顺序堆叠（一键"经典巨无霸"预设）。

**3D 方法选型（已换代）**：早期用"布告板纸片 + 圆顶鼓包挤出 + 彩色积木"三种伪 3D，观感差；现已统一为**受光实体几何**——单品走"带倒角恒厚立体切片"（保留官方贴图），组件走"高保真程序化食物几何"。生成式 image-to-3D（Tripo/Meshy）需云端 API、深度估计需 PyTorch+GPU，本环境暂不可用，故采用纯几何可落地方案；若后续接入远程 GPU 可升级为生成式。
**组件分离的现实约束**：麦当劳官方菜单只有成品/套餐粒度单品、无组件级素材图，故官方成品图走 image-to-3D 立体切片；内部组件按"已调研官方形态+官方配色"做高保真程序化重建，使食材可被独立编辑。

## 设计原则 / 边界
- 仅使用麦当劳**真实在售**素材，不臆造不存在的单品；价格/营养以 MCP 实时或快照数据为准。
- 鼓励创新组合：汉堡、小食、甜品、饮料皆可叠进同一座「汉堡塔」，越有创意越好。
- 非官方产品，仅供娱乐/创意展示；餐品供应、价格以麦当劳官方实时渠道为准（见 CONTEST_DECLARATION.md）。

## 文件结构
- `SKILL.md`：本技能定义
- `assets/materials.json`：分类素材库（MCP 真实数据快照）
- `assets/burger3d.js`：官方素材 3D 引擎 v3.0（Three.js；全部产品以官方产品图布告板呈现，零自定义/占位几何与贴图，按官方规范排序）
- `assets/img2mesh.js`：2D→3D 工具（官方透明 PNG → 带倒角恒厚立体切片，受光 MeshStandardMaterial，带贴图 UV）
- `assets/components3d.js`：可分离汉堡组件 3D 模型库 v2（高保真食物几何：细分+噪声+芝麻/面包糠/焦痕/融化；独立生成、按官方规范排序堆叠）
- `assets/official_composition.json`：官方构造/排序规范（分类 priority + 巨无霸等经典汉堡组成顺序）
- `assets/mcd_photos/`：123 款官方产品图（透明 PNG，官方素材唯一来源）
- `assets/burger_studio_3d.html`：3D 网页工作室前端（设计 + 画廊 + 投票）
- `assets/burger_components_3d.html`：组件级 3D 设计工作室（官方图转 3D + 组件分离/自由组合）
- `assets/vendor/`：本地化 Three.js r128 + OrbitControls（离线可用）
- `assets/burger_renderer.py` / `assets/burger_studio.html` / `assets/demo.html`：旧版 2D SVG 方案（保留对照）
- `assets/demo3d.html`：离线官方图展示页（内联 123 款官方素材 + 种子作品，双击即开，2D 官方图呈现）
- `scripts/studio_server.py`：零依赖本地服务（REST：素材/渲染/发布/投票）
- `scripts/fetch_menu.py` / `scripts/build_materials.py`：开发期从 MCP 生成素材库
- `gallery/gallery.json`：作品与投票持久化存储
- `README.md` / `MCP_INTEGRATION.md` / `CONTEST_DECLARATION.md` / `mcp-config.example.json`：参赛交付文件
