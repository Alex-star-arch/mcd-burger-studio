# 排障手册

> 读者：跑不起来 / 跑起来不对的人。按"现象"查，不要按"我觉得是哪个模块"查。

## 快速定位三步

```bash
python scripts/run.py --check      # 1. 资产与依赖是否齐
python scripts/selfcheck.py        # 2. 八项断言，第几项红就是哪类问题
python scripts/run.py --no-open    # 3. 前台起服务看启动日志
```

`selfcheck.py` 的失败项编号就是下面章节号，直接跳转。

---

## 1. frontmatter / SKILL.md 相关

| 现象 | 原因 | 处理 |
|---|---|---|
| `name 与目录名不一致` | 改了目录名没改 frontmatter | 二者必须一致，否则 Agent 装载后引用不到 |
| `description 仅 N 字` | 触发词太少，Agent 命中率低 | 补场景词：拼套餐、创意汉堡、3D 汉堡、投票打榜 |
| `缺字段` | 手改时删掉了 | `name/description/version/license` 四个必需 |

## 2. 路径死链

| 现象 | 原因 | 处理 |
|---|---|---|
| `N 条失效: assets/xxx` | 文件被移动/删除但 SKILL.md 没同步 | 以代码实际引用为准改文档，**不要**为了让断言过而造空文件 |
| `_legacy_pages/` 里的文件找不到 | 该目录在 `.gitignore` 中，不进仓库 | 文档里不要引用它；需要保留说明就写进 CHANGELOG |

## 3. 素材库异常

| 现象 | 原因 | 处理 |
|---|---|---|
| `materials 为空` | 刷新脚本中途失败写了半截 | 用 `_backup/` 下的 `materials.json` 覆盖回来 |
| `total/buyable 与断言不符` | 换了门店或季节菜单变了 | **改 `selfcheck.py` 顶部常量**，别改数据迁就断言 |
| 价格全是 `null` | 抓的是套餐类，套餐通常无单点价 | 看 `buyable`，为 `true` 的才有价格 |
| 商品重复 | 多次 `refresh` 追加而非重建 | 脚本是重建语义，若重复说明改过代码，检查 `build()` |

## 4. 图片 404

| 现象 | 原因 | 处理 |
|---|---|---|
| 卡片全是破图 | 只拷了 HTML，没拷 `assets/mcd_photos/` | 必须整目录使用 |
| 少数几张破图 | 官方源当时是 GIF / 已下架 | 重跑 `refresh_menu_from_mcp.py`；仍缺就把该商品 `buyable` 设 false |
| 直接双击 HTML 打开全白 | `file://` 下 `/assets/` 绝对路径解析不到 | **必须经 HTTP 访问**，这是设计约束 |
| 图片加载很慢 | 误用了 `image` 字段（MCP CDN 外链） | 页面应读 `photo`（本地路径），检查是否被改回 |

## 5. 3D 相关

| 现象 | 原因 | 处理 |
|---|---|---|
| 3D 区域纯黑/纯白 | WebGL 不可用（虚拟机、远程桌面、禁用硬件加速） | Chrome/Edge 设置里开"使用硬件加速"；或启动加 `--use-gl=angle --use-angle=swiftshader` |
| 组件堆叠错位、悬空 | `Box3` 未在 `updateMatrixWorld` 后取包围盒 | 见 `burger_components_3d.html` 中 `addComponent` 的贴合逻辑，勿删 `updateMatrixWorld(true)` |
| 塔顶被裁 | 相机用了固定距离 | 走 `fitStackCamera(totalH)` 的包围球取景，不要写死 `camera.position.z` |
| 阴影浮在汉堡中间 | 阴影被挂到场景根而非 `compRoot` | 阴影必须挂 `compRoot`，按世界包围盒底面 `worldToLocal` 定位 |
| 控制台报 `Components3D is not defined` | 脚本顺序错 | 必须 `three.min.js` → `OrbitControls.js` → `GLTFLoader.js` → `components3d.js` |

> **GLB 不是 bug**：`mcd_component_models/*.glb` 已入库但前端**未加载**，3D 组件一律由
> `components3d.js` 程序化生成。目录里定义过 `COMP_DIR`/`gltfLoader` 但未接入调用链——
> 这是"预留替换位"，不是加载失败。别去追这个"404"。

## 6. 画廊 / 发布 / 投票

| 现象 | 原因 | 处理 |
|---|---|---|
| 发布成功但卡片没图 | 预览图超 6MB 被服务端丢弃，或 dataURL 不是 `data:image/` | 正常降级，卡片显示占位块；3D 截图过大时降低 `pixelRatio` |
| 投票 409 | 昵称已投过 | 换昵称或直接改 `gallery.json` 的 `voters`（仅调试） |
| 刷新后票数回退 | 服务在写盘前被强杀 | 写盘是 `os.replace` 原子替换，正常不会被截断；检查是否手工编辑过 JSON |
| 多人同时投票丢数据 | 未持锁的场景（例如自己写脚本绕过服务直接改文件） | 必须走 `POST /api/vote`，服务内有 `threading.Lock` |

## 7. 端口与网络

| 现象 | 原因 | 处理 |
|---|---|---|
| 端口被占用 | 上次服务没退 | `run.py` 自动顺延最多 20 个；或 `--port 8766` |
| 外部设备打不开 | 默认只监听 `127.0.0.1` | 加 `--lan` 监听 `0.0.0.0` |
| `--lan` 也不行 | 公司 WiFi 开了 AP 隔离 / 防火墙拦截 | 手机连热点再试；Windows 首次弹窗点"允许访问" |
| **curl 本地接口返回 502** | **系统代理（HTTP_PROXY）把 127.0.0.1 也转发了** | `curl --noproxy '*'` 或 `NO_PROXY=127.0.0.1,localhost`；`run.py` 的探活已内置绕过代理 |
| 中文输出乱码 | Windows 控制台 GBK | `run.py`/`selfcheck.py` 已 `reconfigure(utf-8)`；用 cmd 时先 `chcp 65001` |

## 8. 移动端

| 现象 | 原因 | 处理 |
|---|---|---|
| 底部抽屉被标签栏盖住 | `z-index` 层级冲突 | 抽屉 `97` / 标签栏 `96`，改动时保持这个顺序 |
| 浮动按钮挡住"发布" | IntersectionObserver 未生效 | 检查发布卡是否在 `watchPublish()` 的观察范围内 |
| 内容被刘海/圆角裁切 | 未适配安全区 | 布局需保留 `env(safe-area-inset-*)` |
| 电脑上截移动端图尺寸不对 | Windows headless Chrome 的 `--window-size` 不生效 | 用一个空白页把应用嵌进 `<iframe width=390 height=844>` 再截图（该调试页不入库，临时写一个即可） |

## 9. 什么时候该认输

以下都属于**设计取舍**，不是待修 bug，别再花时间：

- 组件级 3D 是程序化重建，不是官方模型（官方无组件级素材）；
- 官方营养只覆盖 37/63 件，缺的标"暂缺"而不是补全；
- 昵称即身份，换昵称可重复投票，无账号体系；
- 3D 层序是"成分官方、顺序规范化"，`rounds` 对单品为空是接口本身的限制。
