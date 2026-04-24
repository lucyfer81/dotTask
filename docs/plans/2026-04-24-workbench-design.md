# Workbench 设计文档

**日期**: 2026-04-24
**状态**: 已确认

## 概述

为 dotTask 新增"沉浸式执行台"页面 `/workbench`，解决管理大量地点任务时"导航路径深、记录不便捷"的痛点。MVP 聚焦于双向联动选择器 + 状态大按钮 + 日志录入。

## 布局

经典双栏布局：

```
┌─────────────────────────────────────────────┐
│  [Location ▾]  [Task ▾]      (过滤联动)     │
├──────────────────┬──────────────────────────┤
│  Action Items    │  状态按钮区               │
│  ☑ 已完成检查    │  [Pending] [In Progress] │
│  ☐ 待处理事项    │  [Blocked] [Completed]   │
│  进度: 1/2       │                          │
│                  │  ┌──────────────────┐    │
│  ── 时光轴 ──   │  │  日志输入框       │    │
│  4/24 状态更新   │  │  Ctrl+Enter 提交  │    │
│  4/23 新增记录   │  └──────────────────┘    │
│                  │  📎 📧 辅助信息栏       │
└──────────────────┴──────────────────────────┘
```

- 14 寸笔记本：双栏约 40%/60% 分割
- 24 寸显示器：双栏充分利用宽度

## 数据层

**无数据库改动**。复用 TaskAssignment 现有字段：

- `local_status`：状态（Pending / In Progress / Blocked / Completed）
- `task_log`：日志 + Markdown checklist 行动项
- `it_name` / `it_role`：辅助信息
- `issue_blocker`：Blocked 原因

### task_log Markdown 格式

```
## 2026-04-24 14:30
已完成补丁分发，待重启验证。

## Action Items
- [x] 检查系统版本
- [x] 执行补丁分发
- [ ] 验证重启结果

## 2026-04-23 09:00
开始执行升级任务。
```

### 解析函数

新增 `parse_task_log(text)` 工具函数，返回：

```python
{
    "entries": [{"timestamp": "...", "content": "..."}],
    "checklist": [{"text": "...", "done": True/False}]
}
```

## 路由

新增 `workbench` Blueprint：

| 路由 | 方法 | 用途 | 返回 |
|---|---|---|---|
| `/workbench` | GET | 完整页面骨架 | 完整 HTML |
| `/workbench/options` | GET | 联动下拉选项 | HTML 片段 |
| `/workbench/content` | GET | 双栏详情内容 | HTML 片段 |
| `/workbench/log` | POST | 提交日志/勾选行动项 | 时光轴 HTML 片段 |
| `/workbench/status` | POST | 切换状态 | 状态按钮 + 时光轴 HTML |

联动逻辑：
- `GET /workbench/options?type=task&location_id=3` → location_id=3 的任务选项
- `GET /workbench/options?type=location&task_id=5` → task_id=5 的地点选项

## 前端交互

### 顶部选择器
- 两个 `<select>` 用 HTMX `hx-get` 联动
- 选择后另一个自动过滤，底部双栏通过 `hx-get="/workbench/content"` 加载
- 当 Location + Task 唯一确定 TaskAssignment 时显示内容

### 左栏（Context Pane）
- **Checklist**：从 task_log 解析 `- [ ]` / `- [x]`，渲染为可勾选 checkbox
  - 勾选时 `hx-post="/workbench/log"` 更新文本
  - 显示完成百分比进度条
- **时光轴**：倒序显示日志条目，左侧竖线 + 圆点标记

### 右栏（Action Pane）
- **状态按钮**：4 个彩色大按钮，点击 `hx-post="/workbench/status"`
  - Pending：灰色，In Progress：蓝色，Blocked：红色，Completed：绿色
  - 当前状态高亮，自动在时光轴插入状态变更记录
- **日志输入框**：`<textarea>` + Alpine.js 监听 Ctrl+Enter
  - 提交后清空，时光轴顶端即时显示新条目
  - 页面加载/切换任务时自动聚焦
- **辅助信息栏**：IT 联系人、文件/邮件链接（只读）

### Alpine.js 范围（最小化）
- 仅处理：Ctrl+Enter 提交、自动聚焦输入框

## 导航入口

在 base.html 顶部导航栏添加 "Workbench" 项，与 Dashboard / Tasks / Locations / Data 并列。

## 视觉风格

- Tailwind CSS + 暗色模式支持，与现有系统一致
- 已完成行动项：删除线样式
- Blocked 状态：醒目警告色
- Completed 状态：沉浸式置灰

## MVP 范围（不包含）

- 全局搜索 Command Bar（Ctrl+K）
- 自动聚焦下一个未完成任务
- 复杂的 UI 过渡动画
