import sqlite3

conn = sqlite3.connect('data/onetools.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM menu_configurations')
rows = cursor.fetchall()
print('Current menu configurations:')
for row in rows:
    print(row)
conn.close()