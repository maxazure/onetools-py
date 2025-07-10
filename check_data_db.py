import sqlite3

# 检查正确的数据库路径
db_path = 'data/onetools.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"检查数据库: {db_path}")
print("\n所有表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    print(f'表名: {table[0]}')

print("\n菜单相关表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%menu%'")
menu_tables = cursor.fetchall()

if menu_tables:
    for table in menu_tables:
        print(f'表名: {table[0]}')
        # 显示表结构
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f'  表结构:')
        for col in columns:
            print(f'    {col[1]} ({col[2]})')
        
        # 显示表数据
        cursor.execute(f"SELECT * FROM {table[0]}")
        rows = cursor.fetchall()
        print(f'  数据行数: {len(rows)}')
        if rows:
            print(f'  前5行数据:')
            for i, row in enumerate(rows[:5]):
                print(f'    {i+1}: {row}')
        print()
else:
    print('未找到菜单相关的表')

conn.close()