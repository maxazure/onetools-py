"""
数据库迁移脚本 - 创建动态查询表单相关表
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_sqlite_manager
from app.core.logging import get_logger
from app.models.tables import Base, QueryForm, QueryFormHistory

logger = get_logger(__name__)


async def create_tables():
    """创建动态查询表单相关的数据库表"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        # 创建表结构
        logger.info("开始创建动态查询表单相关数据库表...")
        
        async with sqlite_manager.get_connection() as conn:
            # 创建query_forms表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS query_forms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    form_name VARCHAR(255) NOT NULL UNIQUE,
                    form_description TEXT,
                    sql_template TEXT NOT NULL,
                    form_config JSON NOT NULL,
                    target_database VARCHAR(255),
                    is_active BOOLEAN DEFAULT 1,
                    created_by VARCHAR(100) DEFAULT 'system',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建query_form_history表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS query_form_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    form_id INTEGER NOT NULL,
                    query_params JSON,
                    executed_sql TEXT,
                    execution_time REAL,
                    row_count INTEGER,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    user_id VARCHAR(100) DEFAULT 'system',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (form_id) REFERENCES query_forms (id)
                )
            """)
            
            # 创建索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_forms_name 
                ON query_forms (form_name)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_forms_active 
                ON query_forms (is_active)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_form_history_form_id 
                ON query_form_history (form_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_form_history_created_at 
                ON query_form_history (created_at)
            """)
            
            await conn.commit()
            
        logger.info("动态查询表单数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        return False


async def insert_sample_data():
    """插入示例数据"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        logger.info("开始插入示例数据...")
        
        async with sqlite_manager.get_connection() as conn:
            # 示例查询表单1：用户查询
            sample_form_1 = {
                "form_name": "用户信息查询",
                "form_description": "根据用户ID、姓名或邮箱查询用户信息",
                "sql_template": """
                    SELECT user_id, username, email, status, created_date 
                    FROM users 
                    WHERE (@user_id IS NULL OR user_id = @user_id)
                      AND (@username IS NULL OR username LIKE '%' + @username + '%')
                      AND (@email IS NULL OR email LIKE '%' + @email + '%')
                      AND (@status IS NULL OR status = @status)
                      AND (@date_from IS NULL OR created_date >= @date_from)
                      AND (@date_to IS NULL OR created_date <= @date_to)
                    ORDER BY created_date DESC
                """,
                "form_config": """
                {
                    "title": "用户信息查询",
                    "description": "查询系统中的用户信息，支持多条件组合查询",
                    "fields": [
                        {
                            "parameter": "@user_id",
                            "label": "用户ID",
                            "field_type": "number",
                            "required": false,
                            "match_type": "exact",
                            "placeholder": "请输入用户ID",
                            "order": 1
                        },
                        {
                            "parameter": "@username",
                            "label": "用户名",
                            "field_type": "text",
                            "required": false,
                            "match_type": "like",
                            "placeholder": "请输入用户名（支持模糊查询）",
                            "order": 2
                        },
                        {
                            "parameter": "@email",
                            "label": "邮箱",
                            "field_type": "email",
                            "required": false,
                            "match_type": "like",
                            "placeholder": "请输入邮箱地址",
                            "order": 3
                        },
                        {
                            "parameter": "@status",
                            "label": "状态",
                            "field_type": "select",
                            "required": false,
                            "match_type": "exact",
                            "placeholder": "请选择用户状态",
                            "data_source": {
                                "type": "static",
                                "options": [
                                    {"label": "活跃", "value": "Active"},
                                    {"label": "禁用", "value": "Disabled"},
                                    {"label": "暂停", "value": "Suspended"}
                                ]
                            },
                            "order": 4
                        },
                        {
                            "parameter": "@date_from",
                            "label": "创建日期从",
                            "field_type": "date",
                            "required": false,
                            "match_type": "greater_equal",
                            "placeholder": "请选择开始日期",
                            "order": 5
                        },
                        {
                            "parameter": "@date_to",
                            "label": "创建日期到",
                            "field_type": "date",
                            "required": false,
                            "match_type": "less_equal",
                            "placeholder": "请选择结束日期",
                            "order": 6
                        }
                    ],
                    "layout": {
                        "columns": 3,
                        "button_position": "bottom",
                        "label_width": "120px",
                        "field_spacing": "16px"
                    }
                }
                """,
                "target_database": "UserManagement",
                "is_active": 1
            }
            
            # 示例查询表单2：销售数据查询
            sample_form_2 = {
                "form_name": "销售数据查询",
                "form_description": "查询指定时间范围内的销售数据统计",
                "sql_template": """
                    SELECT 
                        product_name,
                        SUM(quantity) as total_quantity,
                        SUM(amount) as total_amount,
                        COUNT(*) as order_count,
                        AVG(amount) as avg_amount
                    FROM sales_orders 
                    WHERE (@product_name IS NULL OR product_name LIKE '%' + @product_name + '%')
                      AND (@start_date IS NULL OR order_date >= @start_date)
                      AND (@end_date IS NULL OR order_date <= @end_date)
                      AND (@min_amount IS NULL OR amount >= @min_amount)
                      AND (@max_amount IS NULL OR amount <= @max_amount)
                    GROUP BY product_name
                    HAVING COUNT(*) >= ISNULL(@min_orders, 0)
                    ORDER BY total_amount DESC
                """,
                "form_config": """
                {
                    "title": "销售数据查询",
                    "description": "查询产品销售统计数据，支持按产品名称、时间范围和金额范围筛选",
                    "fields": [
                        {
                            "parameter": "@product_name",
                            "label": "产品名称",
                            "field_type": "text",
                            "required": false,
                            "match_type": "like",
                            "placeholder": "请输入产品名称（支持模糊查询）",
                            "order": 1
                        },
                        {
                            "parameter": "@start_date",
                            "label": "开始日期",
                            "field_type": "date",
                            "required": false,
                            "match_type": "greater_equal",
                            "placeholder": "请选择开始日期",
                            "order": 2
                        },
                        {
                            "parameter": "@end_date",
                            "label": "结束日期",
                            "field_type": "date",
                            "required": false,
                            "match_type": "less_equal",
                            "placeholder": "请选择结束日期",
                            "order": 3
                        },
                        {
                            "parameter": "@min_amount",
                            "label": "最小金额",
                            "field_type": "number",
                            "required": false,
                            "match_type": "greater_equal",
                            "placeholder": "请输入最小金额",
                            "validation": {"min": 0},
                            "order": 4
                        },
                        {
                            "parameter": "@max_amount",
                            "label": "最大金额",
                            "field_type": "number",
                            "required": false,
                            "match_type": "less_equal",
                            "placeholder": "请输入最大金额",
                            "validation": {"min": 0},
                            "order": 5
                        },
                        {
                            "parameter": "@min_orders",
                            "label": "最少订单数",
                            "field_type": "number",
                            "required": false,
                            "default_value": "1",
                            "match_type": "greater_equal",
                            "placeholder": "请输入最少订单数",
                            "validation": {"min": 1},
                            "order": 6
                        }
                    ],
                    "layout": {
                        "columns": 2,
                        "button_position": "bottom",
                        "label_width": "100px",
                        "field_spacing": "16px"
                    }
                }
                """
            }
            
            # 插入示例表单
            await conn.execute("""
                INSERT OR IGNORE INTO query_forms 
                (form_name, form_description, sql_template, form_config, target_database, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sample_form_1["form_name"],
                sample_form_1["form_description"],
                sample_form_1["sql_template"],
                sample_form_1["form_config"],
                sample_form_1["target_database"],
                sample_form_1["is_active"]
            ))
            
            await conn.execute("""
                INSERT OR IGNORE INTO query_forms 
                (form_name, form_description, sql_template, form_config, target_database, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sample_form_2["form_name"],
                sample_form_2["form_description"],
                sample_form_2["sql_template"],
                sample_form_2["form_config"],
                None,  # target_database
                1      # is_active
            ))
            
            await conn.commit()
            
        logger.info("示例数据插入成功")
        return True
        
    except Exception as e:
        logger.error(f"插入示例数据失败: {e}")
        return False


async def verify_tables():
    """验证表创建是否成功"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        logger.info("开始验证数据库表...")
        
        async with sqlite_manager.get_connection() as conn:
            # 检查query_forms表
            result = await conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='query_forms'
            """)
            if not result.fetchone():
                logger.error("query_forms表不存在")
                return False
            
            # 检查query_form_history表
            result = await conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='query_form_history'
            """)
            if not result.fetchone():
                logger.error("query_form_history表不存在")
                return False
            
            # 检查表结构
            result = await conn.execute("PRAGMA table_info(query_forms)")
            columns = [row[1] for row in result.fetchall()]
            expected_columns = [
                'id', 'form_name', 'form_description', 'sql_template', 
                'form_config', 'target_database', 'is_active', 
                'created_by', 'created_at', 'updated_at'
            ]
            
            for col in expected_columns:
                if col not in columns:
                    logger.error(f"query_forms表缺少列: {col}")
                    return False
            
            # 检查数据
            result = await conn.execute("SELECT COUNT(*) FROM query_forms")
            count = result.fetchone()[0]
            logger.info(f"query_forms表中有 {count} 条记录")
            
        logger.info("数据库表验证成功")
        return True
        
    except Exception as e:
        logger.error(f"验证数据库表失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("动态查询表单数据库迁移脚本")
    print("=" * 60)
    
    # 创建表
    print("1. 创建数据库表...")
    if not await create_tables():
        print("❌ 创建数据库表失败")
        return False
    print("✅ 数据库表创建成功")
    
    # 插入示例数据
    print("\n2. 插入示例数据...")
    if not await insert_sample_data():
        print("❌ 插入示例数据失败")
        return False
    print("✅ 示例数据插入成功")
    
    # 验证表
    print("\n3. 验证数据库表...")
    if not await verify_tables():
        print("❌ 验证数据库表失败")
        return False
    print("✅ 数据库表验证成功")
    
    print("\n" + "=" * 60)
    print("🎉 动态查询表单数据库迁移完成！")
    print("=" * 60)
    
    print("\n📋 迁移摘要:")
    print("  • 创建了 query_forms 表（查询表单配置）")
    print("  • 创建了 query_form_history 表（执行历史记录）")
    print("  • 创建了相关索引用于性能优化")
    print("  • 插入了 2 个示例查询表单")
    print("\n🚀 现在可以通过 /query-forms 页面管理动态查询表单了！")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        sys.exit(1)