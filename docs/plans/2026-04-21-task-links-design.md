# Task 邮件链接 & 文档链接设计

日期: 2026-04-21

## 需求

为 Task 添加两个多值链接字段：
1. **邮件 URL** — 多封邮件，点击在浏览器打开 Outlook Web 链接
2. **文档 URL** — 多个文件，点击在浏览器打开 OneDrive/SharePoint 文件

每个链接由用户自定义名称 + URL 组成。

## 设计决策

- **存储方案**: JSON 存储在现有列（方案 A）
- **表单交互**: 动态表单组（添加/删除按钮）
- **显示方式**: 文字链接，用户自定义显示名
- **现有数据**: `link_to_file` 和 `link_to_mail` 字段未使用过，可直接改造

## 数据层

### 列变更

- `link_to_mail`: `String(500)` → `Text`
- `link_to_file`: `String(500)` → `Text`

### JSON 格式

```json
[
  {"name": "Q3报告", "url": "https://onedrive.com/..."},
  {"name": "需求文档", "url": "https://sharepoint.com/..."}
]
```

空值存 `None`（数据库 NULL）。

### Task 模型

添加 `mail_links` 和 `file_links` 属性，封装 JSON 序列化/反序列化：

```python
@property
def mail_links(self):
    if self.link_to_mail:
        return json.loads(self.link_to_mail)
    return []

@mail_links.setter
def mail_links(self, value):
    self.link_to_mail = json.dumps(value) if value else None
```

## 表单层

### 动态表单组

邮件链接和文档链接各一组，每组：
- 初始显示一行（名称 + URL 输入框）
- "添加"按钮增加新行
- 每行有"删除"按钮
- 提交时 JavaScript 将所有行组装成 JSON

### 前端实现

- 不依赖额外 JS 库，使用原生 JavaScript + htmx
- 表单字段使用 `mail_links_json` / `file_links_json` 隐藏字段传递 JSON

## 显示层

### 任务详情页

链接以列表显示，每项为可点击的文字链接：

```html
<a href="https://..." target="_blank" rel="noopener">显示名称</a>
```

### 任务列表页

显示链接数量摘要（如"2封邮件 · 3个文档"），hover 展开显示所有链接。

## 影响范围

- `app/models.py` — Task 模型，修改列类型，添加属性
- `app/routes/tasks.py` — 创建/编辑路由，处理 JSON 数据
- `app/templates/tasks/form.html` — 动态表单组
- `app/templates/tasks/detail.html` — 链接显示
- `app/templates/tasks/list.html` — 列表中的链接摘要
- `app/services/excel_service.py` — Excel 导入导出适配
