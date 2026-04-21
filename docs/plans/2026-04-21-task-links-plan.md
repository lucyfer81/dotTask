# Task Links 多值链接实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Task 的 link_to_file 和 link_to_mail 从单 URL 字段改造为支持多个命名链接的 JSON 字段。

**Architecture:** 在现有数据库列中存储 JSON 数组，通过模型属性封装序列化/反序列化，前端用动态表单组交互，详情页显示为可点击文字链接，列表页显示数量摘要。

**Tech Stack:** Flask, SQLAlchemy, SQLite, Jinja2, Tailwind CSS, 原生 JavaScript

**注意:** 项目无测试基础设施，使用手动启动 Flask 应用验证。

---

### Task 1: 修改 Task 模型

**Files:**
- Modify: `app/models.py:1-62`

**Step 1: 添加 json import 并修改列类型和属性**

在 `app/models.py` 顶部添加 `import json`。将 `link_to_file` 和 `link_to_mail` 的列类型从 `db.String(500)` 改为 `db.Text`。添加 `file_links` 和 `mail_links` 属性封装 JSON 序列化/反序列化。

修改后的 Task 模型关键部分：

```python
import json
from datetime import datetime, timezone
from app import db

# ... Location model unchanged ...

class Task(db.Model):
    __tablename__ = "task_master"

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(300), nullable=False)
    task_source = db.Column(db.String(200))
    stakeholder = db.Column(db.String(200))
    task_description = db.Column(db.Text)
    scope_country = db.Column(db.String(100))
    scope_location_type = db.Column(db.String(50))
    task_owner = db.Column(db.String(200))
    execution_model = db.Column(db.String(200))
    overall_status = db.Column(db.String(50), default="Not Started")
    start_date = db.Column(db.Date)
    target_date = db.Column(db.Date)
    last_update = db.Column(db.Date)
    link_to_file = db.Column(db.Text)
    link_to_mail = db.Column(db.Text)
    task_priority = db.Column(db.String(50), default="Medium")
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    assignments = db.relationship("TaskAssignment", backref="task", lazy="dynamic",
                                  cascade="all, delete-orphan")

    @property
    def file_links(self):
        """Return parsed list of {"name": ..., "url": ...} dicts."""
        if self.link_to_file:
            try:
                return json.loads(self.link_to_file)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @file_links.setter
    def file_links(self, value):
        self.link_to_file = json.dumps(value, ensure_ascii=False) if value else None

    @property
    def mail_links(self):
        """Return parsed list of {"name": ..., "url": ...} dicts."""
        if self.link_to_mail:
            try:
                return json.loads(self.link_to_mail)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @mail_links.setter
    def mail_links(self, value):
        self.link_to_mail = json.dumps(value, ensure_ascii=False) if value else None

    def __repr__(self):
        return f"<Task {self.task_name}>"
```

**Step 2: 验证应用启动**

Run: `cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "from app import create_app; app = create_app(); print('OK')"`
Expected: 输出 `OK`，无报错。

**Step 3: Commit**

```bash
git add app/models.py
git commit -m "feat: add JSON-based multi-link support to Task model"
```

---

### Task 2: 修改路由处理 JSON 链接数据

**Files:**
- Modify: `app/routes/tasks.py:46-83` (create)
- Modify: `app/routes/tasks.py:104-132` (edit)

**Step 1: 添加 helper 函数并修改 create 和 edit 路由**

在 `app/routes/tasks.py` 中添加 `_parse_links` helper，修改 create 和 edit 路由以处理 JSON 链接数据。

在 `_parse_date` 函数后面添加：

```python
def _parse_links(json_str):
    """Parse JSON links string into list of {"name": ..., "url": ...} dicts.
    Filter out entries with empty url."""
    if not json_str:
        return []
    try:
        links = json.loads(json_str)
        return [l for l in links if l.get("url", "").strip()]
    except (json.JSONDecodeError, TypeError):
        return []
```

在文件顶部 imports 中添加 `import json`。

修改 create 路由（约第 62-63 行），将：
```python
            link_to_file=request.form.get("link_to_file", ""),
            link_to_mail=request.form.get("link_to_mail", ""),
```
替换为：
```python
            link_to_file=json.dumps(_parse_links(request.form.get("file_links_json", "")), ensure_ascii=False) or None,
            link_to_mail=json.dumps(_parse_links(request.form.get("mail_links_json", "")), ensure_ascii=False) or None,
```

修改 edit 路由（约第 120-121 行），将：
```python
        task.link_to_file = request.form.get("link_to_file", "")
        task.link_to_mail = request.form.get("link_to_mail", "")
```
替换为：
```python
        task.link_to_file = json.dumps(_parse_links(request.form.get("file_links_json", "")), ensure_ascii=False) or None
        task.link_to_mail = json.dumps(_parse_links(request.form.get("mail_links_json", "")), ensure_ascii=False) or None
```

**Step 2: 验证应用启动**

Run: `cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "from app import create_app; app = create_app(); print('OK')"`
Expected: 输出 `OK`。

**Step 3: Commit**

```bash
git add app/routes/tasks.py
git commit -m "feat: update task routes to handle JSON link data"
```

---

### Task 3: 修改表单模板 — 动态链接表单组

**Files:**
- Modify: `app/templates/tasks/form.html:134-156`

**Step 1: 替换 Links & Comments 区块**

将 `form.html` 的 Links & Comments 区块（第 134-156 行）替换为动态链接表单组。需要：
- 邮件链接：动态添加/删除行（名称 + URL）
- 文档链接：动态添加/删除行（名称 + URL）
- 隐藏字段 `mail_links_json` 和 `file_links_json` 传递 JSON
- 编辑模式下回填已有链接数据

替换整个 `<!-- Links & Comments -->` 区块为：

```html
        <!-- Links & Comments -->
        <div class="mb-6">
            <h2 class="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">Links & Comments</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Email Links -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Email Links</label>
                    <div id="mail-links-container" class="space-y-2">
                        <!-- Dynamic rows inserted here -->
                    </div>
                    <button type="button" onclick="addMailLinkRow()"
                        class="mt-2 inline-flex items-center px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">
                        + Add Email
                    </button>
                    <input type="hidden" id="mail_links_json" name="mail_links_json" value="">
                </div>
                <!-- File Links -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">File Links</label>
                    <div id="file-links-container" class="space-y-2">
                        <!-- Dynamic rows inserted here -->
                    </div>
                    <button type="button" onclick="addFileLinkRow()"
                        class="mt-2 inline-flex items-center px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">
                        + Add File
                    </button>
                    <input type="hidden" id="file_links_json" name="file_links_json" value="">
                </div>
                <div class="md:col-span-2">
                    <label for="comments" class="block text-sm font-medium text-gray-700 mb-1">Comments</label>
                    <textarea id="comments" name="comments" rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">{{ task.comments if task else '' }}</textarea>
                </div>
            </div>
        </div>
```

**Step 2: 在 extra_js block 中添加链接管理 JavaScript**

在 `{% block extra_js %}` 的 `<script>` 标签开头（loadLocations 函数之前）添加链接管理代码：

```javascript
    // ===== Dynamic Link Rows =====
    const MAIL_ROW_HTML = (name, url) => `
        <div class="link-row flex items-center gap-2">
            <input type="text" placeholder="Email name" value="${name}"
                class="link-name flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500">
            <input type="url" placeholder="https://outlook.office.com/..." value="${url}"
                class="link-url flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500">
            <button type="button" onclick="this.parentElement.remove()"
                class="px-2 py-1.5 text-red-600 hover:text-red-800 text-sm">&times;</button>
        </div>`;

    const FILE_ROW_HTML = (name, url) => `
        <div class="link-row flex items-center gap-2">
            <input type="text" placeholder="File name" value="${name}"
                class="link-name flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500">
            <input type="url" placeholder="https://onedrive.live.com/..." value="${url}"
                class="link-url flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500">
            <button type="button" onclick="this.parentElement.remove()"
                class="px-2 py-1.5 text-red-600 hover:text-red-800 text-sm">&times;</button>
        </div>`;

    function addMailLinkRow(name = '', url = '') {
        document.getElementById('mail-links-container').insertAdjacentHTML('beforeend', MAIL_ROW_HTML(escapeHtml(name), escapeHtml(url)));
    }

    function addFileLinkRow(name = '', url = '') {
        document.getElementById('file-links-container').insertAdjacentHTML('beforeend', FILE_ROW_HTML(escapeHtml(name), escapeHtml(url)));
    }

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function collectLinks(containerId) {
        const rows = document.querySelectorAll(`#${containerId} .link-row`);
        const links = [];
        rows.forEach(row => {
            const name = row.querySelector('.link-name').value.trim();
            const url = row.querySelector('.link-url').value.trim();
            if (url) links.push({name: name || url, url: url});
        });
        return links;
    }

    // Sync hidden fields before form submit
    document.querySelector('form').addEventListener('formdata', function(e) {
        const mailLinks = collectLinks('mail-links-container');
        const fileLinks = collectLinks('file-links-container');
        e.formData.set('mail_links_json', mailLinks.length ? JSON.stringify(mailLinks) : '');
        e.formData.set('file_links_json', fileLinks.length ? JSON.stringify(fileLinks) : '');
    });

    // Load existing links for edit mode
    {% if task %}
    {% if task.link_to_mail %}
    try {
        const existingMails = {{ task.link_to_mail | safe }};
        existingMails.forEach(l => addMailLinkRow(l.name, l.url));
    } catch(e) {}
    {% endif %}
    {% if task.link_to_file %}
    try {
        const existingFiles = {{ task.link_to_file | safe }};
        existingFiles.forEach(l => addFileLinkRow(l.name, l.url));
    } catch(e) {}
    {% endif %}
    {% endif %}

    // Always start with at least one empty row if no existing data
    if (!document.querySelector('#mail-links-container .link-row')) addMailLinkRow();
    if (!document.querySelector('#file-links-container .link-row')) addFileLinkRow();
```

**Step 3: 启动应用手动验证**

Run: `cd /home/ubuntu/my-repos/dotTask && .venv/bin/flask --app app run --port 5001`

验证：
1. 打开浏览器访问 `/tasks/new`，确认邮件链接和文档链接区域各有一个空的输入行
2. 点击 "+ Add Email" 和 "+ Add File" 按钮，确认能动态添加新行
3. 点击 × 按钮确认能删除行
4. 编辑已有任务时确认能正确回填数据

**Step 4: Commit**

```bash
git add app/templates/tasks/form.html
git commit -m "feat: dynamic link form groups for email and file URLs"
```

---

### Task 4: 修改详情页模板 — 显示链接列表

**Files:**
- Modify: `app/templates/tasks/detail.html:78-89`

**Step 1: 替换详情页的链接显示**

将 `detail.html` 中第 78-89 行的文件链接和邮件链接显示替换为多链接列表：

替换：
```html
                    {% if task.link_to_file %}
                    <div>
                        <dt class="text-sm font-medium text-gray-500">File Link</dt>
                        <dd class="text-sm mt-1"><a href="{{ task.link_to_file }}" target="_blank" class="text-blue-600 hover:text-blue-800">{{ task.link_to_file }}</a></dd>
                    </div>
                    {% endif %}
                    {% if task.link_to_mail %}
                    <div>
                        <dt class="text-sm font-medium text-gray-500">Email Link</dt>
                        <dd class="text-sm mt-1"><a href="{{ task.link_to_mail }}" target="_blank" class="text-blue-600 hover:text-blue-800">{{ task.link_to_mail }}</a></dd>
                    </div>
                    {% endif %}
```

替换为：
```html
                    {% set file_links = task.file_links %}
                    {% if file_links %}
                    <div>
                        <dt class="text-sm font-medium text-gray-500">File Links</dt>
                        <dd class="text-sm mt-1 space-y-1">
                            {% for link in file_links %}
                            <a href="{{ link.url }}" target="_blank" rel="noopener"
                               class="flex items-center gap-1 text-blue-600 hover:text-blue-800">
                                <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                                </svg>
                                {{ link.name }}
                            </a>
                            {% endfor %}
                        </dd>
                    </div>
                    {% endif %}
                    {% set mail_links = task.mail_links %}
                    {% if mail_links %}
                    <div>
                        <dt class="text-sm font-medium text-gray-500">Email Links</dt>
                        <dd class="text-sm mt-1 space-y-1">
                            {% for link in mail_links %}
                            <a href="{{ link.url }}" target="_blank" rel="noopener"
                               class="flex items-center gap-1 text-blue-600 hover:text-blue-800">
                                <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                                </svg>
                                {{ link.name }}
                            </a>
                            {% endfor %}
                        </dd>
                    </div>
                    {% endif %}
```

**Step 2: 启动应用验证**

创建一个带有链接的测试任务，然后查看详情页确认链接正确显示为可点击的文字链接，带邮件/文件图标。

**Step 3: Commit**

```bash
git add app/templates/tasks/detail.html
git commit -m "feat: display multi-links with icons on task detail page"
```

---

### Task 5: 修改列表页模板 — 显示链接数量摘要

**Files:**
- Modify: `app/templates/tasks/list.html:50-58` (表头)
- Modify: `app/templates/tasks/list.html:61-103` (表体行)

**Step 1: 在列表表头添加 Links 列**

在 `list.html` 表头的 Target Date 列后面（第 56 行后）添加一列：

```html
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Links</th>
```

同时更新空数据行的 colspan 从 7 改为 8：
```html
<td colspan="8" ...>
```

**Step 2: 在表体行中添加链接摘要**

在 Target Date 的 `<td>` 后面、Scope 列前面，添加：

```html
                        <td class="px-4 py-3 text-sm text-gray-600">
                            {% set fl = task.file_links %}
                            {% set ml = task.mail_links %}
                            {% if fl or ml %}
                                <div class="flex items-center gap-2 flex-wrap">
                                    {% if ml %}
                                    <span class="inline-flex items-center gap-1 text-xs" title="{% for l in ml %}{{ l.name }}
{% endfor %}">
                                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                                        </svg>
                                        {{ ml | length }}
                                    </span>
                                    {% endif %}
                                    {% if fl %}
                                    <span class="inline-flex items-center gap-1 text-xs" title="{% for l in fl %}{{ l.name }}
{% endfor %}">
                                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                                        </svg>
                                        {{ fl | length }}
                                    </span>
                                    {% endif %}
                                </div>
                            {% else %}
                                -
                            {% endif %}
                        </td>
```

**Step 3: 启动应用验证**

在列表页确认带链接的任务显示邮件和文档的数量图标，hover 显示名称列表。无链接的任务显示 `-`。

**Step 4: Commit**

```bash
git add app/templates/tasks/list.html
git commit -m "feat: show link count summary with icons in task list"
```

---

### Task 6: 适配 Excel 导入导出

**Files:**
- Modify: `app/services/excel_service.py:26-41` (export)
- Modify: `app/services/excel_service.py:91-119` (import)

**Step 1: 修改导出逻辑**

将 `excel_service.py` 中导出部分的 `t.link_to_file` 和 `t.link_to_mail`（约第 40 行）改为可读格式：

将：
```python
            t.link_to_file, t.link_to_mail, t.task_priority, t.comments,
```
替换为：
```python
            t.link_to_file or "", t.link_to_mail or "", t.task_priority, t.comments,
```

（导出保持 JSON 原文即可，Excel 中完整保留数据。）

**Step 2: 修改导入逻辑**

将导入部分（约第 112-113 行）的：
```python
                    link_to_file=str(row[14] or ""),
                    link_to_mail=str(row[15] or ""),
```
替换为：
```python
                    link_to_file=str(row[14]) if row[14] else None,
                    link_to_mail=str(row[15]) if row[15] else None,
```

这样导入时保留 JSON 原文或设为 None。

**Step 3: 验证应用启动**

Run: `cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "from app import create_app; app = create_app(); print('OK')"`

**Step 4: Commit**

```bash
git add app/services/excel_service.py
git commit -m "feat: adapt excel import/export for JSON link format"
```

---

### Task 7: 端到端手动验证

**Step 1: 启动 Flask 开发服务器**

Run: `cd /home/ubuntu/my-repos/dotTask && .venv/bin/flask --app app run --port 5001`

**Step 2: 验证创建流程**

1. 访问 `/tasks/new`
2. 填写基本字段
3. 添加 2 个邮件链接（输入名称和 URL）
4. 添加 2 个文档链接（输入名称和 URL）
5. 点击 Save
6. 确认跳转到详情页且链接正确显示

**Step 3: 验证编辑流程**

1. 在详情页点击 Edit
2. 确认已有链接被正确回填到表单
3. 添加一个新链接，删除一个已有链接
4. Save 并确认变更生效

**Step 4: 验证列表显示**

1. 返回任务列表
2. 确认链接数量摘要正确显示
3. Hover 确认 tooltip 显示链接名称

**Step 5: 最终 Commit（如有修正）**

```bash
git add -A
git commit -m "fix: adjustments from end-to-end testing"
```
