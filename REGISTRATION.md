# 报名指南（REGISTRATION）

> 本文件不是官方要求文件，仅为本项目的报名操作备忘：报名 Issue 文案、提交前自检、仓库文件对照。
> 官方规则以 [M-China/mcd-developer-innovation-challenge](https://github.com/M-China/mcd-developer-innovation-challenge) 为准。

---

## 1. 报名方式

在活动仓库下按标准格式发布 **Issue**（麦当劳通过 Issue 校验资格，校验逻辑较严格）。

**注意事项（官方明确要求）**

- 报名 Issue 的【标题】与【正文】之间**不要**使用换行符；
- 【项目简介】与简介内容之间**不要**使用换行符；
- 项目地址**不要**使用 Markdown 链接语法（如 `[文字](url)` 会校验失败）；
- 仓库必须为 **Public**，且创建时间在 2025-12-25 00:00 ~ 2026-10-25 23:59 之间；
- 截止时间：**2026-10-25 23:59（北京时间）**。

---

## 2. 可直接复制的 Issue 文案

### 标题

```
【参赛申请】麦当劳「真」随心配——用官方在售菜单自由拼套餐、设计3D汉堡并投票打榜
```

### 正文（整段复制，勿在字段间加空行）

```
【参赛申请】
项目名称：麦当劳「真」随心配
项目地址：https://github.com/Alex-star-arch/{{REPO_NAME}}
项目简介：把麦当劳 MCP 的真实在售菜单变成可自由拼装的素材：63 项可单点商品自由组合成自定义套餐，实时聚合价格与热量/蛋白/脂肪/碳水/钠（官方未公开营养的明确标注不臆测）；14 款在售汉堡可一键载入官方组成并做 3D 拆层设计；套餐与 3D 汉堡都能一键发布到共享画廊，供他人浏览与投票打榜。零依赖 Python 服务起在本机，同一 WiFi 下即可多人同时创作与互投，适合门店活动、社团团建与课堂演示。项目全程由腾讯 WorkBuddy 的 Agent 模式开发，并真实调用 query-nearby-stores / query-meals / query-meal-detail / list-nutrition-foods 四个 MCP 工具。
```

> 把 `{{REPO_NAME}}` 替换为实际仓库名（推送完成后填写）。
> 提交前请先在浏览器里打开该链接，确认**未登录状态也能访问**（即 Public）。

---

## 3. 提交前自检清单

| # | 官方条件 | 本项目状态 | 自查方式 |
|---|---|---|---|
| 1 | 包含 `README.md`（介绍/安装/示例/目标用户） | ✅ | 打开根目录 README，含「目标用户」「快速开始」「使用示例」章节 |
| 2 | 包含 `CONTEST_DECLARATION.md` 且**内容不可改动** | ✅ 与官方原文逐字节一致 | `diff` 官方文件，无差异 |
| 3 | 包含 `MCP_INTEGRATION.md`（Server/Tool/流程/价值） | ✅ | 含 4 个 Tool 真实参数、调用时序、业务价值 |
| 4 | 包含 `mcp-config.example.json`（仅环境变量占位） | ✅ | 只有 `${MCD_MCP_TOKEN}`，无真实 Token |
| 5 | 包含 `workbuddy.md`（WorkBuddy 专项必需） | ✅ | 含时间线、逐字对话节选、工具调用、证据索引 |
| 6 | 包含源代码 | ✅ | `assets/*.html|js`、`scripts/*.py` |
| 7 | 仓库公开可访问 | ⬜ 推送后确认 | 无痕窗口访问仓库 URL |
| 8 | 真实使用麦当劳 MCP | ✅ | `assets/*_raw.json` 原始返回可核验 |
| 9 | 真实使用腾讯 WorkBuddy | ✅ | `workbuddy.md` + `.workbuddy/memory/` 开发日志 |
| 10 | 项目创建时间在允许区间 | ⬜ 创建仓库时确认 | 仓库创建于 2026-10 月 |
| 11 | 内容合规（无敏感/侵权/恶意代码） | ✅ | 仅官方公开素材 + 原创代码；无外链风险内容 |

---

## 4. 仓库文件对照（评委视角）

```
README.md                  ← 项目介绍 / 安装 / 使用示例 / 目标用户
CONTEST_DECLARATION.md     ← 参赛声明（官方原文，未改）
MCP_INTEGRATION.md         ← MCP Server / Tool / 调用流程 / 业务价值
mcp-config.example.json    ← 脱敏配置（占位符）
workbuddy.md               ← WorkBuddy 开发对话上下文 ★ 专项奖励核验
SKILL.md                   ← WorkBuddy Skill 定义
LICENSE                    ← MIT
REGISTRATION.md            ← 本文件（报名备忘）
assets/                    ← 前端、组件库、MCP 快照、官方图、vendor
scripts/                   ← 零依赖服务端、数据重建脚本
gallery/                   ← 作品与投票持久化
screenshots/               ← 桌面 / 平板 / 手机截图
```

---

## 5. 排名规则提醒

- 排名依据：仓库**公开 Star 数**（活动开始前已获得的 Star 也计入）；
- 榜单单列 Star > 0 的项目，取前 100（并列同分全部进入）；
- 定榜时间：**2026-10-26 00:00** 采集的数据；
- 同一 GitHub 账号多个项目，只有 Star 最高的一个进榜。

> 因此报名的关键是：**仓库能跑通、README 一眼看懂、别人愿意点 Star**。README 顶部已放三张核心截图与"它解决什么问题"，便于传播。

---

## 6. 报名后待办

- [ ] 确认 Issue 下收到报名成功回执（失败会附原因，可修改后重新提交）；
- [ ] 仓库保持 Public 至活动结束（含领奖期）；
- [ ] 检查 GitHub 注册邮箱可读（获奖通知走邮箱）；
- [ ] 若获奖：2026-11-14 前提交收货信息 / 手机号 / WorkBuddy 积分兑换。
