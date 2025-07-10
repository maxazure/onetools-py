import pyodbc

print('pyodbc version:', pyodbc.version)
print('Available drivers:', pyodbc.drivers())

# 测试连接
try:
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=OneToolsDb;Trusted_Connection=yes;"
    conn = pyodbc.connect(conn_str)
    print("SQL Server connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")