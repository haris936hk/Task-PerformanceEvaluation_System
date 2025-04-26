import sqlite3
from database import get_conn
from datetime import datetime

def create_task(title, desc, assigned_to, due_date, type_='task'):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO tasks(title,description,assigned_to,type,due_date) VALUES(?,?,?,?,?)", (title,desc,assigned_to,type_,due_date))
    conn.commit(); conn.close()

def get_tasks(user_id, include_completed=True):
    conn = get_conn(); c = conn.cursor()
    q = "SELECT * FROM tasks WHERE assigned_to=?"
    params = [user_id]
    if not include_completed:
        q += " AND completed=0"
    c.execute(q, params)
    tasks = c.fetchall(); conn.close()
    return tasks

def toggle_complete(task_id, user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE tasks SET completed=1-completed WHERE id=? AND assigned_to=?", (task_id,user_id))
    conn.commit(); conn.close()