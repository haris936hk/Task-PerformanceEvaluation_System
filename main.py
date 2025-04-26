# import flet as ft
# from auth import login, signup, get_user
# from ui_utils import validate_username, validate_password
# from dashboard import dashboard_view
# from tasks import create_task, get_tasks, toggle_complete
# from wellness import log_wellness, get_wellness
# from feedback import submit_feedback, get_feedback
# from training import list_resources, add_resource
# from team import get_team_members, get_available_employees, create_team, edit_team
# from rewards import earn_points, get_balance, list_rewards, redeem_reward, add_reward

# # Tasks & Goals Page with creation dialog

# def tasks_page(page, user):
#     # List view
#     lst = ft.ListView(expand=1, spacing=8)
#     def load_tasks():
#         lst.controls.clear()
#         for t in get_tasks(user['id']):
#             cb = ft.Checkbox(
#                 label=f"[{t['type']}] {t['title']} (Due: {t['due_date']})",
#                 value=bool(t['completed']),
#                 on_change=lambda e, id=t['id']: (toggle_complete(id, user['id']), load_tasks(), page.update())
#             )
#             lst.controls.append(cb)
#     load_tasks()

#     # Dialog fields
#     title_f = ft.TextField(label="Title", width=300)
#     desc_f = ft.TextField(label="Description", multiline=True, width=300)
#     date_p = ft.DatePicker(label="Due Date", width=300)
#     type_dd = ft.Dropdown(label="Type", options=[ft.dropdown.Option("task"), ft.dropdown.Option("goal")])
#     # Assign only self for users, or choose for managers
#     assignee_dd = ft.Dropdown(label="Assign To", width=300,
#         options=([ft.dropdown.Option(user['username'], key=user['id'])] if user['role']=='user'
#                  else [ft.dropdown.Option(u['username'], key=u['id']) for u in get_available_employees()]+
#                       [ft.dropdown.Option(user['username'], key=user['id'])]))

#     def submit_task(e):
#         aid = assignee_dd.value
#         create_task(title_f.value, desc_f.value, aid, date_p.value.isoformat(), type_dd.value)
#         title_f.value = desc_f.value = ""; date_p.value = None; type_dd.value = None; assignee_dd.value = None
#         page.dialog.open = False; load_tasks(); page.update()

#     dialog = ft.AlertDialog(
#         title=ft.Text("New Task/Goal"),
#         content=ft.Column([title_f, desc_f, date_p, type_dd, assignee_dd], tight=True),
#         actions=[
#             ft.TextButton("Cancel", on_click=lambda e: (setattr(page.dialog, 'open', False), page.update())),
#             ft.ElevatedButton("Create", on_click=submit_task)
#         ]
#     )
#     page.dialog = dialog

#     add_btn = ft.FloatingActionButton(icon=ft.icons.ADD, on_click=lambda e: (setattr(page.dialog, 'open', True), page.update()))

#     return ft.Stack([lst, add_btn], expand=1)

# # Teams Page: Full Management Form

# def teams_page(page, user, role):
#     if role != 'manager':
#         return ft.Text("Only managers can manage teams.")

#     team_id = user['team_id']
#     controls = []

#     # Create new team if none
#     if not team_id:
#         name_f = ft.TextField(label="Team Name")
#         avail = get_available_employees()
#         checkboxes = [ft.Checkbox(label=u['username'], key=u['id']) for u in avail]
#         def create(e):
#             selected = [cb.key for cb in checkboxes if cb.value]
#             if len(selected) > 5:
#                 page.snack_bar = ft.SnackBar(ft.Text("Max 5 members.")); page.snack_bar.open=True; page.update(); return
#             tid = create_team(name_f.value, user['id'], selected)
#             page.snack_bar = ft.SnackBar(ft.Text(f"Team created (ID: {tid})")); page.snack_bar.open=True; page.update()
#             # refresh
#             page.controls.clear(); home_view = None; page.update()
#         controls = [name_f] + checkboxes + [ft.ElevatedButton("Create Team", on_click=create)]
#         return ft.Column(controls, spacing=10)

#     # Edit existing team
#     members = get_team_members(team_id)
#     avail = get_available_employees()
#     name_f = ft.TextField(label="Team Name", value=next((t['name'] for t in [{ 'name': '' }] ,'')))  # load current name if stored

#     def rename(e):
#         edit_team(team_id, new_name=name_f.value)
#         page.snack_bar = ft.SnackBar(ft.Text("Team renamed.")); page.snack_bar.open=True; page.update()

#     remove_controls = [ft.Row([ft.Text(m['username']), ft.IconButton(ft.icons.REMOVE_CIRCLE, on_click=lambda e, uid=m['id']: (edit_team(team_id, remove_ids=[uid]), page.update()))]) for m in members]
#     add_controls = []
#     for u in avail:
#         btn = ft.IconButton(ft.icons.ADD_CIRCLE, on_click=lambda e, uid=u['id']: (len(get_team_members(team_id))<5 and edit_team(team_id, add_ids=[uid]) or page.snack_bar.open and None, page.update()))
#         add_controls.append(ft.Row([ft.Text(u['username']), btn]))

#     def delete(e):
#         # remove all members then delete
#         for m in members: edit_team(team_id, remove_ids=[m['id']])
#         # delete team record
#         import sqlite3
#         from database import get_conn
#         conn = get_conn(); c = conn.cursor(); c.execute("DELETE FROM teams WHERE id=?", (team_id,)); conn.commit(); conn.close()
#         page.snack_bar = ft.SnackBar(ft.Text("Team deleted.")); page.snack_bar.open=True; page.update()

#     controls = [
#         name_f, ft.ElevatedButton("Rename Team", on_click=rename),
#         ft.Text("Members:"), *remove_controls,
#         ft.Text("Add Members:"), *add_controls,
#         ft.Divider(), ft.ElevatedButton("Delete Team", bgcolor=ft.colors.ERROR, on_click=delete)
#     ]
#     return ft.Column(controls, spacing=8)