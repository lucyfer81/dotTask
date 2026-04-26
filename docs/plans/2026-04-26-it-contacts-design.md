# Location 多 IT Contact 设计

## 背景

当前 Location 模型只有 `it_manager` 和 `primary_it_contact` 两个文本字段，无法满足每个 location 有多个 IT Contact 负责不同职能的需求。

## 方案

新建 `ItContact` 关联表，通过 `location_id` 外键关联到 Location。每个联系人记录姓名、职能、邮箱、电话。

## 数据模型

```python
class ItContact(db.Model):
    __tablename__ = "it_contact"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location_master.id"), nullable=False)
    name = db.Column(db.String(200))
    role = db.Column(db.String(100))  # 职能，来自 YAML 配置
    email = db.Column(db.String(200))
    phone = db.Column(db.String(100))
```

Location 模型添加 `it_contacts` relationship，移除旧的 `it_manager` 和 `primary_it_contact` 字段。

## 职能配置

在 `config/dropdowns.yaml` 中新增 `it_roles` 列表：

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

## UI 设计

- Location 表单页：动态增减联系人列表，每行含姓名、职能（下拉）、邮箱、电话 + 删除按钮，底部"添加联系人"按钮
- Location 详情页：表格展示所有联系人信息
- 使用 Alpine.js 实现动态交互

## 数据迁移

迁移脚本将现有 `it_manager` → role="IT Manager"、`primary_it_contact` → role="IT Coordinator" 的联系人记录。迁移完成后删除旧字段。

## 涉及文件

- `app/models.py` — 新增 ItContact 模型
- `config/dropdowns.yaml` — 新增 it_roles
- `app/routes/locations.py` — 处理联系人 CRUD
- `app/templates/locations/form.html` — 动态联系人列表
- `app/templates/locations/detail.html` — 联系人表格展示
- 迁移脚本
