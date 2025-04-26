import flet as ft
import re
from passlib.hash import bcrypt
from database import get_conn
from ui_utils import validate_username, validate_password

SESSIONS = {}

def signup(username: str, password: str, role: str):
    if not validate_username(username) or not validate_password(password):
        raise ValueError("Invalid credentials format")
    pw_hash = bcrypt.hash(password)
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)", (username,pw_hash,role))
    uid = c.lastrowid
    c.execute("INSERT INTO points(user_id) VALUES(?)", (uid,))
    conn.commit(); conn.close()
    return uid

def login(username: str, password: str):
    conn = get_conn(); c=conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone(); conn.close()
    if not user or not bcrypt.verify(password,user['password_hash']):
        return None
    # create session token
    token = bcrypt.hash(f"{username}{ft.time.time()}")
    SESSIONS[token] = user['id']
    return token

def get_user(token: str):
    uid = SESSIONS.get(token)
    if not uid: return None
    conn = get_conn(); c=conn.cursor()
    c.execute("SELECT id,username,role,team_id FROM users WHERE id=?",(uid,))
    user = c.fetchone(); conn.close()
    return user