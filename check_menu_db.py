import sqlite3

conn = sqlite3.connect('onetools.db')
cursor = conn.cursor()

print("检查菜单项数据库内容:")
cursor.execute('SELECT id, label FROM menu_configurations ORDER BY id')
rows = cursor.fetchall()

print('菜单项列表:')
for row in rows:
    print(f'ID: {row[0]}, 标签: {row[1]}')

conn.close()