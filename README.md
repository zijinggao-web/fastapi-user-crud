# FastAPI User CRUD with JWT Authentication

基于 FastAPI 的用户 CRUD API，使用 JWT 认证保护所有接口。

## 功能特性

- ✅ JWT 认证保护所有用户接口
- ✅ 完整的 CRUD 操作（创建、读取、更新、删除）
- ✅ MySQL 数据库存储
- ✅ 内置测试页面，方便自测
- ✅ Docker Compose 一键启动

## 快速开始

### 1. 启动服务

```bash
docker-compose up --build
```

服务启动后：
- API 服务：http://localhost:8000
- 测试页面：http://localhost:8000/test
- MySQL 数据库：localhost:3306

### 2. 使用测试页面

1. 访问 http://localhost:8000/test
2. 使用 User ID 作为用户名登录（密码可任意）
3. 获取 Token 后，可以测试所有 CRUD 操作

### 3. API 接口

#### 认证接口

- `POST /auth/login` - 登录获取 Token
  - 请求格式：`application/x-www-form-urlencoded`
  - 参数：`username` (User ID), `password` (可任意)
  - 返回：`{"access_token": "...", "token_type": "bearer"}`

#### 用户接口（需要 JWT Token）

所有接口都需要在 Header 中携带 Token：
```
Authorization: Bearer <your_token>
```

- `POST /users` - 创建用户
- `GET /users` - 获取所有用户
- `GET /users/me` - 获取当前登录用户信息
- `GET /users/{user_id}` - 获取指定用户
- `PUT /users/{user_id}` - 更新用户
- `DELETE /users/{user_id}` - 删除用户

## 项目结构

```
.
├── main.py              # FastAPI 应用主文件
├── requirements.txt      # Python 依赖
├── Dockerfile           # API 服务容器配置
├── docker-compose.yml   # Docker Compose 配置
└── README.md           # 项目说明
```

## 技术栈

- FastAPI - Web 框架
- SQLAlchemy - ORM
- PyMySQL - MySQL 驱动
- python-jose - JWT 处理
- MySQL 8.4 - 数据库