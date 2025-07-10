import sqlite3

conn = sqlite3.connect('data/onetools.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM database_servers WHERE id = 1')
result = cursor.fetchone()
print(f'Database server with id=1: {result}')

cursor.execute('SELECT * FROM database_servers')
all_servers = cursor.fetchall()
print(f'All database servers: {all_servers}')

conn.close()