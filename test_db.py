#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/onetools.db')
cursor = conn.cursor()

# 添加测试数据
cursor.execute('INSERT INTO database_servers (name, "order") VALUES (?, ?)', ('TestServer1', 1))
cursor.execute('INSERT INTO database_servers (name, "order") VALUES (?, ?)', ('TestServer2', 2))
conn.commit()

# 查看添加的数据
cursor.execute('SELECT * FROM database_servers')
print('Added servers:', cursor.fetchall())

conn.close()
