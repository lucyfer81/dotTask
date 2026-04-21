# YAML 下拉框配置设计

## 目标

将所有硬编码下拉框常量迁移到 YAML 配置文件，统一管理。location_type 字段从自由文本改为下拉框。

## 方案

### 新增文件

**`config/dropdowns.yaml`** — 存放所有下拉框选项：
- location_types（新增 Plant / Office / Market Office / Warehouse / R&D Center）
- statuses（原 STATUS_OPTIONS）
- priorities（原 PRIORITY_OPTIONS）
- local_statuses（原 LOCAL_STATUS_OPTIONS）

**`app/dropdowns.py`** — 加载工具：
- `get_options(key)` 函数，返回对应列表
- 应用启动时加载一次，缓存结果

### 修改文件

| 文件 | 改动 |
|------|------|
| `app/routes/tasks.py` | 删除3个常量，改用 `get_options()` |
| `app/routes/locations.py` | 传入 `location_types` 到模板 |
| `app/templates/locations/form.html` | location_type 从 `<input>` 改为 `<select>` |
| `app/services/scope_engine.py` | `get_distinct_location_types()` 改为从 YAML 读取 |

### 不做

- 不加管理界面编辑 YAML
- 不加热更新机制
- 不改数据库结构

## 依赖

- 添加 PyYAML
