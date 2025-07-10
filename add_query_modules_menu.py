import sqlite3
from datetime import datetime

def add_query_modules_menu():
    """为查询模块添加菜单配置"""
    conn = sqlite3.connect('data/onetools.db')
    cursor = conn.cursor()
    
    # 查询模块菜单配置
    query_modules = [
        {
            "key": "/transaction-query",
            "label": "事务查询",
            "icon": "TransactionOutlined",
            "path": "/transaction-query",
            "component": "TransactionQuery",
            "position": "top",
            "section": "main",
            "order": 1,
            "enabled": True
        },
        {
            "key": "/custom-query",
            "label": "自定义查询",
            "icon": "CodeOutlined",
            "path": "/custom-query",
            "component": "CustomQuery",
            "position": "top",
            "section": "main",
            "order": 2,
            "enabled": True
        },
        {
            "key": "/user-query",
            "label": "用户查询",
            "icon": "UserOutlined",
            "path": "/user-query",
            "component": "UserQuery",
            "position": "top",
            "section": "main",
            "order": 3,
            "enabled": True
        }
    ]
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        for module in query_modules:
            # 检查是否已存在
            cursor.execute("SELECT COUNT(*) FROM menu_configurations WHERE key = ?", (module["key"],))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                cursor.execute("""
                    INSERT INTO menu_configurations (key, label, icon, path, component, position, section, "order", enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    module["key"],
                    module["label"],
                    module["icon"],
                    module["path"],
                    module["component"],
                    module["position"],
                    module["section"],
                    module["order"],
                    module["enabled"],
                    current_time,
                    current_time
                ))
                print(f"Added menu configuration: {module['key']} - {module['label']}")
            else:
                print(f"Menu configuration already exists: {module['key']} - {module['label']}")
        
        conn.commit()
        print("Successfully added query modules menu configurations")
        
        # 显示所有菜单配置
        cursor.execute("SELECT key, label, icon, path, component, position, section, \"order\", enabled FROM menu_configurations ORDER BY section, \"order\"")
        rows = cursor.fetchall()
        print("\nCurrent menu configurations:")
        for row in rows:
            print(f"  {row[0]} - {row[1]} ({row[2]}) - {row[4]} - {row[5]}/{row[6]} - Order: {row[7]}")
        
    except Exception as e:
        print(f"Error adding menu configurations: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_query_modules_menu()