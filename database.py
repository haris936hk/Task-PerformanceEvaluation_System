import sqlite3
from sqlite3 import Connection

DB_PATH = "app.db"

def get_conn() -> Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize tables
def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('manager','user')) NOT NULL,
        team_id INTEGER,
        FOREIGN KEY(team_id) REFERENCES teams(id)
    )
    """)
    # Teams
    c.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    """)
    # Tasks & Goals
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        assigned_to INTEGER,
        completed INTEGER DEFAULT 0,
        type TEXT CHECK(type IN ('task','goal')) NOT NULL,
        due_date TEXT,
        feedback TEXT,
        FOREIGN KEY(assigned_to) REFERENCES users(id)
    )
    """)
    # Wellness
    c.execute("""
    CREATE TABLE IF NOT EXISTS wellness (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        stress_level INTEGER,
        workload TEXT,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # Feedback
    c.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY,
        from_user INTEGER,
        message TEXT NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # Training
    c.execute("""
    CREATE TABLE IF NOT EXISTS training (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        added_by INTEGER,
        FOREIGN KEY(added_by) REFERENCES users(id)
    )
    """)
    # Rewards
    c.execute("""
    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        cost INTEGER NOT NULL,
        created_by INTEGER,
        FOREIGN KEY(created_by) REFERENCES users(id)
    )
    """)
    # Recognition points
    c.execute("""
    CREATE TABLE IF NOT EXISTS points (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()