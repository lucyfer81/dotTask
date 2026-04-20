# APAC Infra Task Manager — 设计文档

## 概述

将个人 Excel 任务管理工具（APAC_Infra_Task_List.xlsx）转为 Flask + SQLite Web 应用。单人使用，核心流程：创建任务 → 按规则/手动分配到各地 → 跟踪进度 → 更新状态。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Flask + SQLAlchemy + Flask-WTF |
| 前端 | HTMX + Tailwind CSS + Chart.js |
| 数据库 | SQLite（单文件） |
| Excel | openpyxl |
| PDF 导出 | jsPDF（前端） |

## 数据模型

### Location_Master（地点表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增 |
| location_name | TEXT | 地点名称 |
| country | TEXT | 国家 |
| city | TEXT | 城市 |
| location_type | TEXT | 地点类型（Plant/Office 等） |
| region | TEXT | 区域（如 APAC-North） |
| is_active | BOOLEAN | 是否活跃 |
| it_manager | TEXT | IT 经理 |
| primary_it_contact | TEXT | 主要 IT 联系人 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### Task_Master（任务表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增 |
| task_name | TEXT | 任务名称 |
| task_source | TEXT | 来源 |
| stakeholder | TEXT | 干系人 |
| task_description | TEXT | 描述 |
| scope_type | TEXT | 范围类型：All/Country/Location_Type/Region/Manual |
| scope_rule | TEXT | 规则说明 |
| scope_detail | TEXT | 规则值（如 China、Plant） |
| task_owner | TEXT | 负责人 |
| execution_model | TEXT | 执行模式 |
| overall_status | TEXT | Not Started/In Progress/Completed/On Hold/Cancelled |
| start_date | DATE | 开始日期 |
| target_date | DATE | 目标日期 |
| last_update | DATE | 最后更新 |
| link_to_file | TEXT | 文件链接 |
| link_to_mail | TEXT | 邮件链接 |
| task_priority | TEXT | Critical/High/Medium/Low |
| comments | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### Task_Assignment（分配表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增 |
| task_id | INTEGER FK | → Task_Master.id |
| location_id | INTEGER FK | → Location_Master.id |
| it_name | TEXT | IT 人员 |
| it_role | TEXT | IT 角色 |
| local_responsibility | TEXT | 本地职责 |
| local_status | TEXT | Pending/In Progress/Completed/Blocked/N/A |
| last_update | DATE | 最后更新 |
| issue_blocker | TEXT | 阻碍项 |
| comments | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 任务分配机制

### 规则引擎（Scope Engine）

| scope_type | 匹配逻辑 | scope_detail 示例 |
|---|---|---|
| All | 所有 is_active=True 的地点 | （空） |
| Country | Location_Master.country = scope_detail | "China" |
| Location_Type | Location_Master.location_type = scope_detail | "Plant" |
| Region | Location_Master.region = scope_detail | "APAC-North" |
| Manual | 不自动分配，用户手动选择 | （空） |

### 工作流

1. 用户创建任务，设定 scope_type + scope_detail
2. 系统预览匹配的地点数量
3. 确认后自动生成 Task_Assignment 记录
4. 用户可在任务详情页手动增删地点

## 页面设计

### 1. 仪表盘 `/`

- 统计卡片：总任务、进行中、已完成、逾期、有阻塞
- 图表：按状态分布（饼）、按优先级（柱）、按地点进度（堆叠柱）、时间线趋势（线）
- 逾期/即将到期任务提醒
- 导出 PDF 报告

### 2. 任务列表 `/tasks`

- 表格 + 筛选（状态/优先级/负责人/日期）+ 搜索 + 排序 + 分页
- 行内快速更新状态（HTMX 下拉框）
- 新建/编辑/删除/查看详情

### 3. 任务详情 `/tasks/<id>`

- 基本信息（可编辑）
- 关联地点分配列表（查看/编辑/增删）
- 分配预览与规则触发

### 4. 地点管理 `/locations`

- CRUD + 激活/停用
- 查看某地点所有任务分配

### 5. 导入导出 `/data`

- 上传 .xlsx 导入
- 按筛选条件导出 Excel

## 项目结构

```
dotTask/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── dashboard.py
│   │   ├── tasks.py
│   │   ├── locations.py
│   │   └── data_io.py
│   ├── services/
│   │   ├── scope_engine.py
│   │   └── excel_service.py
│   ├── templates/
│   └── static/
├── instance/tasks.db
├── config.py
├── run.py
└── requirements.txt
```

## 部署

本地 `flask run`，端口 5000。无需 Docker 或外部服务。
