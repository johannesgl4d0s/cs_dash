import sqlite3
con = sqlite3.connect("app.db")
cur = con.cursor()

# Create Tables
sql = """
    DROP TABLE IF EXISTS history;
    CREATE TABLE IF NOT EXISTS history (
        user_id INTEGER NOT NULL,
        timestamp DATETIME NOT NULL,
        power NUMERIC default 0,
        primary key (user_id, timestamp)
    )
"""
cur.executescript(sql)

con.commit()
con.close()