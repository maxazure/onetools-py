## Environment
- 本项目是运行在wsl环境下

## Windows Commands
- 运行 python npm node pip netstat 等命令时 要使用cmd.exe 在windows下运行
- 连接 sql server时，需要在windows 环境下运行 使用 cmd.exe 启动python程序

## Chrome Debugging
- 在启动chrome 进行调试的时候 需要使他在局域网可用，你需要使用局域网ip访问它 192.168.31.129

## Frontend Architecture Decisions

### SQL编辑器统一化 (2025-01-11)
**决策**: 统一使用Monaco Editor作为唯一的SQL编辑器
**原因**: 
- 之前项目同时使用Monaco Editor和CodeMirror两套编辑器，造成：
  - 用户体验不一致
  - 依赖冗余，增加打包体积
  - 维护复杂性高
- Monaco Editor功能更完整，有工具栏、快捷键、性能优化
**实施**:
- 统一使用 `/frontend/src/components/SqlEditor/SqlEditor.tsx` 组件
- 移除CodeMirror相关依赖：`@codemirror/lang-sql`, `@codemirror/theme-one-dark`, `@uiw/react-codemirror`
- QueryFormBuilder中的SQL编辑器已替换为SqlEditor组件
**影响范围**:
- 自定义查询页面：已使用Monaco Editor (SqlEditor)
- 保存查询页面：已使用Monaco Editor (SqlEditor) 
- 查询表单构建器：已从CodeMirror替换为Monaco Editor (SqlEditor)

### 查询表单字段匹配类型优化 (2025-01-11)
**改进**: 根据字段类型智能选择匹配操作符
- 数字字段：=, <>, >, <, >=, <=, BETWEEN, IN, IS NULL等
- 文本字段：=, LIKE, 开头匹配, 结尾匹配, 包含, IN等  
- 日期字段：=, >, <, >=, <=, BETWEEN等
- 选择器字段：=, <>, IN等
- 字段类型变更时自动选择合适的默认匹配类型

### 查询表单数据源配置 (2025-01-11)
**功能**: 为select字段添加SQL数据源支持
- 支持静态选项和SQL查询两种数据源类型
- SQL数据源可配置查询语句、值字段、显示字段
- 提供测试数据源功能
- 内置使用示例和帮助信息