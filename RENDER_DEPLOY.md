# Render 部署指南

本项目已配置好 Render 部署所需的文件。

## 部署步骤

### 方法一：使用 Render Dashboard（推荐）

1. **登录 Render**
   - 访问 [https://dashboard.render.com/](https://dashboard.render.com/)
   - 使用 GitHub/GitLab/Bitbucket 账号登录

2. **创建 PostgreSQL 数据库（必须先创建）**
   - 点击 "New +" → "PostgreSQL"
   - **Name**: `bank-fastapi-db`（或你喜欢的名称）
   - **Database**: `bankfastapi`（或你喜欢的名称）
   - **User**: `bankfastapi_user`（或你喜欢的名称）
   - **Region**: 选择离你最近的区域（如 `Singapore`）
   - **Plan**: 选择 `Free`（免费计划支持持久化）
   - 点击 "Create Database"
   - **重要**: 复制 `Internal Database URL` 或 `External Database URL`（稍后会用到）

3. **创建新的 Web Service**
   - 点击 "New +" → "Web Service"
   - 连接你的 Git 仓库（GitHub/GitLab/Bitbucket）
   - 选择 `bank-fastapi` 仓库

4. **配置服务**
   - **Name**: `bank-fastapi`（或你喜欢的名称）
   - **Region**: 选择离你最近的区域（如 `Singapore`）
   - **Branch**: `main`（或你的主分支）
   - **Root Directory**: `bank-fastapi`（如果仓库根目录是 `bank-fastapi`）
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: 选择 `Free`（免费计划）或付费计划

5. **配置环境变量（重要）**
   - 在 "Environment" 部分，添加以下环境变量：
     - `PYTHON_VERSION`: `3.11.0`
     - `DATABASE_URL`: 粘贴之前复制的 PostgreSQL 连接字符串
       - 格式类似：`postgresql://user:password@host:port/database`
       - 或使用 Render 的自动连接：在 "Environment" 中点击 "Link Database"，选择你创建的 PostgreSQL 数据库

6. **部署**
   - 点击 "Create Web Service"
   - Render 会自动开始构建和部署
   - 等待部署完成（通常需要 2-5 分钟）

### 方法二：使用 render.yaml（自动配置，推荐）

如果你已经将 `render.yaml` 文件提交到仓库：

1. 登录 Render Dashboard
2. 点击 "New +" → "Blueprint"
3. 选择你的 Git 仓库
4. Render 会自动读取 `render.yaml` 并创建：
   - PostgreSQL 数据库服务（免费，数据持久化）
   - Web 服务（自动连接到数据库）
5. 点击 "Apply" 开始部署
6. Render 会自动配置 `DATABASE_URL` 环境变量，无需手动设置

## 重要提示

### ⚠️ Render 免费计划限制（重要更新）

**Render 免费计划不再支持持久化磁盘存储！**

- ❌ **SQLite 在免费计划上不可靠**: 免费实例不支持持久化磁盘，SQLite 文件会在实例休眠或重启后丢失
- ❌ **不支持的功能**: SSH 访问、自动扩展、一次性任务、持久化磁盘
- ✅ **解决方案**: 使用 Render 的**免费 PostgreSQL 数据库**（数据会持久化保存）

### ✅ 使用 PostgreSQL 数据库（推荐）

本项目已配置为**自动支持 PostgreSQL 和 SQLite**：

- **本地开发**: 自动使用 SQLite (`data.db`)
- **Render 部署**: 自动使用 PostgreSQL（通过 `DATABASE_URL` 环境变量）

**PostgreSQL 的优势**：
- ✅ 免费计划支持持久化存储
- ✅ 数据不会丢失
- ✅ 适合生产环境
- ✅ Render 自动提供连接字符串

### ⚠️ 免费 Web 服务限制

- **自动休眠**: 免费计划的服务在 15 分钟无活动后会自动休眠
- **首次唤醒**: 休眠后的首次请求可能需要 30-60 秒来唤醒服务
- **升级建议**: 如果需要 24/7 运行，考虑升级到付费计划（但数据库可以继续使用免费计划）

### 环境变量

如果需要配置环境变量，可以在 Render Dashboard 中设置：
- 进入服务设置 → Environment
- 添加所需的变量

## 项目结构

```
bank-fastapi/
├── main.py                # FastAPI 应用主文件
├── database.py            # 数据库配置
├── models.py              # 数据模型
├── requirements.txt       # Python 依赖
├── render.yaml            # Render 配置文件（可选）
├── templates/             # Jinja2 模板文件
└── data.db                # SQLite 数据库（会在部署时创建）
```

## 访问部署后的应用

部署成功后，Render 会提供一个 URL，例如：
- `https://bank-fastapi.onrender.com`

API 端点：
- `https://bank-fastapi.onrender.com/api/account`
- `https://bank-fastapi.onrender.com/api/transactions`
- `https://bank-fastapi.onrender.com/admin`

## 本地测试

确保本地可以正常运行：

```bash
cd bank-fastapi
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 更新部署

每次推送到 Git 仓库的主分支，Render 会自动重新部署。

也可以手动触发部署：
- 进入 Render Dashboard
- 选择你的服务
- 点击 "Manual Deploy" → "Deploy latest commit"

## 查看日志

在 Render Dashboard 中：
- 进入你的服务
- 点击 "Logs" 标签
- 可以查看实时日志和构建日志

## 故障排查

### 部署失败
1. 检查构建日志中的错误信息
2. 确保 `requirements.txt` 中的所有依赖都正确
3. 检查 Python 版本是否兼容

### 服务无法启动
1. 检查启动命令是否正确：`uvicorn main:app --host 0.0.0.0 --port $PORT`
2. 查看日志中的错误信息
3. 确保 `main.py` 中的代码没有语法错误

### 数据库问题
1. **PostgreSQL 连接失败**:
   - 检查 `DATABASE_URL` 环境变量是否正确设置
   - 确保 PostgreSQL 数据库服务已创建并运行
   - 查看日志中的数据库连接错误信息
2. **本地开发使用 SQLite**:
   - 本地开发时，不设置 `DATABASE_URL` 环境变量即可使用 SQLite
   - 确保 `data.db` 文件有写入权限
3. **查看日志中的数据库初始化信息**:
   - 检查是否显示 "Database initialized successfully"
   - 如果看到 PostgreSQL 连接错误，检查连接字符串格式

## 推荐配置

对于生产环境，建议：
1. **数据库**: 使用 PostgreSQL（免费计划即可，数据持久化）
2. **Web 服务**: 
   - 免费计划：适合开发和测试（会自动休眠）
   - 付费计划：适合生产环境（24/7 运行，无休眠）
3. 配置自定义域名
4. 设置环境变量来管理敏感信息

## 数据库迁移说明

本项目已自动支持 SQLite 和 PostgreSQL：
- **本地开发**: 不设置 `DATABASE_URL`，自动使用 SQLite
- **Render 部署**: 设置 `DATABASE_URL` 环境变量，自动使用 PostgreSQL
- 代码会自动检测数据库类型并适配 SQL 语法

