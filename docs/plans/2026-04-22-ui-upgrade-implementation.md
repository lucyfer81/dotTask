# Command Center UI 升级实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 dotTask 从表格工具升级为沉浸式个人指挥中心，包含暗色主题、原地编辑、侧边抽屉、看板视图和动效系统。

**Architecture:** 渐进式升级，在现有 Flask + Tailwind CDN + HTMX 架构上逐步增强。Phase 1 改视觉层，Phase 2 改交互层，Phase 3 加新功能。每个 Phase 独立可交付。

**Tech Stack:** Flask, Jinja2, Tailwind CSS (CDN + dark mode), HTMX 2.0.4, Sortable.js (CDN 新增), Chart.js, 纯 CSS 动画

---

## Phase 1: 视觉基线 — 暗色主题 + 动效

### Task 1: 配置 Tailwind CDN 暗色模式 + 引入 Sortable.js

**Files:**
- Modify: `app/templates/base.html:1-11`

**Step 1: 在 base.html 的 `<head>` 中添加 Tailwind 暗色配置和 Sortable.js CDN**

在 `<script src="https://cdn.tailwindcss.com"></script>` 之后插入 Tailwind config，在 HTMX script 之后添加 Sortable.js：

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Cascadia Code', 'monospace'],
      },
      colors: {
        'cc-bg': '#1a1b1e',
        'cc-card': '#2c2e33',
        'cc-border': '#373a40',
      }
    }
  }
}
</script>
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js"></script>
```

**Step 2: 验证页面加载正常**

Run: `cd /home/ubuntu/my-repos/dotTask && .venv/bin/python run.py`
Expected: 浏览器打开 `http://localhost:5000` 页面正常加载

**Step 3: 提交**

```bash
git add app/templates/base.html
git commit -m "feat: configure Tailwind dark mode and add Sortable.js CDN"
```

---

### Task 2: 添加暗色主题切换按钮

**Files:**
- Modify: `app/templates/base.html:14-29` (导航栏区域)

**Step 1: 在导航栏右侧添加主题切换按钮**

在 `<nav>` 的 `<div class="flex justify-between h-16">` 内，在关闭的 `</div>` 之前（即 flex 容器末尾）插入主题切换按钮：

```html
<!-- 在导航栏末尾 </div> 之前添加 -->
<div class="flex items-center">
    <button id="theme-toggle" type="button" class="p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-cc-card focus:outline-none" title="Toggle dark mode">
        <svg id="theme-icon-light" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
        </svg>
        <svg id="theme-icon-dark" class="w-5 h-5 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
        </svg>
    </button>
</div>
```

**Step 2: 在 `</body>` 之前添加主题切换 JS**

在 `base.html` 的 `{% block extra_js %}{% endblock %}` 之后，`</body>` 之前插入：

```html
<script>
// Theme toggle
(function() {
    const html = document.documentElement;
    const toggle = document.getElementById('theme-toggle');
    const iconLight = document.getElementById('theme-icon-light');
    const iconDark = document.getElementById('theme-icon-dark');

    function setTheme(dark) {
        if (dark) {
            html.classList.add('dark');
            iconLight.classList.add('hidden');
            iconDark.classList.remove('hidden');
        } else {
            html.classList.remove('dark');
            iconLight.classList.remove('hidden');
            iconDark.classList.add('hidden');
        }
        localStorage.setItem('theme', dark ? 'dark' : 'light');
    }

    // Init from localStorage
    const saved = localStorage.getItem('theme');
    if (saved === 'dark') setTheme(true);

    toggle.addEventListener('click', function() {
        setTheme(!html.classList.contains('dark'));
    });
})();
</script>
```

**Step 3: 提交**

```bash
git add app/templates/base.html
git commit -m "feat: add dark/light theme toggle with localStorage persistence"
```

---

### Task 3: 更新 base.html 骨架的暗色样式

**Files:**
- Modify: `app/templates/base.html:12-48`

**Step 1: 给 `<body>` 和导航栏添加 dark: 类**

将 `<body class="bg-gray-50 min-h-screen">` 改为：
```html
<body class="bg-gray-50 dark:bg-cc-bg min-h-screen text-gray-900 dark:text-gray-200 transition-colors duration-300">
```

将 `<nav class="bg-white shadow-sm border-b border-gray-200">` 改为：
```html
<nav class="bg-white dark:bg-cc-card shadow-sm border-b border-gray-200 dark:border-cc-border">
```

将应用名称链接 `text-xl font-bold text-gray-800` 改为：
```html
text-xl font-bold text-gray-800 dark:text-gray-100
```

将所有导航链接中的 `text-gray-600` 改为 `text-gray-600 dark:text-gray-400`，
`hover:text-blue-600` 改为 `hover:text-blue-600 dark:hover:text-blue-400`，
`text-blue-600 border-b-2 border-blue-600` 改为 `text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400`。

**Step 2: 给 flash 消息添加 dark: 类**

将 flash 消息的 `bg-green-50 text-green-800` 改为 `bg-green-50 dark:bg-green-900/30 dark:text-green-300`，
`bg-red-50 text-red-800` 改为 `bg-red-50 dark:bg-red-900/30 dark:text-red-300`，
`bg-blue-50 text-blue-800` 改为 `bg-blue-50 dark:bg-blue-900/30 dark:text-blue-300`。

**Step 3: 给 `<main>` 添加 dark: 类**

`<main>` 不需要改动（已经继承了 body 的暗色背景）。

**Step 4: 验证**

Run: 浏览器中点击主题切换按钮，确认页面颜色在亮暗之间正确切换。

**Step 5: 提交**

```bash
git add app/templates/base.html
git commit -m "feat: apply dark mode classes to base template skeleton"
```

---

### Task 4: 更新 main.css — 暗色 badge + 动画 + 状态发光

**Files:**
- Modify: `app/static/css/main.css`

**Step 1: 完全重写 main.css，添加暗色 badge 和动画系统**

```css
/* === HTMX 指示器 === */
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline-block; }
.htmx-request.htmx-indicator { display: inline-block; }

/* === 表格行 hover === */
.table-row-hover:hover {
    background-color: #f9fafb;
}
.dark .table-row-hover:hover {
    background-color: #353840;
}

/* === Badge 基础 === */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
}

/* === 浅色 Badge === */
.badge-not-started { background-color: #e5e7eb; color: #374151; }
.badge-in-progress { background-color: #dbeafe; color: #1d4ed8; }
.badge-completed { background-color: #d1fae5; color: #065f46; }
.badge-on-hold { background-color: #fef3c7; color: #92400e; }
.badge-cancelled { background-color: #fee2e2; color: #991b1b; }
.badge-pending { background-color: #e5e7eb; color: #374151; }
.badge-blocked { background-color: #fee2e2; color: #991b1b; }
.badge-na { background-color: #f3f4f6; color: #6b7280; }
.badge-critical { background-color: #fee2e2; color: #991b1b; }
.badge-high { background-color: #fef3c7; color: #92400e; }
.badge-medium { background-color: #dbeafe; color: #1d4ed8; }
.badge-low { background-color: #d1fae5; color: #065f46; }

/* === 暗色 Badge === */
.dark .badge-not-started { background-color: #374151; color: #9ca3af; }
.dark .badge-in-progress { background-color: #1e3a5f; color: #60a5fa; }
.dark .badge-completed { background-color: #064e3b; color: #34d399; }
.dark .badge-on-hold { background-color: #78350f; color: #fbbf24; }
.dark .badge-cancelled { background-color: #7f1d1d; color: #fca5a5; }
.dark .badge-pending { background-color: #374151; color: #9ca3af; }
.dark .badge-blocked { background-color: #7f1d1d; color: #fca5a5; }
.dark .badge-na { background-color: #1f2937; color: #6b7280; }
.dark .badge-critical { background-color: #7f1d1d; color: #fca5a5; }
.dark .badge-high { background-color: #78350f; color: #fbbf24; }
.dark .badge-medium { background-color: #1e3a5f; color: #60a5fa; }
.dark .badge-low { background-color: #064e3b; color: #34d399; }

/* === 暗色状态发光 === */
.dark .badge-completed {
    box-shadow: 0 0 8px rgba(64, 192, 87, 0.4);
}
.dark .badge-blocked {
    animation: pulse-red 2s ease-in-out infinite;
}
.dark .badge-in-progress {
    box-shadow: 0 0 6px rgba(34, 139, 230, 0.3);
}

@keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 4px rgba(250, 82, 82, 0.3); }
    50% { box-shadow: 0 0 12px rgba(250, 82, 82, 0.6); }
}

/* === 全局动效 === */
.fade-in-up {
    animation: fadeInUp 0.3s ease-out;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

.scale-on-hover {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.scale-on-hover:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.dark .scale-on-hover:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* === Toast 通知 === */
#toast-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
.toast {
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    animation: slideInRight 0.3s ease-out;
    max-width: 360px;
}
.toast-success { background-color: #065f46; color: #34d399; }
.toast-error { background-color: #7f1d1d; color: #fca5a5; }
.toast-info { background-color: #1e3a5f; color: #60a5fa; }
.toast-exit { animation: slideOutRight 0.3s ease-in forwards; }

@keyframes slideInRight {
    from { opacity: 0; transform: translateX(100%); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes slideOutRight {
    from { opacity: 1; transform: translateX(0); }
    to { opacity: 0; transform: translateX(100%); }
}

/* === 搜索行动画 === */
.animate-row-exit {
    transform: scaleY(0);
    opacity: 0;
    max-height: 0 !important;
    padding-top: 0;
    padding-bottom: 0;
    margin-top: 0;
    margin-bottom: 0;
    overflow: hidden;
    transition: all 300ms ease-out;
}
.animate-row-enter {
    animation: fadeInUp 0.3s ease-out;
}

/* === 抽屉面板 === */
#drawer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 40;
    opacity: 0;
    transition: opacity 300ms;
    pointer-events: none;
}
#drawer-overlay.active {
    opacity: 1;
    pointer-events: auto;
}
#drawer-panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 600px;
    max-width: 90vw;
    z-index: 50;
    transform: translateX(100%);
    transition: transform 300ms ease;
    overflow-y: auto;
}
#drawer-panel.active {
    transform: translateX(0);
}

/* === 看板卡片拖拽 === */
.sortable-ghost {
    opacity: 0.4;
}
.sortable-chosen {
    transform: rotate(2deg) scale(1.05);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

/* === 进度链小方块 === */
.progress-dot {
    width: 8px;
    height: 8px;
    border-radius: 2px;
    display: inline-block;
    margin-right: 2px;
}
.progress-dot-completed { background-color: #40c057; }
.progress-dot-in-progress { background-color: #228be6; }
.progress-dot-pending { background-color: #6b7280; }
.progress-dot-blocked { background-color: #fa5252; }
.progress-dot-na { background-color: #4b5563; }
.progress-chain-complete {
    box-shadow: 0 0 8px rgba(64, 192, 87, 0.5);
}
```

**Step 2: 提交**

```bash
git add app/static/css/main.css
git commit -m "feat: add dark mode badges, glow effects, animations, drawer and toast CSS"
```

---

### Task 5: 在 base.html 中添加 Toast 容器和 Drawer 容器

**Files:**
- Modify: `app/templates/base.html`

**Step 1: 在 `<body>` 开头添加 Toast 容器**

在 `<body>` 标签之后立即添加：
```html
<div id="toast-container"></div>
```

**Step 2: 在 `</body>` 之前添加 Drawer 容器**

在主题切换 JS 的 `<script>` 之前添加：
```html
<!-- Drawer Panel -->
<div id="drawer-overlay" onclick="closeDrawer()"></div>
<div id="drawer-panel" class="bg-white dark:bg-cc-card shadow-2xl"></div>
```

**Step 3: 在主题切换 JS 的 IIFE 之后添加 Drawer 和 Toast 的 JS 函数**

```html
<script>
// Drawer
function openDrawer(url) {
    const overlay = document.getElementById('drawer-overlay');
    const panel = document.getElementById('drawer-panel');
    panel.innerHTML = '<div class="p-8 text-center text-gray-500 dark:text-gray-400">Loading...</div>';
    overlay.classList.add('active');
    panel.classList.add('active');
    htmx.ajax('GET', url, '#drawer-panel');
}
function closeDrawer() {
    document.getElementById('drawer-overlay').classList.remove('active');
    document.getElementById('drawer-panel').classList.remove('active');
}

// Toast
function showToast(message, type) {
    type = type || 'info';
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function() {
        toast.classList.add('toast-exit');
        setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
}
</script>
```

**Step 4: 提交**

```bash
git add app/templates/base.html
git commit -m "feat: add toast container and drawer panel to base template"
```

---

### Task 6: 更新 Dashboard 模板暗色样式

**Files:**
- Modify: `app/templates/dashboard/index.html`

**Step 1: 给所有卡片元素添加 dark: 类**

所有 `bg-white` 改为 `bg-white dark:bg-cc-card`，
`border-gray-200` 改为 `border-gray-200 dark:border-cc-border`，
`text-gray-800` 改为 `text-gray-800 dark:text-gray-100`，
`text-gray-700` 改为 `text-gray-700 dark:text-gray-300`，
`text-gray-500` 改为 `text-gray-500 dark:text-gray-400`，
`text-gray-600` 改为 `text-gray-600 dark:text-gray-400`。

给统计卡片添加 `scale-on-hover` 类。

给 alert 卡片的 `bg-red-50` 改为 `bg-red-50 dark:bg-red-900/20`，`border-red-200` 改为 `border-red-200 dark:border-red-800`，
`bg-amber-50` 改为 `bg-amber-50 dark:bg-amber-900/20`，`border-amber-200` 改为 `border-amber-200 dark:border-amber-800`。

**Step 2: 验证**

Run: 浏览器中切换到暗色模式，确认 Dashboard 页面所有元素正确显示暗色。

**Step 3: 提交**

```bash
git add app/templates/dashboard/index.html
git commit -m "feat: apply dark mode to dashboard template"
```

---

### Task 7: 更新其余模板暗色样式

**Files:**
- Modify: `app/templates/tasks/list.html`
- Modify: `app/templates/tasks/detail.html`
- Modify: `app/templates/tasks/form.html`
- Modify: `app/templates/locations/list.html`
- Modify: `app/templates/locations/detail.html`
- Modify: `app/templates/locations/form.html` (如果存在)
- Modify: `app/templates/data/index.html`

**Step 1: 对每个模板执行统一的暗色类替换规则**

通用替换规则（适用于所有模板）：
- `bg-white shadow-sm rounded-lg border border-gray-200` → `bg-white dark:bg-cc-card shadow-sm rounded-lg border border-gray-200 dark:border-cc-border`
- `text-gray-900` → `text-gray-900 dark:text-gray-100`
- `text-gray-800` → `text-gray-800 dark:text-gray-100`
- `text-gray-700` → `text-gray-700 dark:text-gray-300`
- `text-gray-600` → `text-gray-600 dark:text-gray-400`
- `text-gray-500` → `text-gray-500 dark:text-gray-400`
- `bg-gray-50` (在 thead 中) → `bg-gray-50 dark:bg-cc-bg`
- `border-gray-200` (在 hr/divider 中) → `border-gray-200 dark:border-cc-border`
- `border-gray-300` (在 input/select 中) → `border-gray-300 dark:border-cc-border`
- 输入框添加：`dark:bg-cc-bg dark:text-gray-200`

对任务列表模板 (`list.html`)：
- 表格外层 div 添加 `scale-on-hover`（给表格行）
- 目标日期的 `text-red-600` 改为 `text-red-600 dark:text-red-400`

对任务详情模板 (`detail.html`)：
- 给卡片添加 `scale-on-hover`
- 进度条的 `bg-gray-200` 改为 `bg-gray-200 dark:bg-gray-700`
- Task log 区域 `bg-gray-50` 改为 `bg-gray-50 dark:bg-gray-800`

对数据导入模板 (`data/index.html`)：
- 警告区域 `bg-yellow-50` 改为 `bg-yellow-50 dark:bg-yellow-900/20`

**Step 2: 验证**

Run: 逐一访问所有页面，在暗色模式下确认样式正确。

**Step 3: 提交**

```bash
git add app/templates/
git commit -m "feat: apply dark mode to all page templates"
```

---

## Phase 2: 交互升级 — HTMX 原地编辑 + 侧边抽屉

### Task 8: 添加 HTMX 局部更新路由（edit-field / save-field / drawer）

**Files:**
- Modify: `app/routes/tasks.py`

**Step 1: 在 tasks.py 末尾添加三个新路由**

在 `_parse_links` 函数之前添加：

```python
@bp.route("/<int:id>/edit-field")
def edit_field(id):
    """Return inline edit form fragment for HTMX."""
    task = Task.query.get_or_404(id)
    field = request.args.get("field")
    allowed = {"task_description", "comments"}
    if field not in allowed:
        return "", 400
    value = getattr(task, field) or ""
    return render_template("tasks/partials/edit_field.html", task=task, field=field, value=value)


@bp.route("/<int:id>/save-field", methods=["POST"])
def save_field(id):
    """Save inline edit and return display fragment for HTMX."""
    task = Task.query.get_or_404(id)
    field = request.form.get("field")
    allowed = {"task_description", "comments"}
    if field not in allowed:
        return "", 400
    setattr(task, field, request.form.get("value", ""))
    task.last_update = date.today()
    db.session.commit()
    return render_template("tasks/partials/display_field.html", task=task, field=field)


@bp.route("/<int:id>/drawer")
def drawer(id):
    """Return drawer content fragment for HTMX slide-over panel."""
    task = Task.query.get_or_404(id)
    assignments = task.assignments.order_by(TaskAssignment.id).all()
    return render_template(
        "tasks/partials/drawer.html", task=task, assignments=assignments,
        status_options=get_options("statuses"),
        local_status_options=get_options("local_statuses"),
    )
```

**Step 2: 创建 partials 目录**

```bash
mkdir -p app/templates/tasks/partials
```

**Step 3: 提交**

```bash
git add app/routes/tasks.py
git commit -m "feat: add HTMX inline edit and drawer routes to tasks"
```

---

### Task 9: 创建 HTMX 局部模板（partials）

**Files:**
- Create: `app/templates/tasks/partials/edit_field.html`
- Create: `app/templates/tasks/partials/display_field.html`
- Create: `app/templates/tasks/partials/drawer.html`
- Create: `app/templates/tasks/partials/status_badge.html`

**Step 1: 创建 edit_field.html**

```html
<form hx-post="{{ url_for('tasks.save_field', id=task.id) }}"
      hx-target="closest [data-field-container]"
      hx-swap="outerHTML"
      class="inline">
    <input type="hidden" name="field" value="{{ field }}">
    <textarea name="value" rows="4"
              class="w-full text-sm border border-blue-400 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200 dark:border-blue-600"
              autofocus>{{ value }}</textarea>
    <div class="flex gap-2 mt-1">
        <button type="submit" class="px-2 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700">Save</button>
        <button type="button" class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200"
                onclick="htmx.ajax('GET', '{{ url_for('tasks.detail', id=task.id) }}', {target: this.closest('[data-field-container]'), swap: 'outerHTML'})">Cancel</button>
    </div>
</form>
```

**Step 2: 创建 display_field.html**

```html
<div data-field-container class="group">
    <span class="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap cursor-pointer border-b border-dashed border-transparent hover:border-gray-400 dark:hover:border-gray-500"
          hx-get="{{ url_for('tasks.edit_field', id=task.id) }}?field={{ field }}"
          hx-target="closest [data-field-container]"
          hx-swap="outerHTML">
        {{ getattr(task, field) or '-' }}
    </span>
    <span class="ml-1 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">click to edit</span>
</div>
```

**Step 3: 创建 drawer.html**

```html
<div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-cc-border">
        <div>
            <h2 class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ task.task_name }}</h2>
            <div class="flex gap-2 mt-1">
                <span class="badge badge-{{ task.overall_status | lower | replace(' ', '-') }}">{{ task.overall_status }}</span>
                <span class="badge badge-{{ task.task_priority | lower }}">{{ task.task_priority }}</span>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <a href="{{ url_for('tasks.detail', id=task.id) }}" class="text-xs text-blue-600 dark:text-blue-400 hover:underline" target="_blank">Open full page</a>
            <button onclick="closeDrawer()" class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        </div>
    </div>

    <!-- Quick Info -->
    <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
            <span class="text-gray-500 dark:text-gray-400">Owner:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200 font-mono">{{ task.task_owner or '-' }}</span>
        </div>
        <div>
            <span class="text-gray-500 dark:text-gray-400">Target:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200 font-mono">{{ task.target_date.strftime('%Y-%m-%d') if task.target_date else '-' }}</span>
        </div>
        <div>
            <span class="text-gray-500 dark:text-gray-400">Scope:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200">{{ task.scope_country or 'All' }} / {{ task.scope_location_type or 'All' }}</span>
        </div>
        <div>
            <span class="text-gray-500 dark:text-gray-400">Execution:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200">{{ task.execution_model or '-' }}</span>
        </div>
    </div>

    <!-- Progress -->
    {% set ns = namespace(completed=0, in_progress=0, pending=0, blocked=0, na=0) %}
    {% for a in assignments %}
        {% if a.local_status == 'Completed' %}{% set ns.completed = ns.completed + 1 %}
        {% elif a.local_status == 'In Progress' %}{% set ns.in_progress = ns.in_progress + 1 %}
        {% elif a.local_status == 'Pending' %}{% set ns.pending = ns.pending + 1 %}
        {% elif a.local_status == 'Blocked' %}{% set ns.blocked = ns.blocked + 1 %}
        {% elif a.local_status == 'N/A' %}{% set ns.na = ns.na + 1 %}
        {% endif %}
    {% endfor %}
    {% if assignments | length > 0 %}
    {% set pct = (ns.completed / (assignments | length) * 100) | int %}
    <div>
        <div class="flex justify-between text-xs mb-1">
            <span class="text-gray-600 dark:text-gray-400">Progress {{ pct }}%</span>
            <span class="text-gray-500 dark:text-gray-500">{{ ns.completed }}/{{ assignments | length }} done</span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div class="bg-green-500 h-2 rounded-full transition-all duration-500" style="width: {{ pct }}%"></div>
        </div>
    </div>
    {% endif %}

    <!-- Assignments List -->
    <div>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">Locations ({{ assignments | length }})</h3>
        {% if assignments %}
        <div class="space-y-2 max-h-[50vh] overflow-y-auto">
            {% for a in assignments %}
            <div class="border border-gray-200 dark:border-cc-border rounded-lg p-3">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ a.location.location_name }}</span>
                    <span class="badge badge-{{ (a.local_status or 'pending') | lower | replace(' ', '-') }}">{{ a.local_status or 'Pending' }}</span>
                </div>
                {% if a.it_name %}
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ a.it_name }}</span>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p class="text-sm text-gray-500 dark:text-gray-400">No assignments.</p>
        {% endif %}
    </div>
</div>
```

**Step 4: 创建 status_badge.html（用于极速状态切换的局部替换）**

```html
<span class="badge badge-{{ status | lower | replace(' ', '-') }} cursor-pointer relative"
      hx-get="{{ url_for('tasks.status_menu', id=task_id) }}"
      hx-target="this"
      hx-swap="outerHTML">
    {{ status }}
</span>
```

**Step 5: 提交**

```bash
mkdir -p app/templates/tasks/partials
git add app/templates/tasks/partials/
git commit -m "feat: add HTMX partial templates for inline editing and drawer"
```

---

### Task 10: 在任务详情页集成原地编辑

**Files:**
- Modify: `app/templates/tasks/detail.html:59-60` (Description)
- Modify: `app/templates/tasks/detail.html:112-116` (Comments)

**Step 1: 替换描述字段为可点击编辑**

将 detail.html 中 Description 的 `<dd>` 改为：
```html
<dd class="text-sm text-gray-900 dark:text-gray-100 mt-1 whitespace-pre-wrap">
    {% include "tasks/partials/display_field.html" with context %}
</dd>
```

实际上需要在 detail.html 中用 `data-field-container` 包裹。将第 58-60 行：
```html
<div class="sm:col-span-2">
    <dt class="text-sm font-medium text-gray-500">Description</dt>
    <dd class="text-sm text-gray-900 mt-1 whitespace-pre-wrap">{{ task.task_description or '-' }}</dd>
</div>
```
改为：
```html
<div class="sm:col-span-2">
    <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Description</dt>
    <dd class="text-sm mt-1">
        <div data-field-container>
            <span class="text-gray-900 dark:text-gray-100 whitespace-pre-wrap cursor-pointer border-b border-dashed border-transparent hover:border-gray-400 dark:hover:border-gray-500"
                  hx-get="{{ url_for('tasks.edit_field', id=task.id) }}?field=task_description"
                  hx-target="closest [data-field-container]"
                  hx-swap="outerHTML">
                {{ task.task_description or '-' }}
            </span>
            <span class="ml-1 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity"></span>
        </div>
    </dd>
</div>
```

同样将 Comments（第 112-117 行）做类似处理，field 改为 `comments`。

**Step 2: 验证**

Run: 在任务详情页点击描述文字，确认弹出的 textarea 可以编辑并保存。

**Step 3: 提交**

```bash
git add app/templates/tasks/detail.html
git commit -m "feat: integrate click-to-edit on task description and comments"
```

---

### Task 11: 在任务列表集成侧边抽屉

**Files:**
- Modify: `app/templates/tasks/list.html:65-67`

**Step 1: 修改任务名称链接，点击打开抽屉**

将列表页中：
```html
<a href="{{ url_for('tasks.detail', id=task.id) }}" class="text-blue-600 hover:text-blue-800">{{ task.task_name }}</a>
```
改为：
```html
<a href="{{ url_for('tasks.detail', id=task.id) }}"
   class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
   onclick="event.preventDefault(); openDrawer('{{ url_for('tasks.drawer', id=task.id) }}')">
    {{ task.task_name }}
</a>
```

**Step 2: 验证**

Run: 在任务列表点击任务名，确认右侧滑出抽屉面板，显示任务信息。

**Step 3: 提交**

```bash
git add app/templates/tasks/list.html
git commit -m "feat: open slide-over drawer on task name click in list view"
```

---

### Task 12: 极速状态切换（HTMX 局部替换）

**Files:**
- Modify: `app/routes/tasks.py`
- Modify: `app/templates/tasks/list.html:71-78`
- Create: `app/templates/tasks/partials/status_menu.html`

**Step 1: 添加 status_menu 路由到 tasks.py**

在 `edit_field` 路由之前添加：

```python
@bp.route("/<int:id>/status-menu")
def status_menu(id):
    """Return status popup menu fragment for HTMX."""
    task = Task.query.get_or_404(id)
    return render_template("tasks/partials/status_menu.html", task=task, status_options=get_options("statuses"))
```

同时修改现有的 `update_status` 路由，让它支持 HTMX 请求返回片段：

```python
@bp.route("/<int:id>/status", methods=["POST"])
def update_status(id):
    task = Task.query.get_or_404(id)
    new_status = request.form.get("overall_status")
    if new_status in get_options("statuses"):
        task.overall_status = new_status
        task.last_update = date.today()
        db.session.commit()

    if request.headers.get("HX-Request"):
        return render_template("tasks/partials/status_menu.html", task=task, status_options=get_options("statuses"))

    return redirect(request.headers.get("Referer", url_for("tasks.list")))
```

**Step 2: 创建 status_menu.html**

```html
<div class="relative inline-block" onclick="event.stopPropagation()">
    <span class="badge badge-{{ task.overall_status | lower | replace(' ', '-') }} cursor-pointer"
          hx-get="{{ url_for('tasks.status_menu', id=task.id) }}"
          hx-target="closest .relative"
          hx-swap="outerHTML">
        {{ task.overall_status }}
    </span>
    <div class="absolute z-10 mt-1 left-0 bg-white dark:bg-cc-card border border-gray-200 dark:border-cc-border rounded-md shadow-lg py-1 min-w-[140px]">
        {% for s in status_options %}
        <button class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 {{ 'font-bold' if s == task.overall_status else '' }} {{ 'text-gray-900 dark:text-gray-100' if s == task.overall_status else 'text-gray-700 dark:text-gray-300' }}"
                hx-post="{{ url_for('tasks.update_status', id=task.id) }}"
                hx-vals='{"overall_status": "{{ s }}"}'
                hx-target="closest .relative"
                hx-swap="outerHTML">
            <span class="badge badge-{{ s | lower | replace(' ', '-') }} mr-1"></span>
            {{ s }}
        </button>
        {% endfor %}
    </div>
</div>
```

**Step 3: 替换列表页的状态列**

将 list.html 中第 71-78 行的 `<td>` 内容（包含 form + select）替换为：

```html
<td class="px-4 py-3 text-sm">
    {% include "tasks/partials/status_menu.html" with context %}
</td>
```

注意：需要在循环内让 `task` 变量可用。所以 status_menu.html 中的变量名需要与循环变量一致。此处已用 `task` 命名，与循环 `{% for task in tasks.items %}` 一致。

**Step 4: 验证**

Run: 在任务列表点击状态 badge，确认弹出状态选择菜单，点击新状态后 badge 更新。

**Step 5: 提交**

```bash
git add app/routes/tasks.py app/templates/tasks/list.html app/templates/tasks/partials/status_menu.html
git commit -m "feat: quick status switch popup on task list using HTMX"
```

---

## Phase 3: 看板视图 + 进度链 + 搜索动效

### Task 13: 添加看板路由

**Files:**
- Modify: `app/routes/tasks.py`

**Step 1: 添加 kanban 路由**

在 `list` 路由之后添加：

```python
@bp.route("/kanban")
def kanban():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    columns = {}
    for s in get_options("statuses"):
        columns[s] = [t for t in tasks if t.overall_status == s]
    return render_template("tasks/kanban.html", columns=columns)
```

**Step 2: 提交**

```bash
git add app/routes/tasks.py
git commit -m "feat: add kanban view route"
```

---

### Task 14: 创建看板模板

**Files:**
- Create: `app/templates/tasks/kanban.html`

**Step 1: 创建 kanban.html**

```html
{% extends "base.html" %}

{% block title %}Kanban - APAC Task Manager{% endblock %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Kanban Board</h1>
        <div class="flex gap-2">
            <a href="{{ url_for('tasks.list') }}" class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-cc-card border border-gray-300 dark:border-cc-border rounded-md hover:bg-gray-50 dark:hover:bg-gray-700">List View</a>
            <a href="{{ url_for('tasks.create') }}" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">New Task</a>
        </div>
    </div>

    <div class="flex gap-4 overflow-x-auto pb-4" id="kanban-board">
        {% for status, tasks in columns.items() %}
        <div class="flex-shrink-0 w-72">
            <div class="bg-gray-100 dark:bg-cc-bg rounded-lg p-3">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
                        <span class="badge badge-{{ status | lower | replace(' ', '-') }}">{{ status }}</span>
                    </h3>
                    <span class="text-xs text-gray-500 dark:text-gray-400">{{ tasks | length }}</span>
                </div>
                <div class="space-y-2 min-h-[200px] kanban-column" data-status="{{ status }}">
                    {% for task in tasks %}
                    <div class="bg-white dark:bg-cc-card rounded-lg p-3 shadow-sm border border-gray-200 dark:border-cc-border cursor-grab scale-on-hover"
                         data-task-id="{{ task.id }}">
                        <div class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2"
                             onclick="openDrawer('{{ url_for('tasks.drawer', id=task.id) }}')">
                            {{ task.task_name }}
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="badge badge-{{ task.task_priority | lower }}">{{ task.task_priority }}</span>
                            {% if task.target_date %}
                            <span class="text-xs text-gray-500 dark:text-gray-400 font-mono">{{ task.target_date.strftime('%m/%d') }}</span>
                            {% endif %}
                        </div>
                        <!-- Progress Chain -->
                        {% set assignments = task.assignments.all() %}
                        {% if assignments %}
                        <div class="mt-2 flex flex-wrap gap-0.5">
                            {% for a in assignments %}
                            <span class="progress-dot progress-dot-{{ (a.local_status or 'pending') | lower | replace(' ', '-') | replace('/', '') }}"
                                  title="{{ a.location.location_name }}: {{ a.local_status or 'Pending' }}"></span>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.kanban-column').forEach(function(col) {
        new Sortable(col, {
            group: 'kanban',
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            animation: 200,
            onEnd: function(evt) {
                var taskId = evt.item.dataset.taskId;
                var newStatus = evt.to.dataset.status;
                htmx.ajax('POST', '/tasks/' + taskId + '/status', {
                    values: { overall_status: newStatus },
                    target: 'body',
                    swap: 'none'
                });
            }
        });
    });
});
</script>
{% endblock %}
```

**Step 2: 提交**

```bash
git add app/templates/tasks/kanban.html
git commit -m "feat: add kanban board template with Sortable.js drag-and-drop"
```

---

### Task 15: 在导航栏添加看板入口

**Files:**
- Modify: `app/templates/base.html:22-26`

**Step 1: 在 Tasks 导航链接之后添加 Kanban 链接**

在 `<a href="/tasks" ...>Tasks</a>` 之后插入：
```html
<a href="/tasks/kanban" class="nav-link {% if '/kanban' in request.path %}text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400{% else %}text-gray-600 dark:text-gray-400{% endif %} inline-flex items-center px-1 pt-1 text-sm font-medium hover:text-blue-600 dark:hover:text-blue-400">Kanban</a>
```

**Step 2: 提交**

```bash
git add app/templates/base.html
git commit -m "feat: add Kanban link to navigation bar"
```

---

### Task 16: 在任务列表页添加进度链

**Files:**
- Modify: `app/templates/tasks/list.html`

**Step 1: 在任务表格的任务名列中添加进度链**

在任务名称链接之后（`</a>` 后面），添加进度链：

```html
{% set task_assignments = task.assignments.all() %}
{% if task_assignments %}
<div class="mt-1 flex flex-wrap gap-0.5">
    {% for a in task_assignments %}
    <span class="progress-dot progress-dot-{{ (a.local_status or 'pending') | lower | replace(' ', '-') | replace('/', '') }}"
          title="{{ a.location.location_name }}"></span>
    {% endfor %}
</div>
{% endif %}
```

**Step 2: 提交**

```bash
git add app/templates/tasks/list.html
git commit -m "feat: add progress chain dots to task list rows"
```

---

### Task 17: 实时搜索动效

**Files:**
- Modify: `app/templates/tasks/list.html:19-45` (搜索区域)
- Modify: `app/routes/tasks.py` (添加 search 片段路由)

**Step 1: 修改搜索表单为 HTMX 实时搜索**

将搜索表单的 `<form method="get">` 改为 HTMX 驱动：
```html
<form hx-get="{{ url_for('tasks.list') }}" hx-target="#task-table-body" hx-swap="innerHTML" hx-indicator="#search-spinner" class="flex flex-wrap items-center gap-3">
```

给搜索 input 添加 `hx-trigger="keyup changed delay:300ms, search"` 属性。

给表格的 `<tbody>` 添加 `id="task-table-body"`。

**Step 2: 修改 list 路由支持 HTMX 请求**

在 tasks.py 的 `list()` 函数末尾，如果检测到 HTMX 请求，只返回表格行片段：

```python
@bp.route("/")
def list():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    query = Task.query
    if search:
        query = query.filter(
            db.or_(
                Task.task_name.ilike(f"%{search}%"),
                Task.task_description.ilike(f"%{search}%"),
            )
        )
    if status:
        query = query.filter_by(overall_status=status)
    if priority:
        query = query.filter_by(task_priority=priority)

    tasks = query.order_by(Task.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    if request.headers.get("HX-Request"):
        return render_template(
            "tasks/partials/task_rows.html", tasks=tasks, today=date.today(),
            status_options=get_options("statuses"),
        )

    return render_template(
        "tasks/list.html",
        tasks=tasks, search=search, status=status, priority=priority,
        status_options=get_options("statuses"), priority_options=get_options("priorities"),
        today=date.today(),
    )
```

**Step 3: 创建 task_rows.html 局部模板**

```html
{% for task in tasks.items %}
<tr class="table-row-hover animate-row-enter">
    <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
        <a href="{{ url_for('tasks.detail', id=task.id) }}"
           class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
           onclick="event.preventDefault(); openDrawer('{{ url_for('tasks.drawer', id=task.id) }}')">
            {{ task.task_name }}
        </a>
        {% set task_assignments = task.assignments.all() %}
        {% if task_assignments %}
        <div class="mt-1 flex flex-wrap gap-0.5">
            {% for a in task_assignments %}
            <span class="progress-dot progress-dot-{{ (a.local_status or 'pending') | lower | replace(' ', '-') | replace('/', '') }}"
                  title="{{ a.location.location_name }}"></span>
            {% endfor %}
        </div>
        {% endif %}
    </td>
    <td class="px-4 py-3 text-sm">
        <span class="badge badge-{{ task.task_priority | lower }}">{{ task.task_priority }}</span>
    </td>
    <td class="px-4 py-3 text-sm">
        <!-- Status menu partial will be loaded here -->
    </td>
    <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{{ task.task_owner or '-' }}</td>
    <td class="px-4 py-3 text-sm">
        {% if task.target_date %}
            {% set is_overdue = task.target_date < today and task.overall_status not in ['Completed', 'Cancelled'] %}
            <span class="{{ 'text-red-600 dark:text-red-400 font-semibold' if is_overdue else 'text-gray-600 dark:text-gray-400' }} font-mono">
                {{ task.target_date.strftime('%Y-%m-%d') }}
            </span>
        {% else %}
            <span class="text-gray-400">-</span>
        {% endif %}
    </td>
    <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
        {% set fl = task.file_links %}
        {% set ml = task.mail_links %}
        {% if fl or ml %}{{ (fl | length) + (ml | length) }}{% else %}-{% endif %}
    </td>
    <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
        {{ task.scope_type }}
    </td>
    <td class="px-4 py-3 text-sm text-right space-x-1">
        <a href="{{ url_for('tasks.detail', id=task.id) }}" class="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 rounded hover:bg-blue-100">Detail</a>
        <a href="{{ url_for('tasks.edit', id=task.id) }}" class="inline-flex items-center px-2 py-1 text-xs font-medium text-yellow-700 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/30 rounded hover:bg-yellow-100">Edit</a>
    </td>
</tr>
{% else %}
<tr>
    <td colspan="8" class="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">No tasks match your search.</td>
</tr>
{% endfor %}
```

**Step 4: 提交**

```bash
git add app/routes/tasks.py app/templates/tasks/list.html app/templates/tasks/partials/task_rows.html
git commit -m "feat: add HTMX live search with animation effects"
```

---

### Task 18: 最终验证和清理

**Step 1: 全页面验证**

Run: 启动应用 `cd /home/ubuntu/my-repos/dotTask && .venv/bin/python run.py`

逐一测试：
- 暗色/浅色主题切换正常
- Dashboard 所有图表在暗色下可读
- 任务列表：抽屉打开/关闭、状态切换、搜索动效
- 任务详情：原地编辑描述和备注
- 看板视图：拖拽改状态、进度链显示
- 数据导入/导出页面暗色正常

**Step 2: 修复发现的问题**

**Step 3: 最终提交**

```bash
git add -A
git commit -m "feat: Command Center UI upgrade complete - dark theme, inline editing, drawer, kanban"
```
