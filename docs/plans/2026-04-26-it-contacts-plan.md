# Location 多 IT Contact 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Location 的两个固定 IT 联系人字段替换为可动态增减的 ItContact 关联表，每个联系人记录姓名、职能、邮箱、电话。

**Architecture:** 新建 `ItContact` 模型通过 `location_id` 外键关联 Location。使用项目已有的 YAML + `get_options()` 模式管理职能下拉选项。前端用 Alpine.js 实现联系人行的动态增减。数据迁移在 `_migrate_db()` 中完成。

**Tech Stack:** Flask, SQLAlchemy, SQLite, Alpine.js, Jinja2, YAML 配置

---

### Task 1: 新增 ItContact 模型和 YAML 配置

**Files:**
- Modify: `app/models.py:6-30` (Location 模型)
- Modify: `config/dropdowns.yaml` (新增 it_roles)
- Modify: `app/__init__.py` (_migrate_db 函数)

**Step 1: 在 models.py 中新增 ItContact 模型，并在 Location 上添加 relationship**

在 `Task` 类之前（第 31 行前）新增：

```python
class ItContact(db.Model):
    __tablename__ = "it_contact"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location_master.id"), nullable=False)
    name = db.Column(db.String(200))
    role = db.Column(db.String(100))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(100))

    def __repr__(self):
        return f"<ItContact {self.name}>"
```

在 Location 类的 `assignments` relationship 之后（第 26 行后）新增：

```python
    it_contacts = db.relationship("ItContact", backref="location", cascade="all, delete-orphan")
```

暂不删除旧的 `it_manager` 和 `primary_it_contact` 字段（迁移完成后再删）。

**Step 2: 在 dropdowns.yaml 末尾新增 it_roles**

```yaml
it_roles:
  - IT Manager
  - IT Coordinator
  - Network Admin
  - System Admin
  - Security
  - Infrastructure
  - Helpdesk
  - Application Support
  - Other
```

**Step 3: 在 app/__init__.py 的 _migrate_db 中添加数据迁移逻辑**

在 `_migrate_db` 函数末尾追加：

```python
        # Migrate it_manager / primary_it_contact → it_contact rows
        result = conn.execute(sqlalchemy.text(
            "SELECT id FROM sqlite_master WHERE type='table' AND name='it_contact'"
        ))
        if result.fetchone():
            from app.models import Location, ItContact
            locations = Location.query.all()
            for loc in locations:
                existing = ItContact.query.filter_by(location_id=loc.id).count()
                if existing > 0:
                    continue
                if loc.it_manager:
                    conn.execute(sqlalchemy.text(
                        "INSERT INTO it_contact (location_id, name, role) VALUES (:lid, :name, :role)"
                    ), {"lid": loc.id, "name": loc.it_manager, "role": "IT Manager"})
                if loc.primary_it_contact:
                    conn.execute(sqlalchemy.text(
                        "INSERT INTO it_contact (location_id, name, role) VALUES (:lid, :name, :role)"
                    ), {"lid": loc.id, "name": loc.primary_it_contact, "role": "IT Coordinator"})
            conn.commit()
```

**Step 4: 重启服务，确认表创建和数据迁移成功**

Run: `bash taskmgr.sh restart`

检查 flask.log 无报错。

**Step 5: Commit**

```bash
git add app/models.py config/dropdowns.yaml app/__init__.py
git commit -m "feat: add ItContact model with data migration from legacy fields"
```

---

### Task 2: 修改 locations 路由，处理联系人 CRUD

**Files:**
- Modify: `app/routes/locations.py`

**Step 1: 修改 create 路由（第 121-140 行）**

在 import 行追加 `ItContact`：

```python
from app.models import Location, TaskAssignment, Task, ItContact
```

修改 POST 处理，创建 location 后保存联系人：

```python
@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        loc = Location(
            location_name=request.form["location_name"],
            country=request.form.get("country", ""),
            city=request.form.get("city", ""),
            location_type=request.form.get("location_type", ""),
            region=request.form.get("region", ""),
            is_active=request.form.get("is_active") == "on",
            comments=request.form.get("comments", ""),
        )
        db.session.add(loc)
        db.session.flush()  # get loc.id
        _save_contacts(loc.id)
        db.session.commit()
        flash("Location created", "success")
        return redirect(url_for("locations.list"))

    return render_template(
        "locations/form.html", location=None,
        countries=get_options("countries"),
        location_types=get_options("location_types"),
        it_roles=get_options("it_roles"),
    )
```

**Step 2: 修改 edit 路由（第 143-160 行）**

```python
@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    loc = Location.query.get_or_404(id)
    if request.method == "POST":
        loc.location_name = request.form["location_name"]
        loc.country = request.form.get("country", "")
        loc.city = request.form.get("city", "")
        loc.location_type = request.form.get("location_type", "")
        loc.region = request.form.get("region", "")
        loc.is_active = request.form.get("is_active") == "on"
        loc.comments = request.form.get("comments", "")
        _save_contacts(loc.id)
        db.session.commit()
        flash("Location updated", "success")
        return redirect(url_for("locations.list"))

    return render_template(
        "locations/form.html", location=loc,
        countries=get_options("countries"),
        location_types=get_options("location_types"),
        it_roles=get_options("it_roles"),
    )
```

**Step 3: 新增 _save_contacts 辅助函数**

在 create 路由之前添加：

```python
def _save_contacts(location_id):
    """Replace all ItContact rows for a location from form data."""
    ItContact.query.filter_by(location_id=location_id).delete()
    names = request.form.getlist("contact_name")
    roles = request.form.getlist("contact_role")
    emails = request.form.getlist("contact_email")
    phones = request.form.getlist("contact_phone")
    for i in range(len(names)):
        if names[i].strip():
            db.session.add(ItContact(
                location_id=location_id,
                name=names[i].strip(),
                role=roles[i] if i < len(roles) else "",
                email=emails[i] if i < len(emails) else "",
                phone=phones[i] if i < len(phones) else "",
            ))
```

**Step 4: Commit**

```bash
git add app/routes/locations.py
git commit -m "feat: add ItContact CRUD in location create/edit routes"
```

---

### Task 3: 修改 form.html，实现动态联系人列表

**Files:**
- Modify: `app/templates/locations/form.html:64-76`

**Step 1: 替换旧的 IT Manager 和 Primary IT Contact 两个 div**

将第 64-76 行（IT Manager + Primary IT Contact 两个 div）替换为：

```html
            <!-- IT Contacts (dynamic list) -->
            <div class="md:col-span-2" x-data="contactList({
                roles: [{% for r in it_roles %}'{{ r }}',{% endfor %}],
                contacts: [
                    {% if location and location.it_contacts %}
                    {% for c in location.it_contacts %}
                    { name: '{{ c.name|e }}', role: '{{ c.role|e }}', email: '{{ c.email|e }}', phone: '{{ c.phone|e }}' },
                    {% endfor %}
                    {% endif %}
                ]
            })">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">IT Contacts</label>
                <div class="space-y-3">
                    <template x-for="(c, i) in contacts" :key="i">
                        <div class="flex flex-wrap items-start gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-cc-border">
                            <div class="flex-1 min-w-[140px]">
                                <input type="text" x-model="c.name" name="contact_name" class="w-full px-2 py-1 border border-gray-300 dark:border-cc-border rounded text-sm dark:bg-cc-bg dark:text-gray-200" placeholder="Name">
                            </div>
                            <div class="w-[160px]">
                                <select x-model="c.role" name="contact_role" class="w-full px-2 py-1 border border-gray-300 dark:border-cc-border rounded text-sm dark:bg-cc-bg dark:text-gray-200">
                                    <option value="">-- Role --</option>
                                    <template x-for="r in roles"><option :value="r" x-text="r"></option></template>
                                </select>
                            </div>
                            <div class="flex-1 min-w-[160px]">
                                <input type="email" x-model="c.email" name="contact_email" class="w-full px-2 py-1 border border-gray-300 dark:border-cc-border rounded text-sm dark:bg-cc-bg dark:text-gray-200" placeholder="Email">
                            </div>
                            <div class="w-[130px]">
                                <input type="tel" x-model="c.phone" name="contact_phone" class="w-full px-2 py-1 border border-gray-300 dark:border-cc-border rounded text-sm dark:bg-cc-bg dark:text-gray-200" placeholder="Phone">
                            </div>
                            <button type="button" @click="contacts.splice(i, 1)" class="px-2 py-1 text-red-600 dark:text-red-400 hover:text-red-800 text-sm" title="Remove">&times;</button>
                        </div>
                    </template>
                </div>
                <button type="button" @click="contacts.push({ name: '', role: '', email: '', phone: '' })"
                    class="mt-2 px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 border border-blue-300 dark:border-blue-700 rounded">
                    + Add Contact
                </button>
            </div>
```

**Step 2: 在 `{% endblock %}` 之前添加 Alpine.js 组件**

在文件末尾 `{% endblock %}` 之前添加：

```html
{% block extra_js %}
<script>
function contactList(config) {
    return {
        roles: config.roles,
        contacts: config.contacts.length ? config.contacts : [{ name: '', role: '', email: '', phone: '' }]
    };
}
</script>
{% endblock %}
```

**Step 3: Commit**

```bash
git add app/templates/locations/form.html
git commit -m "feat: dynamic IT contacts list in location form"
```

---

### Task 4: 修改 detail.html，展示联系人表格

**Files:**
- Modify: `app/templates/locations/detail.html:71-78`

**Step 1: 替换旧的 IT Manager 和 Primary IT Contact 展示**

将第 71-78 行替换为：

```html
                    <div class="sm:col-span-2">
                        <dt class="text-sm font-medium text-gray-500 dark:text-gray-300 mb-2">IT Contacts</dt>
                        {% if location.it_contacts %}
                        <table class="w-full text-sm">
                            <thead>
                                <tr class="border-b border-gray-200 dark:border-cc-border">
                                    <th class="text-left py-1 pr-3 text-xs font-medium text-gray-500 dark:text-gray-300">Name</th>
                                    <th class="text-left py-1 pr-3 text-xs font-medium text-gray-500 dark:text-gray-300">Role</th>
                                    <th class="text-left py-1 pr-3 text-xs font-medium text-gray-500 dark:text-gray-300">Email</th>
                                    <th class="text-left py-1 text-xs font-medium text-gray-500 dark:text-gray-300">Phone</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for c in location.it_contacts %}
                                <tr class="border-b border-gray-100 dark:border-gray-700">
                                    <td class="py-1.5 pr-3 text-gray-900 dark:text-gray-100">{{ c.name or '-' }}</td>
                                    <td class="py-1.5 pr-3"><span class="badge badge-in-progress">{{ c.role or '-' }}</span></td>
                                    <td class="py-1.5 pr-3 text-gray-900 dark:text-gray-100">{{ c.email or '-' }}</td>
                                    <td class="py-1.5 text-gray-900 dark:text-gray-100">{{ c.phone or '-' }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        {% else %}
                        <dd class="text-sm text-gray-500">-</dd>
                        {% endif %}
                    </div>
```

**Step 2: Commit**

```bash
git add app/templates/locations/detail.html
git commit -m "feat: display IT contacts table in location detail"
```

---

### Task 5: 清理旧字段，最终验证

**Files:**
- Modify: `app/models.py` (移除 it_manager, primary_it_contact)
- Modify: `app/__init__.py` (可选：清理迁移代码)

**Step 1: 确认数据迁移成功后，从 Location 模型移除旧字段**

删除 `app/models.py` 中的：
```python
    it_manager = db.Column(db.String(200))
    primary_it_contact = db.Column(db.String(200))
```

**Step 2: 重启服务，验证功能正常**

Run: `bash taskmgr.sh restart`

- 访问 Location 列表页，确认无报错
- 创建一个新 Location，添加多个 IT Contact，确认保存成功
- 编辑已有 Location，确认联系人数据正确加载，可增删
- 查看 Location 详情页，确认联系人表格正确显示

**Step 3: Commit**

```bash
git add app/models.py
git commit -m "refactor: remove legacy it_manager and primary_it_contact fields"
```
