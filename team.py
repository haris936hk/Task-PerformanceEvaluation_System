import sqlite3
from database import get_conn

def create_team(name, manager_id, member_ids):
    conn = get_conn(); c = conn.cursor()
    # insert team
    c.execute("INSERT INTO teams(name) VALUES(?)", (name,))
    team_id = c.lastrowid
    # assign manager and members
    for uid in [manager_id] + member_ids:
        c.execute("UPDATE users SET team_id=? WHERE id=?", (team_id, uid))
    conn.commit(); conn.close()
    return team_id

def edit_team(team_id, new_name=None, add_ids=[], remove_ids=[]):
    conn = get_conn(); c = conn.cursor()
    if new_name:
        c.execute("UPDATE teams SET name=? WHERE id=?", (new_name, team_id))
    for uid in add_ids:
        c.execute("UPDATE users SET team_id=? WHERE id=?", (team_id, uid))
    for uid in remove_ids:
        c.execute("UPDATE users SET team_id=NULL WHERE id=? AND team_id=?", (uid, team_id))
    conn.commit(); conn.close()

def get_team_members(team_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id,username FROM users WHERE team_id=?", (team_id,))
    members = c.fetchall(); conn.close()
    return members

def get_available_employees():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id,username FROM users WHERE role='user' AND (team_id IS NULL)")
    avail = c.fetchall(); conn.close()
    return avail