# OneTools 数据库迁移和初始化脚本

本目录包含用于 OneTools 数据库管理的脚本，支持数据导出、迁移和初始化。

## 脚本文件说明

### 1. `export_current_data.py` - 数据导出脚本
**用途**: 导出当前SQLite数据库中的配置数据  
**功能**: 
- 导出菜单配置 (menu_configurations)
- 导出数据库服务器配置 (database_servers)  
- 导出系统设置 (system_settings)
- 生成 `exported_data.json` 文件

**使用方法**:
```bash
# Windows环境
cmd.exe /c "python scripts/export_current_data.py"

# Linux/Mac环境
python scripts/export_current_data.py
```

**输出**: `scripts/exported_data.json`

### 2. `init_database_with_defaults.py` - 数据库初始化脚本
**用途**: 为新程序安装初始化数据库，包含默认配置  
**功能**:
- 创建必要的数据库表
- 插入默认菜单配置
- 插入默认数据库服务器配置
- 插入默认系统设置
- 支持增量初始化（不覆盖现有数据）

**使用方法**:
```bash
# 基本初始化（默认路径: data/onetools.db）
python scripts/init_database_with_defaults.py

# 指定数据库路径
python scripts/init_database_with_defaults.py --db-path /path/to/database.db

# 强制重新初始化（覆盖现有数据）
python scripts/init_database_with_defaults.py --force
```

**参数说明**:
- `--db-path`: 指定数据库文件路径
- `--force`: 强制覆盖现有数据

### 3. `migrate_from_exported_data.py` - 数据迁移脚本
**用途**: 从导出的数据文件迁移到新数据库  
**功能**:
- 读取 `exported_data.json` 文件
- 创建新数据库并导入数据
- 保持原有创建时间，更新修改时间
- 支持指定目标数据库路径

**使用方法**:
```bash
# 基本迁移（使用默认导出文件）
python scripts/migrate_from_exported_data.py

# 指定导出文件和目标数据库
python scripts/migrate_from_exported_data.py --export-file custom_export.json --target-db new_database.db

# 强制覆盖现有数据库
python scripts/migrate_from_exported_data.py --force
```

**参数说明**:
- `--export-file`: 指定导出数据文件路径（默认: scripts/exported_data.json）
- `--target-db`: 指定目标数据库路径（默认: data/onetools_migrated.db）
- `--force`: 强制覆盖现有目标数据库

## 典型使用场景

### 场景1: 新程序初始化
当第一次安装 OneTools 程序时：

```bash
python scripts/init_database_with_defaults.py
```

这将创建包含默认配置的数据库，包括：
- 8个默认菜单项（事务查询、自定义查询、设置等）
- 1个默认数据库服务器（localhost\SQLEXPRESS）
- 6个默认系统设置

### 场景2: 从现有系统迁移
当需要从现有系统迁移配置时：

```bash
# 1. 先导出现有数据
python scripts/export_current_data.py

# 2. 迁移到新数据库
python scripts/migrate_from_exported_data.py --target-db data/onetools.db
```

### 场景3: 备份和恢复
备份当前配置：
```bash
python scripts/export_current_data.py
# 保存 exported_data.json 文件
```

恢复配置：
```bash
python scripts/migrate_from_exported_data.py --export-file backup_exported_data.json
```

## 默认初始化数据

### 菜单配置 (8项)
1. **事务查询** (`/transaction-query`) - TransactionOutlined
2. **自定义查询** (`/custom-query`) - CodeOutlined  
3. **保存的查询** (`/saved-queries`) - SaveOutlined
4. **用户查询** (`/user-query`) - UserOutlined
5. **数据库配置** (`/database-config`) - DatabaseOutlined
6. **菜单配置** (`/menu-config`) - MenuOutlined
7. **系统设置** (`/settings`) - SettingOutlined
8. **关于** (`/about`) - InfoCircleOutlined

### 数据库服务器配置 (1项)
- **服务器**: `localhost\SQLEXPRESS`
- **端口**: 1433
- **描述**: 本地SQL Server Express实例

### 系统设置 (6项)
- `app.name`: OneTools
- `app.version`: 2.0.0
- `database.max_query_history`: 1000
- `database.default_timeout`: 30
- `ui.theme`: light
- `ui.language`: zh-CN

## 数据库表结构

### menu_configurations
- `id`: 主键，自增
- `key`: 菜单键，唯一
- `label`: 显示标签
- `icon`: 图标名称
- `path`: 路由路径
- `component`: 组件名称
- `position`: 位置 (top/bottom)
- `section`: 区域 (main/system)
- `order`: 排序
- `enabled`: 是否启用
- `created_at`: 创建时间
- `updated_at`: 更新时间

### database_servers
- `id`: 主键，自增
- `name`: 服务器名称，唯一
- `port`: 端口号
- `is_enabled`: 是否启用
- `description`: 描述
- `order`: 排序
- `created_at`: 创建时间
- `updated_at`: 更新时间

### system_settings
- `id`: 主键，自增
- `key`: 设置键，唯一
- `value`: 设置值
- `description`: 描述
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 注意事项

1. **运行环境**: 脚本需要在项目根目录下运行
2. **数据库路径**: 默认数据库路径为 `data/onetools.db`
3. **备份建议**: 在运行迁移脚本前建议备份现有数据库
4. **权限要求**: 确保对数据库文件和目录有读写权限
5. **依赖要求**: 脚本仅依赖Python标准库，无需额外安装包

## 故障排除

### 常见问题

1. **找不到数据库文件**
   - 检查数据库路径是否正确
   - 确保 `data` 目录存在

2. **权限错误**
   - 检查对数据库文件的读写权限
   - 在Windows下可能需要管理员权限

3. **编码问题**
   - 确保系统支持UTF-8编码
   - 检查导出的JSON文件编码

4. **表已存在错误**
   - 使用 `--force` 参数强制覆盖
   - 或者手动删除现有数据库文件

### 日志和调试
所有脚本都包含详细的控制台输出，可以根据输出信息判断执行状态和错误原因。