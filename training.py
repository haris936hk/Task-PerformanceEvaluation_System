import sqlite3
from database import get_conn

def add_resource(title, url, added_by):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO training(title,url,added_by) VALUES(?,?,?)", (title,url,added_by))
    conn.commit(); conn.close()

def list_resources():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM training")
    res = c.fetchall(); conn.close()
    return res