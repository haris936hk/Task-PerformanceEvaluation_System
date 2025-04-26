import sqlite3
from database import get_conn

def earn_points(user_id, pts):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE points SET balance=balance+? WHERE user_id=?", (pts,user_id))
    conn.commit(); conn.close()

def get_balance(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT balance FROM points WHERE user_id=?", (user_id,))
    bal = c.fetchone()[0]; conn.close()
    return bal

def redeem_reward(user_id, reward_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT cost FROM rewards WHERE id=?", (reward_id,))
    cost = c.fetchone()[0]
    bal = get_balance(user_id)
    if bal >= cost:
        c.execute("UPDATE points SET balance=balance-? WHERE user_id=?", (cost,user_id))
        conn.commit()
    conn.close()

def list_rewards():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM rewards")
    r = c.fetchall(); conn.close()
    return r

def add_reward(name, cost, created_by):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO rewards(name,cost,created_by) VALUES(?,?,?)", (name,cost,created_by))
    conn.commit(); conn.close()