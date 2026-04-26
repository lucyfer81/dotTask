# IT Person 下拉选择 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 task 分配给 location 时的 IT Person 字段从手动输入改为从 location 的 IT Contacts 下拉选择（保留手动输入选项）。

**Architecture:** 纯 Alpine.js 前端实现。用一个共享的 `itPersonSelect()` Alpine 组件处理下拉/输入切换。后端仅需在 task detail 视图传递 location contacts 映射。

**Tech Stack:** Alpine.js, Jinja2, Flask

---

### Task 1: 后端 — 传递 location contacts 映射到 task detail 模板

**Files:**
- Modify: `app/routes/tasks.py:118-141` (detail 视图)

**Step 1: 修改 tasks.py detail() 视图**

在 `detail()` 视图中构建 `location_contacts_map`（location_id → contacts 列表），传给模板。

```python
# tasks.py detail() — 在 return render_template 之前添加:
location_contacts_map = {}
for loc in unassigned_locations:
    location_contacts_map[loc.id] = loc.contacts
for a in assignments:
    location_contacts_map[a.location_id] = a.location.contacts
```

然后在 `render_template` 中加入 `location_contacts_map=location_contacts_map`。

**Step 2: 重启服务，验证页面不报错**

Run: `bash taskmgr.sh restart`
浏览器打开任意 task detail 页，确认无 500 错误。

**Step 3: Commit**

```bash
git add app/routes/tasks.py
git commit -m "feat: pass location contacts map to task detail template"
```

---

### Task 2: 前端 — Location 详情页 "Add Task" 表单

**Files:**
- Modify: `app/templates/locations/detail.html:196-200`

**Step 1: 替换 IT Person 输入为下拉选择**

将第 196-200 行的纯文本输入替换为 Alpine.js 下拉组件。Location 已知，直接使用 `location.contacts`。

在页面底部 `extra_js` block 中添加 `itPersonSelect` 组件函数。

**Add Task 表单** — 替换 IT Person 部分（约 line 196-200）：

```html
<div x-data="itPersonSelect({
    contacts: {{ location.contacts | tojson }},
    currentName: ''
})">
    <label class="block text-xs font-medium text-gray-500 dark:text-gray-300 mb-1">IT Person</label>
    <input type="hidden" name="it_name" :value="selectedName">
    <input type="hidden" name="it_role" :value="selectedRole">
    <template x-if="contacts.length > 0 && !showManual">
        <select @change="onSelect($event)"
            class="text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
            <option value="">-- Select IT Person --</option>
            <template x-for="c in contacts" :key="c.name">
                <option :value="c.name" x-text="c.name"></option>
            </template>
            <option value="__other__">-- 手动输入 --</option>
        </select>
    </template>
    <template x-if="contacts.length === 0 || showManual">
        <input type="text" x-model="selectedName" placeholder="Optional"
            class="text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
    </template>
</div>
```

**extra_js block** — 在 `</script>` 前添加 `itPersonSelect` 函数：

```javascript
function itPersonSelect(config) {
    return {
        contacts: config.contacts || [],
        currentName: config.currentName || '',
        selectedName: config.currentName || '',
        selectedRole: '',
        showManual: false,
        init() {
            if (this.currentName) {
                var match = this.contacts.find(function(c) { return c.name === this.currentName; }.bind(this));
                if (match) {
                    this.selectedRole = match.role || '';
                } else if (this.contacts.length > 0) {
                    this.showManual = true;
                }
            }
        },
        onSelect(event) {
            var val = event.target.value;
            if (val === '__other__') {
                this.showManual = true;
                this.selectedName = '';
                this.selectedRole = '';
            } else {
                this.selectedName = val;
                var contact = this.contacts.find(function(c) { return c.name === val; });
                this.selectedRole = contact ? (contact.role || '') : '';
            }
        }
    };
}
```

**Step 2: 重启服务，打开 location detail 页，验证 "Add Task" 表单**

确认：有联系人时显示下拉，无联系人时显示文本输入，选中"手动输入"切换为文本框。

**Step 3: Commit**

```bash
git add app/templates/locations/detail.html
git commit -m "feat: IT Person dropdown in location detail Add Task form"
```

---

### Task 3: 前端 — Location 详情页 "Update Assignment" 表单

**Files:**
- Modify: `app/templates/locations/detail.html:156-160`

**Step 1: 替换 Update Assignment 中的 IT Person 输入**

将 line 156-160 的文本输入替换为下拉组件，回显当前 `assignment.it_name`。

```html
<div x-data="itPersonSelect({
    contacts: {{ location.contacts | tojson }},
    currentName: '{{ assignment.it_name or '' }}'
})">
    <label class="block text-xs font-medium text-gray-500 dark:text-gray-300 mb-1">IT Person</label>
    <input type="hidden" name="it_name" :value="selectedName">
    <input type="hidden" name="it_role" :value="selectedRole">
    <template x-if="contacts.length > 0 && !showManual">
        <select @change="onSelect($event)"
            class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
            <option value="">-- Select IT Person --</option>
            <template x-for="c in contacts" :key="c.name">
                <option :value="c.name" x-text="c.name" :selected="c.name === currentName"></option>
            </template>
            <option value="__other__">-- 手动输入 --</option>
        </select>
    </template>
    <template x-if="contacts.length === 0 || showManual">
        <input type="text" x-model="selectedName" placeholder="Optional"
            class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
    </template>
</div>
```

**Step 2: 验证 Update Assignment 表单**

打开有 assignment 的 location detail，展开某 assignment 的更新表单，确认 IT Person 下拉正确回显当前值。

**Step 3: Commit**

```bash
git add app/templates/locations/detail.html
git commit -m "feat: IT Person dropdown in location detail Update Assignment form"
```

---

### Task 4: 前端 — Task 详情页 "Add Location" 表单（动态联动）

**Files:**
- Modify: `app/templates/tasks/detail.html:228-248`

**Step 1: 在 extra_js block 中添加 addLocationForm 组件**

```javascript
function addLocationForm(config) {
    return {
        locationContacts: config.locationContacts || {},
        currentContacts: [],
        selectedName: '',
        selectedRole: '',
        showManual: false,
        onLocationChange(event) {
            var locId = event.target.value;
            this.currentContacts = this.locationContacts[locId] || [];
            this.selectedName = '';
            this.selectedRole = '';
            this.showManual = false;
        },
        onContactSelect(event) {
            var val = event.target.value;
            if (val === '__other__') {
                this.showManual = true;
                this.selectedName = '';
                this.selectedRole = '';
            } else {
                this.selectedName = val;
                var contact = this.currentContacts.find(function(c) { return c.name === val; });
                this.selectedRole = contact ? (contact.role || '') : '';
            }
        }
    };
}
```

**Step 2: 替换 "Add Location" 表单**

将 line 231-248 的整个 form 用 `addLocationForm` 包裹，location select 联动 IT Person 下拉：

```html
<form method="post" action="{{ url_for('tasks.assign_location', id=task.id) }}"
      class="flex flex-wrap items-end gap-3"
      x-data="addLocationForm({ locationContacts: {{ location_contacts_map | tojson }} })">
    <div class="flex-1 min-w-[200px]">
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-300 mb-1">Select Location</label>
        <select name="location_id" required @change="onLocationChange($event)"
            class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
            <option value="">-- Select Location --</option>
            {% for loc in unassigned_locations %}
            <option value="{{ loc.id }}">{{ loc.location_name }}</option>
            {% endfor %}
        </select>
    </div>
    <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-300 mb-1">IT Person</label>
        <input type="hidden" name="it_name" :value="selectedName">
        <input type="hidden" name="it_role" :value="selectedRole">
        <template x-if="currentContacts.length > 0 && !showManual">
            <select @change="onContactSelect($event)"
                class="text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                <option value="">-- Select IT Person --</option>
                <template x-for="c in currentContacts" :key="c.name">
                    <option :value="c.name" x-text="c.name"></option>
                </template>
                <option value="__other__">-- 手动输入 --</option>
            </select>
        </template>
        <template x-if="currentContacts.length === 0 || showManual">
            <input type="text" x-model="selectedName" placeholder="Optional"
                class="text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
        </template>
    </div>
    <button type="submit" class="px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700">Assign</button>
</form>
```

**Step 3: 验证动态联动**

打开 task detail 页，选不同 location，确认 IT Person 下拉随 location 变化。

**Step 4: Commit**

```bash
git add app/templates/tasks/detail.html
git commit -m "feat: dynamic IT Person dropdown in task detail Add Location form"
```

---

### Task 5: 前端 — Task 详情页 "Update Assignment" 表单

**Files:**
- Modify: `app/templates/tasks/detail.html:199-203`

**Step 1: 替换 Update Assignment 中的 IT Person 输入**

每个 assignment 有自己的 location，需要使用该 location 的 contacts。利用 Task 1 传入的 `location_contacts_map`。

```html
<div x-data="itPersonSelect({
    contacts: {{ location_contacts_map.get(assignment.location_id, []) | tojson }},
    currentName: '{{ assignment.it_name or '' }}'
})">
    <label class="block text-xs font-medium text-gray-500 dark:text-gray-300 mb-1">IT Person</label>
    <input type="hidden" name="it_name" :value="selectedName">
    <input type="hidden" name="it_role" :value="selectedRole">
    <template x-if="contacts.length > 0 && !showManual">
        <select @change="onSelect($event)"
            class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
            <option value="">-- Select IT Person --</option>
            <template x-for="c in contacts" :key="c.name">
                <option :value="c.name" x-text="c.name" :selected="c.name === currentName"></option>
            </template>
            <option value="__other__">-- 手动输入 --</option>
        </select>
    </template>
    <template x-if="contacts.length === 0 || showManual">
        <input type="text" x-model="selectedName" placeholder="Optional"
            class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
    </template>
</div>
```

注意：`itPersonSelect` 函数已在 Task 2 中添加到 `tasks/detail.html` 的 `extra_js` block（和 `addLocationForm` 一起）。

**Step 2: 验证 Update Assignment 下拉**

打开 task detail，展开某 location assignment 的详情，确认 IT Person 下拉正确。

**Step 3: Commit**

```bash
git add app/templates/tasks/detail.html
git commit -m "feat: IT Person dropdown in task detail Update Assignment form"
```

---

### Task 6: 全流程手动测试

**Step 1: 启动服务**

Run: `bash taskmgr.sh restart`

**Step 2: 测试场景**

1. **Location 有 contacts → Add Task**：选 location detail，点 Add Task，确认 IT Person 有下拉，选一个联系人后提交，验证 assignment 的 it_name 和 it_role 正确保存
2. **Location 无 contacts → Add Task**：找一个无 contacts 的 location，确认 IT Person 是文本输入框
3. **Location 有 contacts → Update Assignment**：修改已有 assignment 的 IT Person 下拉选择，提交后确认更新
4. **手动输入切换**：选下拉的"手动输入"选项，确认切换为文本输入，输入名字提交
5. **Task detail → Add Location**：选一个 location，确认 IT Person 下拉更新，选联系人提交
6. **Task detail → Update Assignment**：展开 assignment，确认 IT Person 下拉正确回显
7. **已有手动输入的 assignment**：确认旧数据（手动输入的 it_name）正确回显，若不在联系人列表中则显示"手动输入"模式

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: IT Person select-from-contacts complete"
```
