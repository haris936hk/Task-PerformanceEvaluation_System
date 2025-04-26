import sqlite3
from database import get_conn

def submit_feedback(from_user, message):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO feedback(from_user,message) VALUES(?,?)", (from_user,message))
    conn.commit(); conn.close()

def get_feedback():  # manager view
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id,message,timestamp FROM feedback ORDER BY timestamp DESC")
    fb = c.fetchall(); conn.close()
    return fb