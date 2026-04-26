# Alpine.js $persist 状态延续设计

## 目标

用 Alpine.js Persist 插件替换手动 localStorage 操作，实现 UI 状态跨刷新持久化。

## 持久化的状态

1. **Kanban 过滤偏好** — `kanbanFilter.locId` 用 `$persist('')`
2. **Workbench 选择器** — `workbenchSelector.locId` + `taskId` 用 `$persist('')`，并在 x-init 中自动加载内容
3. **表单草稿** — `formDraft` 组件的 draft 数据用 `$persist({})`，移除手动 localStorage 读写

## 不动的部分

- 主题切换（现有 localStorage 实现已经稳定，暂不迁移）

## 技术要点

- CDN: `https://cdn.jsdelivr.net/npm/@alpinejs/persist@3.x.x/dist/cdn.min.js`
- **必须在 Alpine 主文件之前加载**（persist 插件要求）
- `$persist()` 底层就是 localStorage，API 兼容

## 涉及文件

- `app/templates/base.html` — 加 persist CDN + 简化 formDraft
- `app/templates/tasks/kanban.html` — kanbanFilter 用 $persist
- `app/templates/workbench/index.html` — workbenchSelector 用 $persist + auto-load
