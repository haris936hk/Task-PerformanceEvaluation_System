import flet as ft
from flet import PieChart, LineChart
from tasks import get_tasks
from wellness import get_wellness

def dashboard_view(page, user, role):
    # Task metrics
    tasks = get_tasks(user['id'])
    total = len(tasks)
    completed = sum(1 for t in tasks if t['completed'])
    pending = total - completed

    # Wellness data
    wellness = get_wellness(user['id'])
    dates = [w['timestamp'][:10] for w in wellness]
    stress = [w['stress_level'] for w in wellness]

    # Pie chart for tasks
    pie = PieChart(
        expand=1,
        title="Tasks Completion",
        sections=[
            {"value": completed, "label": "Completed"},
            {"value": pending, "label": "Pending"}
        ]
    )
    # Line chart for wellness trend
    line = LineChart(
        expand=1,
        title="Stress Level Over Time",
        data=stress,
        labels=dates
    )

    # Layout animated cards + charts
    cards = []
    for label, value in [("Tasks", f"{completed}/{total}"), ("Pending", str(pending))]:
        cards.append(ft.Card(
            elevation=5,
            margin=10,
            content=ft.Container(
                content=ft.Text(f"{label}: {value}", size=18),
                padding=16,
                animate=ft.animation.Animation(300, "easeInOut")
            )
        ))

    return ft.Column([
        ft.Row(cards, alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([pie, line], height=300)
    ], spacing=20)