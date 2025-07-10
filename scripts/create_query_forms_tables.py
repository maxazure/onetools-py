"""
Simple database migration script for query forms tables
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_sqlite_manager
from app.core.logging import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


async def create_tables():
    """Create query forms related database tables"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        print("Creating query forms tables...")
        
        async with sqlite_manager.get_connection() as conn:
            # Create query_forms table
            await conn.execute(text("""
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
            """))
            
            # Create query_form_history table
            await conn.execute(text("""
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
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_query_forms_name 
                ON query_forms (form_name)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_query_forms_active 
                ON query_forms (is_active)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_query_form_history_form_id 
                ON query_form_history (form_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_query_form_history_created_at 
                ON query_form_history (created_at)
            """))
            
            await conn.commit()
            
        print("SUCCESS: Query forms tables created successfully")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        return False


async def insert_sample_data():
    """Insert sample data"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        print("Inserting sample data...")
        
        async with sqlite_manager.get_connection() as conn:
            # Sample form 1: User query
            form_config_1 = """{
                "title": "User Info Query",
                "description": "Query user information by ID, name or email",
                "fields": [
                    {
                        "parameter": "@user_id",
                        "label": "User ID",
                        "field_type": "number",
                        "required": false,
                        "match_type": "exact",
                        "placeholder": "Enter user ID",
                        "order": 1
                    },
                    {
                        "parameter": "@username",
                        "label": "Username",
                        "field_type": "text",
                        "required": false,
                        "match_type": "like",
                        "placeholder": "Enter username (fuzzy search)",
                        "order": 2
                    },
                    {
                        "parameter": "@email",
                        "label": "Email",
                        "field_type": "email",
                        "required": false,
                        "match_type": "like",
                        "placeholder": "Enter email address",
                        "order": 3
                    },
                    {
                        "parameter": "@status",
                        "label": "Status",
                        "field_type": "select",
                        "required": false,
                        "match_type": "exact",
                        "placeholder": "Select status",
                        "data_source": {
                            "type": "static",
                            "options": [
                                {"label": "Active", "value": "Active"},
                                {"label": "Disabled", "value": "Disabled"},
                                {"label": "Suspended", "value": "Suspended"}
                            ]
                        },
                        "order": 4
                    }
                ],
                "layout": {
                    "columns": 2,
                    "button_position": "bottom",
                    "label_width": "120px",
                    "field_spacing": "16px"
                }
            }"""
            
            sql_template_1 = """
                SELECT user_id, username, email, status, created_date 
                FROM users 
                WHERE (@user_id IS NULL OR user_id = @user_id)
                  AND (@username IS NULL OR username LIKE '%' + @username + '%')
                  AND (@email IS NULL OR email LIKE '%' + @email + '%')
                  AND (@status IS NULL OR status = @status)
                ORDER BY created_date DESC
            """
            
            await conn.execute(text("""
                INSERT OR IGNORE INTO query_forms 
                (form_name, form_description, sql_template, form_config, target_database, is_active)
                VALUES (:form_name, :form_description, :sql_template, :form_config, :target_database, :is_active)
            """), {
                "form_name": "User Info Query",
                "form_description": "Query user information by multiple conditions",
                "sql_template": sql_template_1,
                "form_config": form_config_1,
                "target_database": "UserManagement",
                "is_active": True
            })
            
            await conn.commit()
            
        print("SUCCESS: Sample data inserted successfully")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to insert sample data: {e}")
        return False


async def verify_tables():
    """Verify table creation"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        print("Verifying tables...")
        
        async with sqlite_manager.get_connection() as conn:
            # Check query_forms table
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='query_forms'
            """))
            if not result.fetchone():
                print("ERROR: query_forms table not found")
                return False
            
            # Check query_form_history table
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='query_form_history'
            """))
            if not result.fetchone():
                print("ERROR: query_form_history table not found")
                return False
            
            # Check data
            result = await conn.execute(text("SELECT COUNT(*) FROM query_forms"))
            count = result.fetchone()[0]
            print(f"INFO: Found {count} records in query_forms table")
            
        print("SUCCESS: Tables verified successfully")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to verify tables: {e}")
        return False


async def main():
    """Main function"""
    print("=" * 60)
    print("Query Forms Database Migration Script")
    print("=" * 60)
    
    # Create tables
    if not await create_tables():
        return False
    
    # Insert sample data
    if not await insert_sample_data():
        return False
    
    # Verify tables
    if not await verify_tables():
        return False
    
    print("\n" + "=" * 60)
    print("SUCCESS: Query forms database migration completed!")
    print("=" * 60)
    print("\nMigration Summary:")
    print("  - Created query_forms table")
    print("  - Created query_form_history table")
    print("  - Created performance indexes")
    print("  - Inserted sample data")
    print("\nYou can now access the query forms management at /query-forms")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nMigration failed with error: {e}")
        sys.exit(1)