# Render 部署指南

本项目已配置好 Render 部署所需的文件。

## 部署步骤

### 方法一：使用 Render Dashboard（推荐）

1. **登录 Render**
   - 访问 [https://dashboard.render.com/](https://dashboard.render.com/)
   - 使用 GitHub/GitLab/Bitbucket 账号登录

2. **创建新的 Web Service**
   - 点击 "New +" → "Web Service"
   - 连接你的 Git 仓库（GitHub/GitLab/Bitbucket）
   - 选择 `bank-fastapi` 仓库

3. **配置服务**
   - **Name**: `bank-fastapi`（或你喜欢的名称）
   - **Region**: 选择离你最近的区域（如 `Singapore`）
   - **Branch**: `main`（或你的主分支）
   - **Root Directory**: `bank-fastapi`（如果仓库根目录是 `bank-fastapi`）
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: 选择 `Free`（免费计划）或付费计划

4. **环境变量（可选）**
   - 如果需要，可以添加环境变量：
     - `PYTHON_VERSION`: `3.11.0`
     - 其他自定义环境变量

5. **部署**
   - 点击 "Create Web Service"
   - Render 会自动开始构建和部署
   - 等待部署完成（通常需要 2-5 分钟）

### 方法二：使用 render.yaml（自动配置）

如果你已经将 `render.yaml` 文件提交到仓库：

1. 登录 Render Dashboard
2. 点击 "New +" → "Blueprint"
3. 选择你的 Git 仓库
4. Render 会自动读取 `render.yaml` 并创建服务
5. 点击 "Apply" 开始部署

## 重要提示

### ✅ SQLite 数据库支持

**Render 支持持久化存储，SQLite 可以正常工作！**

- Render 的免费计划提供持久化磁盘存储
- 数据库文件会保存在服务实例中
- 数据在服务重启后仍然保留

### ⚠️ 免费计划限制

- **自动休眠**: 免费计划的服务在 15 分钟无活动后会自动休眠
- **首次唤醒**: 休眠后的首次请求可能需要 30-60 秒来唤醒服务
- **升级建议**: 如果需要 24/7 运行，考虑升级到付费计划

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
1. 确保 `database.py` 中的路径是相对路径
2. 检查是否有写入权限
3. 查看日志中的数据库初始化信息

## 推荐配置

对于生产环境，建议：
1. 使用付费计划（避免自动休眠）
2. 考虑使用 PostgreSQL（Render 提供免费 PostgreSQL 数据库）
3. 配置自定义域名
4. 设置环境变量来管理敏感信息

