import sqlite3
from database import get_conn
from datetime import datetime

def log_wellness(user_id, stress, workload, notes):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO wellness(user_id,stress_level,workload,notes) VALUES(?,?,?,?)", (user_id,stress,workload,notes))
    conn.commit(); conn.close()

def get_wellness(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM wellness WHERE user_id=? ORDER BY timestamp", (user_id,))
    data = c.fetchall(); conn.close()
    return data
