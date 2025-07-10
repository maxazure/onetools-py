import sqlite3

conn = sqlite3.connect('onetools.db')
cursor = conn.cursor()

print("检查数据库中的所有表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('数据库表列表:')
for table in tables:
    print(f'表名: {table[0]}')

print("\n检查是否存在菜单相关的表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%menu%'")
menu_tables = cursor.fetchall()

if menu_tables:
    print('菜单相关表:')
    for table in menu_tables:
        print(f'表名: {table[0]}')
        # 显示表结构
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f'  表结构:')
        for col in columns:
            print(f'    {col[1]} ({col[2]})')
        print()
else:
    print('未找到菜单相关的表')

conn.close()