# 城市书房志愿排班系统

一个完整的全栈志愿排班管理系统，涵盖书房点位管理、班次发布、志愿者报名、签到签退、请假补位和运营统计等全流程功能。

## 功能特性

### 角色权限
- **书房管理员**: 系统全权限，可管理所有资源
- **志愿者**: 报名班次、签到签退、请假申请
- **运营人员**: 班次管理、报名审核、数据统计
- **培训负责人**: 志愿者培训状态管理

### 核心模块
- **点位管理**: 书房点位的增删改查
- **班次管理**: 班次创建、发布、取消、状态管理
- **报名管理**: 志愿者报名、管理员审核、冲突检测
- **签到签退**: 实时签到、签退、时长统计
- **请假补位**: 请假申请、审批、自动释放名额、补位待办
- **志愿者管理**: 志愿者档案、培训状态
- **运营统计**: 数据概览、服务时长排行、点位使用情况
- **审计日志**: 全操作审计追踪

### 业务规则
1. **未培训志愿者不能排晚班** - 晚班班次对未培训志愿者自动拦截
2. **同日跨点位冲突检测** - 同一志愿者同一天不能在不同点位排班
3. **满员班次限制** - 班次人数达到上限后无法继续报名
4. **已签到不能取消** - 已签到的班次不能取消报名
5. **请假释放名额** - 请假审批通过后自动释放名额并生成补位待办
6. **非管理员限制** - 非管理员不能强制调整他人班次

## 技术栈

### 后端
- **框架**: FastAPI (Python)
- **ORM**: SQLAlchemy 2.0
- **数据库**: SQLite (可扩展为 PostgreSQL/MySQL)
- **认证**: JWT (OAuth2)
- **密码加密**: bcrypt

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Ant Design 5
- **路由**: React Router v6
- **HTTP 客户端**: Axios
- **日期处理**: Day.js

### 部署
- **容器化**: Docker + docker-compose
- **反向代理**: Nginx
- **健康检查**: 内置健康检查接口

## 快速开始

### 方式一：Docker Compose (推荐)

```bash
# 克隆项目后，在项目根目录执行
docker-compose up -d --build
```

服务启动后：
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 方式二：本地开发

#### 后端
```bash
cd backend
pip install -r requirements.txt
python init_data.py
uvicorn app.main:app --reload --port 8000
```

#### 前端
```bash
cd frontend
npm install
npm run dev
```

## 默认账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理员，拥有全部权限 |
| 运营人员 | operations | ops123 | 班次管理和数据统计 |
| 培训负责人 | training | train123 | 管理志愿者培训状态 |
| 志愿者 | volunteer1 | vol123 | 已完成培训的志愿者 |
| 志愿者 | volunteer2 | vol123 | 已完成培训的志愿者 |
| 志愿者 | volunteer3 | vol123 | **未培训**的志愿者（用于测试晚班限制） |
| 志愿者 | volunteer4 | vol123 | 培训中的志愿者 |

## 项目结构

```
.
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI 应用入口
│   │   ├── config.py        # 配置
│   │   ├── database.py      # 数据库连接
│   │   ├── models.py        # SQLAlchemy 模型
│   │   ├── schemas.py       # Pydantic 模式
│   │   ├── auth.py          # 认证工具
│   │   ├── routers/         # API 路由
│   │   │   ├── auth.py
│   │   │   ├── study_rooms.py
│   │   │   ├── shifts.py
│   │   │   ├── signups.py
│   │   │   ├── attendance.py
│   │   │   ├── leave.py
│   │   │   ├── volunteers.py
│   │   │   ├── stats.py
│   │   │   └── audit.py
│   │   └── services/        # 业务逻辑层
│   │       ├── shift_service.py
│   │       ├── signup_service.py
│   │       ├── attendance_service.py
│   │       └── leave_service.py
│   ├── init_data.py         # 初始化数据脚本
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── api/             # API 接口
│   │   ├── pages/           # 页面组件
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   └── Dockerfile
├── scripts/                 # 脚本
│   └── smoke.sh             # Smoke 测试脚本
├── docker-compose.yml
└── README.md
```

## API 接口

### 认证
- `POST /api/auth/login` - 登录
- `POST /api/auth/register` - 注册
- `GET /api/auth/me` - 获取当前用户信息

### 书房点位
- `GET /api/study-rooms` - 获取点位列表
- `POST /api/study-rooms` - 创建点位
- `GET /api/study-rooms/{id}` - 获取点位详情
- `PUT /api/study-rooms/{id}` - 更新点位
- `DELETE /api/study-rooms/{id}` - 删除点位

### 班次
- `GET /api/shifts` - 获取班次列表
- `POST /api/shifts` - 创建班次
- `GET /api/shifts/{id}` - 获取班次详情
- `PUT /api/shifts/{id}` - 更新班次
- `POST /api/shifts/{id}/publish` - 发布班次
- `POST /api/shifts/{id}/cancel` - 取消班次
- `DELETE /api/shifts/{id}` - 删除班次

### 报名
- `GET /api/signups` - 获取报名列表
- `POST /api/signups` - 创建报名
- `GET /api/signups/{id}` - 获取报名详情
- `PUT /api/signups/{id}/approve` - 审核通过
- `PUT /api/signups/{id}/reject` - 审核拒绝
- `DELETE /api/signups/{id}` - 取消报名
- `GET /api/signups/check/conflict` - 冲突检查

### 签到签退
- `GET /api/attendance` - 获取签到记录
- `POST /api/attendance/check-in` - 签到
- `POST /api/attendance/check-out` - 签退

### 请假补位
- `GET /api/leave` - 获取请假列表
- `POST /api/leave` - 申请请假
- `PUT /api/leave/{id}/approve` - 批准请假
- `PUT /api/leave/{id}/reject` - 拒绝请假
- `GET /api/leave/replacements/todos` - 补位待办列表
- `PUT /api/leave/replacements/{id}/assign` - 分配补位
- `PUT /api/leave/replacements/{id}/complete` - 完成补位

### 志愿者
- `GET /api/volunteers` - 获取志愿者列表
- `PUT /api/volunteers/profile/{id}/training` - 更新培训状态

### 统计
- `GET /api/stats/overview` - 概览统计
- `GET /api/stats/volunteer-hours` - 志愿者服务时长
- `GET /api/stats/room-usage` - 点位使用情况

### 审计
- `GET /api/audit` - 审计日志列表

### 健康检查
- `GET /health` - 健康检查

## Smoke 测试

### 运行测试

```bash
# 方式一：使用脚本
./scripts/smoke.sh

# 方式二：指定后端地址
BACKEND_URL=http://localhost:8000 ./scripts/smoke.sh
```

### 测试项

1. **健康检查** - 验证服务正常运行
2. **未培训志愿者排晚班失败** - 验证培训规则
3. **同日跨点位排班冲突** - 验证冲突检测
4. **满员班次重复报名不会超员** - 验证人数限制

## 业务流程图

```
点位维护 → 班次发布 → 志愿者报名 → 管理员审核 → 排班确认
                                                    ↓
                                              签到/签退
                                                    ↓
                                              请假补位 ← 请假申请
                                                    ↓
                                              运营统计
```

## 并发控制

- 报名时实时检查班次容量
- 审核通过前二次校验人数限制
- 数据库事务保证数据一致性
- 重复报名幂等处理（返回已有记录）

## 审计日志

所有关键操作均记录审计日志，包括：
- 用户操作人
- 操作类型
- 操作对象
- 操作时间
- IP 地址

## License

MIT
