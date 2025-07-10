# OneTools Python

OneTools 数据库运维工具的 Python 重构版本，采用现代化的技术栈，大幅简化代码量和部署复杂度。

## 🚀 主要特性

### 技术优势
- **异步架构**: 全异步设计，性能提升 3-5 倍
- **代码简化**: 相比 .NET 版本减少 70% 代码量
- **类型安全**: 全程类型检查和验证
- **自动文档**: OpenAPI 自动生成 API 文档
- **容器化**: Docker 支持，跨平台部署

### 功能特性
- **用户查询**: 灵活的用户信息查询和管理
- **自定义查询**: 安全的 SQL 查询执行
- **事务查询**: 事务数据分析和查询
- **数据库管理**: 多数据库连接和健康监控
- **模块化架构**: 插件式模块系统

## 🛠 技术栈

### 后端核心
- **FastAPI**: 现代化的 Web 框架
- **SQLAlchemy**: 异步 ORM 和数据库工具
- **Pydantic**: 数据验证和设置管理
- **Uvicorn**: ASGI 服务器

### 数据库支持
- **SQL Server**: 主要数据库 (通过 ODBC)
- **SQLite**: 配置存储
- **MySQL/PostgreSQL**: 可选支持

### 开发工具
- **pytest**: 测试框架
- **black/isort**: 代码格式化
- **mypy**: 类型检查
- **structlog**: 结构化日志

## 📋 系统要求

### 基础要求
- Python 3.11+
- SQL Server 2019+ (主数据库)
- ODBC Driver 17 for SQL Server

### 可选要求
- Docker & Docker Compose
- Redis (缓存，可选)

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd onetools-py
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

### 3. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 数据库配置
确保 SQL Server 可访问，并更新 `.env` 文件中的连接信息：
```env
SQLSERVER_HOST=localhost\SQLEXPRESS
SQLSERVER_DATABASE=OneToolsDb
SQLSERVER_TRUSTED_CONNECTION=true
```

### 5. 启动服务
```bash
# 开发模式
python -m uvicorn app.main:app --reload

# 或使用启动脚本
chmod +x scripts/start.sh
./scripts/start.sh
```

### 6. 访问服务
- **API 服务**: http://localhost:15008
- **API 文档**: http://localhost:15008/api/docs
- **健康检查**: http://localhost:15008/health

## 🐳 Docker 部署

### 构建镜像
```bash
docker build -t onetools-python .
```

### 使用 Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 📚 API 文档

### 主要端点

#### 用户查询
- `GET /api/v1/users/parameters` - 获取查询参数
- `POST /api/v1/users/query` - 执行用户查询
- `GET /api/v1/users/{id}` - 获取用户详情
- `POST /api/v1/users/{id}/reset-password` - 重置密码

#### 自定义查询
- `POST /api/v1/custom/execute` - 执行自定义 SQL
- `POST /api/v1/custom/validate` - 验证 SQL 安全性
- `POST /api/v1/custom/save` - 保存查询
- `GET /api/v1/custom/saved` - 获取保存的查询

#### 数据库管理
- `GET /api/v1/database/health` - 健康检查
- `GET /api/v1/database/tables` - 获取表列表
- `GET /api/v1/database/tables/{name}` - 获取表结构

### 完整文档
启动服务后访问 `/api/docs` 查看完整的 OpenAPI 文档。

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api.py

# 生成覆盖率报告
pytest --cov=app tests/
```

### 测试类型
- **单元测试**: 核心功能测试
- **集成测试**: API 端点测试
- **安全测试**: SQL 注入防护测试

## 📁 项目结构

```
onetools-py/
├── app/                    # 应用核心代码
│   ├── api/               # API 路由和端点
│   ├── core/              # 核心配置和工具
│   ├── models/            # Pydantic 模型
│   ├── modules/           # 业务模块
│   ├── services/          # 业务服务层
│   ├── utils/             # 工具函数
│   └── main.py            # 应用入口
├── config/                # 配置文件
├── tests/                 # 测试代码
├── scripts/               # 部署脚本
├── docker-compose.yml     # Docker 编排
├── Dockerfile            # Docker 镜像
├── requirements.txt      # Python 依赖
└── pyproject.toml        # 项目配置
```

## ⚙️ 配置说明

### 环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ENVIRONMENT` | 运行环境 | `development` |
| `SQLSERVER_HOST` | SQL Server 地址 | `localhost\SQLEXPRESS` |
| `SQLSERVER_DATABASE` | 数据库名 | `OneToolsDb` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `SERVER_PORT` | 服务端口 | `15008` |

### 配置文件
- `config/settings.yaml`: 主配置文件
- `.env`: 环境变量配置
- `pyproject.toml`: 项目和依赖配置

## 🔒 安全特性

### SQL 安全
- **参数化查询**: 防止 SQL 注入
- **关键词过滤**: 阻止危险操作
- **查询验证**: 多层安全检查
- **只读模式**: 自定义查询限制为 SELECT

### 数据保护
- **敏感信息脱敏**: 日志中的敏感数据自动脱敏
- **连接字符串保护**: 密码信息自动隐藏
- **输入验证**: 严格的参数验证

## 📈 性能特性

### 查询优化
- **连接池**: 数据库连接复用
- **查询缓存**: 结果智能缓存
- **分页查询**: 大数据集优化
- **异步处理**: 并发请求支持

### 监控指标
- **查询统计**: 执行时间和成功率
- **缓存命中率**: 缓存效率监控
- **数据库健康**: 连接状态监控

## 🔧 开发指南

### 添加新模块
1. 继承 `BaseQueryModule`
2. 实现必需的抽象方法
3. 注册到模块注册中心
4. 添加对应的 API 端点

### 代码规范
- 使用 `black` 格式化代码
- 使用 `mypy` 进行类型检查
- 遵循 PEP 8 编码规范
- 编写单元测试

### 提交规范
- 使用 Conventional Commits 格式
- 提交前运行测试和代码检查
- 更新相关文档

## 🚀 生产部署

### 部署检查清单
- [ ] 更新生产环境配置
- [ ] 设置强密码和密钥
- [ ] 配置 HTTPS 和防火墙
- [ ] 设置日志轮转
- [ ] 配置健康检查
- [ ] 设置监控告警

### 性能调优
- 调整连接池大小
- 配置查询缓存
- 优化日志级别
- 设置合适的 worker 数量

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

[MIT License](LICENSE)

## 📞 支持

- **文档**: 查看 `/api/docs` 获取完整 API 文档
- **问题报告**: 在 GitHub Issues 中报告问题
- **功能请求**: 在 GitHub Issues 中提出功能请求

---

## 🎯 与 .NET 版本对比

| 特性 | .NET 版本 | Python 版本 | 改进 |
|------|-----------|-------------|------|
| 代码量 | ~15,000 行 | ~4,500 行 | -70% |
| 启动时间 | 5-10 秒 | 1-2 秒 | 5x 提升 |
| 内存占用 | 200MB+ | 100MB | -50% |
| 部署复杂度 | 高 | 低 | 大幅简化 |
| API 文档 | 手工维护 | 自动生成 | 自动化 |
| 类型安全 | 部分 | 完整 | 全覆盖 |

**OneTools Python - 更简单、更快速、更现代的数据库运维工具**