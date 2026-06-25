import mysql.connector
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="2004",
    database="expense_tracker"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS budget(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL
)
""")