# 数据库架构重构说明

## ⚠️ 重要变更通知

项目的数据库管理架构已进行重大重构，解决了之前存在的数据库初始化双重机制问题。

## 🔄 变更内容

### 问题背景
之前项目同时使用两种数据库初始化方式：
1. 直接使用 `Base.metadata.create_all()` 
2. Alembic 迁移系统

这导致了数据库版本管理的不一致性和潜在的生产环境问题。

### 解决方案
现在项目采用统一的 **Alembic 迁移系统** 进行数据库版本管理：

#### ✅ 新的工作流程
```bash
# 数据库初始化（推荐）
make db-init

# 模型变更后创建迁移
make db-migrate

# 应用迁移
make db-upgrade
```

#### ❌ 废弃的方式
```python
# 不再推荐使用
await init_db(db)  # 已标记为 DEPRECATED
Base.metadata.create_all()  # 仅测试环境使用
```

## 🛠️ 开发者迁移指南

### 1. 现有开发者
如果你已经在使用这个项目：
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新初始化数据库
make db-reset  # 仅开发环境！

# 3. 使用新的初始化方式
make db-init
```

### 2. 新开发者
```bash
# 完整的环境设置
make setup-dev
make db-init
make start-dev
```

### 3. 模型变更流程
```bash
# 1. 修改 app/models/*.py 文件
# 2. 生成迁移脚本
make db-migrate
# 3. 检查生成的迁移脚本
# 4. 应用迁移
make db-upgrade
```

## 📁 新增的文件

### 数据库迁移
- `alembic/versions/666ec5a24c4c_initial_database_schema.py` - 初始数据库模式
- `docs/DATABASE_MIGRATION_GUIDE.md` - 详细的迁移指南

### 修改的文件
- `scripts/init_db.py` - 重构为使用 Alembic
- `app/db/crud.py` - 分离数据初始化逻辑，标记废弃函数
- `Makefile` - 添加完整的数据库管理命令

## 🎯 新增的 Make 命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `make db-init` | 🗃️ 数据库初始化 | 应用迁移 + 初始化默认数据 |
| `make db-migrate` | 📝 创建迁移 | 基于模型变更生成迁移脚本 |
| `make db-upgrade` | ⬆️ 应用迁移 | 将数据库升级到最新版本 |
| `make db-current` | 📍 当前版本 | 显示当前数据库版本 |
| `make db-history` | 📋 迁移历史 | 查看所有迁移记录 |
| `make db-downgrade` | ⬇️ 回滚迁移 | 回滚到指定版本 |
| `make db-reset` | ⚠️ 重置数据库 | 完全重置（危险操作） |

## 💡 最佳实践

### 开发环境
```bash
# 日常开发流程
git pull origin main          # 拉取最新代码
make db-upgrade               # 应用新的迁移
make start-dev                # 启动开发服务器

# 修改模型后
make db-migrate               # 生成迁移
make db-upgrade               # 应用迁移
```

### 生产环境
```bash
# 部署流程
alembic upgrade head          # 应用迁移
python scripts/init_db.py     # 初始化默认数据（如果需要）
```

## ⚠️ 注意事项

1. **测试环境例外**: 测试环境继续使用 `create_all()` 以提高性能
2. **备份重要**: 生产环境应用迁移前务必备份数据库
3. **团队协作**: 迁移脚本需要通过代码 review
4. **版本控制**: 所有迁移文件都应提交到版本控制系统

## 🚀 优势

- ✅ **一致性**: 统一的数据库版本管理
- ✅ **可回滚**: 支持安全的数据库模式回滚  
- ✅ **版本控制**: 所有变更都有历史记录
- ✅ **团队协作**: 数据库变更可代码审查
- ✅ **自动化**: 支持 CI/CD 集成

## 📚 更多信息

详细的数据库管理指南请参考：[DATABASE_MIGRATION_GUIDE.md](./DATABASE_MIGRATION_GUIDE.md)