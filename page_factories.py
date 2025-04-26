import flet as ft
from dashboard import dashboard_view
from auth import login, signup, get_user
from ui_utils import validate_username, validate_password
from tasks import create_task, get_tasks, toggle_complete
from wellness import log_wellness, get_wellness
from feedback import submit_feedback, get_feedback
from training import list_resources, add_resource
from team import get_team_members, get_available_employees, create_team, edit_team
from rewards import get_balance, list_rewards, redeem_reward, add_reward

# Tasks & Goals Page with creation dialog
def tasks_page(page, user, **kwargs):
    lst = ft.ListView(expand=1, spacing=8)
    def load_tasks():
        lst.controls.clear()
        for t in get_tasks(user['id']):
            cb = ft.Checkbox(
                label=f"[{t['type']}] {t['title']} (Due: {t['due_date']})",
                value=bool(t['completed']),
                on_change=lambda e, id=t['id']: (toggle_complete(id, user['id']), load_tasks(), page.update())
            )
            lst.controls.append(cb)
    load_tasks()

    title_f = ft.TextField(label="Title", width=300)
    desc_f = ft.TextField(label="Description", multiline=True, width=300)
    date_p = ft.DatePicker(label="Due Date", width=300)
    type_dd = ft.Dropdown(label="Type", options=[ft.dropdown.Option("task"), ft.dropdown.Option("goal")])
    assignee_opts = ([ft.dropdown.Option(user['username'], key=user['id'])] if user['role']=='user'
        else [ft.dropdown.Option(u['username'], key=u['id']) for u in get_available_employees()]+[ft.dropdown.Option(user['username'], key=user['id'])])
    assignee_dd = ft.Dropdown(label="Assign To", width=300, options=assignee_opts)

    def submit_task(e):
        create_task(title_f.value, desc_f.value, assignee_dd.value, date_p.value.isoformat(), type_dd.value)
        title_f.value=desc_f.value=""; date_p.value=None; type_dd.value=None; assignee_dd.value=None
        page.dialog.open=False; load_tasks(); page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("New Task/Goal"),
        content=ft.Column([title_f, desc_f, date_p, type_dd, assignee_dd], tight=True),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: (setattr(page.dialog,'open',False), page.update())),
            ft.ElevatedButton("Create", on_click=submit_task)
        ]
    )
    page.dialog = dialog
    add_btn = ft.FloatingActionButton(icon=ft.icons.ADD, on_click=lambda e: (setattr(page.dialog,'open',True), page.update()))
    return ft.Stack([lst, add_btn], expand=1)

# Teams Page: Full Management Form
def teams_page(page, user, **kwargs):
    import sqlite3
    from database import get_conn
    if user['role']!='manager': return ft.Text("Only managers can manage teams.")
    team_id=user['team_id']
    if not team_id:
        name_f=ft.TextField(label="Team Name")
        avail=get_available_employees()
        checkboxes=[ft.Checkbox(label=u['username'],key=u['id']) for u in avail]
        def create(e):
            selected=[cb.key for cb in checkboxes if cb.value]
            if len(selected)>5:
                page.snack_bar=ft.SnackBar(ft.Text("Max 5 members."));page.snack_bar.open=True;page.update();return
            tid=create_team(name_f.value,user['id'],selected)
            page.snack_bar=ft.SnackBar(ft.Text(f"Team created (ID: {tid})"));page.snack_bar.open=True;page.update()
        return ft.Column([name_f,*checkboxes,ft.ElevatedButton("Create Team",on_click=create)],spacing=10)
    members=get_team_members(team_id)
    avail=get_available_employees()
    name_f=ft.TextField(label="Team Name")
    def rename(e):
        edit_team(team_id,new_name=name_f.value)
        page.snack_bar=ft.SnackBar(ft.Text("Team renamed."));page.snack_bar.open=True;page.update()
    remove_list=[ft.Row([ft.Text(m['username']),ft.IconButton(ft.icons.REMOVE_CIRCLE,on_click=lambda e,uid=m['id']:(edit_team(team_id,remove_ids=[uid]),page.update()))]) for m in members]
    add_list=[ft.Row([ft.Text(u['username']),ft.IconButton(ft.icons.ADD_CIRCLE,on_click=lambda e,uid=u['id']:(len(get_team_members(team_id))<5 and edit_team(team_id,add_ids=[uid]) or None,page.update()))]) for u in avail]
    def delete(e):
        for m in members: edit_team(team_id,remove_ids=[m['id']])
        conn=get_conn();c=conn.cursor();c.execute("DELETE FROM teams WHERE id=?",(team_id,));conn.commit();conn.close()
        page.snack_bar=ft.SnackBar(ft.Text("Team deleted."));page.snack_bar.open=True;page.update()
    return ft.Column([name_f,ft.ElevatedButton("Rename Team",on_click=rename),ft.Text("Members:"),*remove_list,ft.Text("Add Members:"),*add_list,ft.Divider(),ft.ElevatedButton("Delete Team",bgcolor=ft.colors.ERROR,on_click=delete)],spacing=8)

# Navigation & Main app
def home_view(page, token):
    user=get_user(token)
    role=user['role']
    page.views.clear()
    page.appbar=ft.AppBar(title=ft.Text(f"Welcome, {user['username']}"))
    content=ft.Container(expand=1)
    nav=ft.NavigationBar()
    PAGES=[
        ("Dashboard",ft.icons.DASHBOARD,dashboard_view),
        ("Tasks",ft.icons.TASK,tasks_page),
        ("Goals",ft.icons.FLAG,tasks_page),
        ("Wellness",ft.icons.HEALTH_AND_SAFETY,lambda p,u,**k: wellness_view(p,u)),
        ("Feedback",ft.icons.FEEDBACK,feedback_page),
        ("Training",ft.icons.SCHOOL,training_page),
        ("Teams",ft.icons.GROUP,teams_page),
        ("Rewards",ft.icons.CARD_GIFT_CARD,rewards_page)
    ]
    for idx,(label,icon,fn) in enumerate(PAGES):
        if label=="Teams" and role!='manager': continue
        nav.items.append(ft.NavigationBarItem(icon=icon,label=label,on_click=lambda e,f=fn: select(f)))
    def select(fn):
        content.content=fn(page, user)
        page.update()
    nav.selected_index=0
    select(PAGES[0][2])
    page.add(content, nav)
    page.update()


def main(page: ft.Page):
    page.title="Task & Wellness Management"
    page.vertical_alignment=ft.MainAxisAlignment.CENTER
    uname=ft.TextField(label="Username")
    pwd=ft.TextField(label="Password",password=True,can_reveal_password=True)
    role_dd=ft.Dropdown(label="Role",options=[ft.dropdown.Option("user"),ft.dropdown.Option("manager")])
    msg=ft.Text()
    def on_login(e):
        token=login(uname.value,pwd.value)
        if token: page.clean();home_view(page,token)
        else: msg.value="Invalid credentials";page.update()
    def on_signup(e):
        try:
            signup(uname.value,pwd.value,role_dd.value)
            msg.value="Signup successful! Please login.";page.update()
        except Exception as ex:
            msg.value=str(ex);page.update()
    page.add(uname,pwd,role_dd,ft.Row([ft.ElevatedButton("Login",on_click=on_login),ft.ElevatedButton("Signup",on_click=on_signup)]),msg)

if __name__=='__main__':
    ft.app(target=main,assets_dir="assets")