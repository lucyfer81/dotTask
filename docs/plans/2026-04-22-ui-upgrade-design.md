# UI/UX 升级设计文档 - Command Center

**日期**: 2026-04-22
**方案**: 渐进式升级（方案 A）— 在现有 Flask + Tailwind CDN + HTMX 架构上逐步增强

---

## 1. 暗色主题系统

### 切换机制
- `<html>` 标签加 `class="light"` 或 `class="dark"`
- 导航栏右侧加日/月图标按钮，点击切换
- 当前选择存 `localStorage`，页面加载时恢复

### Tailwind 配置
CDN 模式下通过 inline config 启用 `darkMode: 'class'`

### 配色映射

| 元素 | 浅色 | 暗色 |
|------|------|------|
| 背景 | `bg-gray-50` | `bg-[#1a1b1e]` |
| 卡片 | `bg-white` | `bg-[#2c2e33]` |
| 边框 | `border-gray-200` | `border-[#373a40]` |
| 正文 | `text-gray-800` | `text-gray-200` |
| 次要文字 | `text-gray-600` | `text-gray-400` |

### 状态发光效果（暗色独有）
- Completed: `shadow-[0_0_8px_rgba(64,192,87,0.4)]`
- Blocked: CSS `animation: pulse-red` 呼吸灯
- In Progress: `shadow-[0_0_6px_rgba(34,139,230,0.3)]`

### 等宽字体
`font-mono` 用于 ID、日期、国家代码字段

---

## 2. 原地编辑 (Click-to-Edit)

### 适用范围
任务详情页的描述、备注、各 location 的 task_log

### 交互流程
1. 文本以普通 `<span>` 显示，带 `cursor-pointer` 和 hover 底线提示
2. 点击 → HTMX `hx-get="/tasks/<id>/edit-field?field=description"`
3. 服务端返回 `<textarea>` + 保存/取消按钮的局部 HTML
4. `hx-post` 提交 → 服务端更新 DB 并返回只读文本片段
5. HTMX 通过 `hx-target` 替换回原位

### 后端新增路由
- `GET /tasks/<id>/edit-field?field=xxx` → 返回编辑表单片段
- `POST /tasks/<id>/save-field` → 保存并返回显示片段
- 返回 HTML 片段（非完整页面）

---

## 3. 侧边抽屉 (Slide-over Drawer)

### 触发
任务列表页点击任务名称 → 打开抽屉（不跳转）

### 实现
- `base.html` 中加固定 `<div id="drawer">`，默认 `translate-x-full`
- `hx-get="/tasks/<id>/drawer"` 加载内容
- CSS `transition-transform duration-300` 滑入滑出
- 点击遮罩层或关闭按钮关闭

### 抽屉内容
- 任务基本信息（名称、状态、优先级、日期）
- 进度条（Completed/InProgress/Pending/Blocked 计数）
- Location 分配列表，支持在抽屉内改状态

### 保留跳转入口
加"在新页面打开"的小图标链接

---

## 4. 极速状态切换

### 列表页状态 badge
- 点击 badge → 弹出微型悬浮菜单（`position: absolute`）
- 菜单列出所有可选状态，点击后 `hx-post` 更新
- 服务端返回新 badge HTML，HTMX 局部替换

---

## 5. 看板视图 (Kanban)

### 路由
`GET /tasks/kanban`

### 布局
水平滚动，按状态分列：Not Started | In Progress | Blocked | On Hold | Completed

### 卡片内容
任务名称、优先级 badge、负责人、目标日期、进度链小方块

### 拖拽实现
- Sortable.js CDN，对每列初始化
- `onEnd` 回调 → `htmx.ajax('POST', '/tasks/<id>/update-status')`
- 拖拽时卡片 `opacity-80 rotate-2 scale-105`

### 后端新增
- `GET /tasks/kanban` → 渲染看板模板，数据按状态分组
- `POST /tasks/<id>/update-status` → 更新状态（复用现有逻辑）

---

## 6. 进度链 (Progress Chain)

### 位置
任务卡片底部、抽屉面板内

### 实现
- 每个 location 对应 `w-2 h-2 rounded` 小方块
- 颜色映射：Completed=绿、In Progress=蓝、Pending=灰、Blocked=红
- 全部完成时整条链加发光效果

---

## 7. 动效系统

### 清扫感搜索
- `hx-get="/tasks/search"` 实时触发
- 不匹配行 `animate-row-exit`：`scaleY(0); opacity:0; max-height:0; transition:300ms`
- 匹配行 `animate-row-enter`：`opacity 0→1, translateY 8px→0`

### 全局动效
- `fade-in-up`：进入视口 `opacity 0→1, translateY 12px→0`
- `scale-on-hover`：卡片 hover `scale(1.02)` + 阴影加深
- Toast 通知：替代 flash message，右上角滑入，3秒后自动消失

---

## 技术依赖

| 依赖 | 引入方式 | 用途 |
|------|----------|------|
| Tailwind dark mode | CDN config | 暗色主题 |
| HTMX (已有) | CDN | 局部更新、原地编辑、抽屉 |
| Sortable.js | CDN 新增 | 看板拖拽 |
| CSS animations | main.css | 动效 |

**无新增 Python 后端依赖，无新增 npm 依赖。**

---

## 实施阶段

### Phase 1: 视觉基线
- 暗色主题切换 + 配色
- 等宽字体 + 状态发光
- 全局动效 CSS

### Phase 2: 交互升级
- 原地编辑路由 + 模板
- 侧边抽屉
- 极速状态切换
- Toast 通知

### Phase 3: 看板与动效
- 看板视图 + Sortable.js
- 进度链
- 清扫感搜索
