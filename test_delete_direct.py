import asyncio
import sqlite3
from app.core.database import get_sqlite_manager

async def test_delete_directly():
    """直接测试删除操作"""
    # 首先检查数据库中的菜单项
    db_path = 'data/onetools.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("删除前的菜单项:")
    cursor.execute('SELECT id, label FROM menu_configurations ORDER BY id')
    rows = cursor.fetchall()
    for row in rows:
        print(f'ID: {row[0]}, 标签: {row[1]}')
    
    # 选择一个要删除的ID
    if rows:
        delete_id = rows[0][0]  # 取第一个ID
        print(f"\n尝试删除ID: {delete_id}")
        
        # 使用SQLite管理器删除
        sqlite_manager = get_sqlite_manager()
        try:
            result = await sqlite_manager.execute_query(
                "DELETE FROM menu_configurations WHERE id = ?", 
                (delete_id,)
            )
            print(f"删除操作结果: {result}")
            print(f"影响行数: {result.rowcount}")
        except Exception as e:
            print(f"删除失败: {e}")
        
        # 再次检查数据库
        print("\n删除后的菜单项:")
        cursor.execute('SELECT id, label FROM menu_configurations ORDER BY id')
        rows = cursor.fetchall()
        for row in rows:
            print(f'ID: {row[0]}, 标签: {row[1]}')
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(test_delete_directly())