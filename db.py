import sqlite3
con = sqlite3.connect("app.db")
cur = con.cursor()

# Create Tables
sql = """
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        timestamp DATETIME NOT NULL,
        power NUMERIC NOT NULL
    )
"""
cur.executescript(sql)

con.commit()
con.close()