import flet as ft
import datetime
import os
import hashlib
import base64
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from cryptography.fernet import Fernet
import uuid

# Generate or load encryption key
KEY_FILE = "key.key"
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as key_file:
        key = key_file.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

cipher_suite = Fernet(key)

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///taskmanagement.db')
Session = sessionmaker(bind=engine)

# Data Models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100), nullable=False)
    is_manager = Column(Boolean, default=False)
    department = Column(String(50))
    points = Column(Integer, default=0)
    
    # Relationships
    tasks = relationship("Task", back_populates="assigned_user", foreign_keys="Task.assigned_user_id")
    goals = relationship("Goal", back_populates="assigned_user", foreign_keys="Goal.assigned_user_id")
    wellness_entries = relationship("WellnessEntry", back_populates="user")
    feedback_entries = relationship("Feedback", back_populates="user")
    
    def set_password(self, password):
        # Hash the password with salt
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        # Encrypt the hash for storage
        self.password_hash = cipher_suite.encrypt(password_hash.encode()).decode()
    
    def check_password(self, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        stored_hash = cipher_suite.decrypt(self.password_hash.encode()).decode()
        return password_hash == stored_hash


class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    created_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    completion_date = Column(DateTime)
    assigned_user_id = Column(Integer, ForeignKey('users.id'))
    assigned_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    assigned_user = relationship("User", back_populates="tasks", foreign_keys=[assigned_user_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


class Goal(Base):
    __tablename__ = 'goals'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    created_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    completion_date = Column(DateTime)
    feedback = Column(Text)
    assigned_user_id = Column(Integer, ForeignKey('users.id'))
    assigned_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    assigned_user = relationship("User", back_populates="goals", foreign_keys=[assigned_user_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


class WellnessEntry(Base):
    __tablename__ = 'wellness_entries'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    stress_level = Column(Integer)  # 1-10 scale
    workload = Column(String(20))  # Low, Medium, High
    notes = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    user = relationship("User", back_populates="wellness_entries")


class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    category = Column(String(50))  # System, Process, Team, etc.
    content = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    user = relationship("User", back_populates="feedback_entries")


class TrainingResource(Base):
    __tablename__ = 'training_resources'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    url = Column(String(200))
    category = Column(String(50))
    added_by_id = Column(Integer, ForeignKey('users.id'))
    date_added = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationships
    added_by = relationship("User")


class Reward(Base):
    __tablename__ = 'rewards'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    points_required = Column(Integer)
    available = Column(Boolean, default=True)
    added_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    added_by = relationship("User")


class RewardRedemption(Base):
    __tablename__ = 'reward_redemptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    reward_id = Column(Integer, ForeignKey('rewards.id'))
    redemption_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    points_spent = Column(Integer)
    
    # Relationships
    user = relationship("User")
    reward = relationship("Reward")


# Create all tables
Base.metadata.create_all(engine)


# App class for the Task & Performance Management System
class TaskManagementApp:
    def __init__(self):
        self.db_session = Session()
        self.current_user = None
        
        # Initialize demo data if database is empty
        self.initialize_demo_data()
    
    def initialize_demo_data(self):
        """Initialize demo data if database is empty"""
        if self.db_session.query(User).count() == 0:
            # Create demo manager
            manager = User(
                username="manager",
                full_name="John Manager",
                is_manager=True,
                department="Management"
            )
            manager.set_password("manager123")
            
            # Create demo employee
            employee = User(
                username="employee",
                full_name="Jane Employee",
                is_manager=False,
                department="Engineering"
            )
            employee.set_password("employee123")
            
            # Add users to session
            self.db_session.add(manager)
            self.db_session.add(employee)
            self.db_session.commit()
            
            # Add some demo tasks
            task1 = Task(
                title="Complete project proposal",
                description="Draft a proposal for the new client project",
                due_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3),
                assigned_user_id=2,  # Jane
                assigned_by_id=1  # John
            )
            
            task2 = Task(
                title="Review codebase",
                description="Review the latest code changes and provide feedback",
                due_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
                assigned_user_id=2,  # Jane
                assigned_by_id=1  # John
            )
            
            # Add tasks to session
            self.db_session.add(task1)
            self.db_session.add(task2)
            
            # Add a goal
            goal1 = Goal(
                title="Improve coding skills",
                description="Complete at least 2 online courses on Python advanced topics",
                due_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
                assigned_user_id=2,  # Jane
                assigned_by_id=1  # John
            )
            
            # Add goal to session
            self.db_session.add(goal1)
            
            # Add training resources
            training1 = TrainingResource(
                title="Python Advanced Techniques",
                description="A comprehensive course on advanced Python programming",
                url="https://example.com/python-advanced",
                category="Programming",
                added_by_id=1  # John
            )
            
            training2 = TrainingResource(
                title="Effective Time Management",
                description="Learn how to manage your time efficiently",
                url="https://example.com/time-management",
                category="Soft Skills",
                added_by_id=1  # John
            )
            
            # Add training resources to session
            self.db_session.add(training1)
            self.db_session.add(training2)
            
            # Add rewards
            reward1 = Reward(
                title="Extra Day Off",
                description="Get an extra day off work",
                points_required=100,
                added_by_id=1  # John
            )
            
            reward2 = Reward(
                title="Lunch Voucher",
                description="$25 lunch voucher for your favorite restaurant",
                points_required=50,
                added_by_id=1  # John
            )
            
            # Add rewards to session
            self.db_session.add(reward1)
            self.db_session.add(reward2)
            
            # Commit all changes
            self.db_session.commit()
    
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password"""
        user = self.db_session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            self.current_user = user
            return True
        return False
    
    def get_user_tasks(self, completed=None):
        """Get tasks for the current user, optionally filtered by completion status"""
        query = self.db_session.query(Task).filter_by(assigned_user_id=self.current_user.id)
        if completed is not None:
            query = query.filter_by(completed=completed)
        return query.all()
    
    def get_all_tasks(self):
        """Get all tasks (for managers)"""
        if not self.current_user.is_manager:
            return []
        return self.db_session.query(Task).all()
    
    def create_task(self, title, description, due_date, assigned_user_id=None):
        """Create a new task"""
        if assigned_user_id is None:
            assigned_user_id = self.current_user.id
        
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            assigned_user_id=assigned_user_id,
            assigned_by_id=self.current_user.id
        )
        self.db_session.add(task)
        self.db_session.commit()
        return task
    
    def complete_task(self, task_id):
        """Mark a task as completed"""
        task = self.db_session.query(Task).get(task_id)
        if task and task.assigned_user_id == self.current_user.id:
            task.completed = True
            task.completion_date = datetime.datetime.now(datetime.timezone.utc)
            
            # Award points for completing the task
            self.current_user.points += 10
            
            self.db_session.commit()
            return True
        return False
    
    def get_user_goals(self, completed=None):
        """Get goals for the current user, optionally filtered by completion status"""
        query = self.db_session.query(Goal).filter_by(assigned_user_id=self.current_user.id)
        if completed is not None:
            query = query.filter_by(completed=completed)
        return query.all()
    
    def get_all_goals(self):
        """Get all goals (for managers)"""
        if not self.current_user.is_manager:
            return []
        return self.db_session.query(Goal).all()
    
    def create_goal(self, title, description, due_date, assigned_user_id):
        """Create a new goal (manager only)"""
        if not self.current_user.is_manager:
            return None
        
        goal = Goal(
            title=title,
            description=description,
            due_date=due_date,
            assigned_user_id=assigned_user_id,
            assigned_by_id=self.current_user.id
        )
        self.db_session.add(goal)
        self.db_session.commit()
        return goal
    
    def complete_goal(self, goal_id):
        """Mark a goal as completed"""
        goal = self.db_session.query(Goal).get(goal_id)
        if goal and goal.assigned_user_id == self.current_user.id:
            goal.completed = True
            goal.completion_date = datetime.datetime.now(datetime.timezone.utc)
            
            # Award points for completing the goal
            self.current_user.points += 50
            
            self.db_session.commit()
            return True
        return False
    
    def add_goal_feedback(self, goal_id, feedback):
        """Add feedback to a goal (manager only)"""
        if not self.current_user.is_manager:
            return False
        
        goal = self.db_session.query(Goal).get(goal_id)
        if goal:
            goal.feedback = feedback
            self.db_session.commit()
            return True
        return False
    
    def create_wellness_entry(self, stress_level, workload, notes):
        """Create a new wellness entry"""
        entry = WellnessEntry(
            stress_level=stress_level,
            workload=workload,
            notes=notes,
            user_id=self.current_user.id
        )
        self.db_session.add(entry)
        self.db_session.commit()
        return entry
    
    def get_wellness_entries(self, limit=10):
        """Get wellness entries for the current user"""
        return self.db_session.query(WellnessEntry).filter_by(
            user_id=self.current_user.id
        ).order_by(WellnessEntry.date.desc()).limit(limit).all()
    
    def submit_feedback(self, category, content):
        """Submit feedback"""
        feedback = Feedback(
            category=category,
            content=content,
            user_id=self.current_user.id
        )
        self.db_session.add(feedback)
        self.db_session.commit()
        return feedback
    
    def get_all_feedback(self):
        """Get all feedback (manager only)"""
        if not self.current_user.is_manager:
            return []
        return self.db_session.query(Feedback).order_by(Feedback.date.desc()).all()
    
    def get_training_resources(self, category=None):
        """Get training resources, optionally filtered by category"""
        query = self.db_session.query(TrainingResource)
        if category:
            query = query.filter_by(category=category)
        return query.order_by(TrainingResource.title).all()
    
    def add_training_resource(self, title, description, url, category):
        """Add a new training resource (manager only)"""
        if not self.current_user.is_manager:
            return None
        
        resource = TrainingResource(
            title=title,
            description=description,
            url=url,
            category=category,
            added_by_id=self.current_user.id
        )
        self.db_session.add(resource)
        self.db_session.commit()
        return resource
    
    def get_rewards(self):
        """Get available rewards"""
        return self.db_session.query(Reward).filter_by(available=True).all()
    
    def add_reward(self, title, description, points_required):
        """Add a new reward (manager only)"""
        if not self.current_user.is_manager:
            return None
        
        reward = Reward(
            title=title,
            description=description,
            points_required=points_required,
            added_by_id=self.current_user.id
        )
        self.db_session.add(reward)
        self.db_session.commit()
        return reward
    
    def redeem_reward(self, reward_id):
        """Redeem a reward with points"""
        reward = self.db_session.query(Reward).get(reward_id)
        if not reward or not reward.available:
            return False
        
        if self.current_user.points < reward.points_required:
            return False
        
        redemption = RewardRedemption(
            user_id=self.current_user.id,
            reward_id=reward_id,
            points_spent=reward.points_required
        )
        self.current_user.points -= reward.points_required
        
        self.db_session.add(redemption)
        self.db_session.commit()
        return True
    
    def get_user_redemptions(self):
        """Get reward redemptions for the current user"""
        return self.db_session.query(RewardRedemption).filter_by(
            user_id=self.current_user.id
        ).order_by(RewardRedemption.redemption_date.desc()).all()
    
    def get_user_metrics(self):
        """Get performance metrics for the current user"""
        total_tasks = self.db_session.query(Task).filter_by(
            assigned_user_id=self.current_user.id
        ).count()
        
        completed_tasks = self.db_session.query(Task).filter_by(
            assigned_user_id=self.current_user.id,
            completed=True
        ).count()
        
        completion_rate = 0
        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
        
        total_goals = self.db_session.query(Goal).filter_by(
            assigned_user_id=self.current_user.id
        ).count()
        
        completed_goals = self.db_session.query(Goal).filter_by(
            assigned_user_id=self.current_user.id,
            completed=True
        ).count()
        
        goal_completion_rate = 0
        if total_goals > 0:
            goal_completion_rate = (completed_goals / total_goals) * 100
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "goal_completion_rate": goal_completion_rate,
            "points": self.current_user.points
        }
    
    def get_team_metrics(self):
        """Get team performance metrics (manager only)"""
        if not self.current_user.is_manager:
            return {}
        
        users = self.db_session.query(User).filter_by(is_manager=False).all()
        metrics = []
        
        for user in users:
            total_tasks = self.db_session.query(Task).filter_by(
                assigned_user_id=user.id
            ).count()
            
            completed_tasks = self.db_session.query(Task).filter_by(
                assigned_user_id=user.id,
                completed=True
            ).count()
            
            completion_rate = 0
            if total_tasks > 0:
                completion_rate = (completed_tasks / total_tasks) * 100
            
            metrics.append({
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "department": user.department,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": completion_rate,
                "points": user.points
            })
        
        return metrics
    
    def get_all_users(self):
        """Get all users (manager only)"""
        if not self.current_user.is_manager:
            return []
        return self.db_session.query(User).filter_by(is_manager=False).all()


# Flet UI Implementation
def main(page: ft.Page):
    # Initialize the app
    app = TaskManagementApp()
    
    # App title
    page.title = "Task & Performance Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    # Define theme colors
    primary_color = ft.Colors.BLUE_700
    accent_color = ft.Colors.AMBER_600
    
    # Create navigation drawer
    def navigation_drawer():
        rail = ft.NavigationRail(
            expand=True,
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="Dashboard"),
                ft.NavigationRailDestination(icon=ft.Icons.TASK_OUTLINED, selected_icon=ft.Icons.TASK, label="Tasks"),
                ft.NavigationRailDestination(icon=ft.Icons.FLAG_OUTLINED, selected_icon=ft.Icons.FLAG, label="Goals"),
                ft.NavigationRailDestination(icon=ft.Icons.HEALTH_AND_SAFETY_OUTLINED, selected_icon=ft.Icons.HEALTH_AND_SAFETY, label="Wellness"),
                ft.NavigationRailDestination(icon=ft.Icons.SCHOOL_OUTLINED, selected_icon=ft.Icons.SCHOOL, label="Training"),
                ft.NavigationRailDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, selected_icon=ft.Icons.EMOJI_EVENTS, label="Rewards"),
                ft.NavigationRailDestination(icon=ft.Icons.FEEDBACK_OUTLINED, selected_icon=ft.Icons.FEEDBACK, label="Feedback"),
            ],
            on_change=lambda e: change_page(e.control.selected_index),
        )
        
        # Manager-specific option
        if app.current_user and app.current_user.is_manager:
            rail.destinations.append(
                ft.NavigationRailDestination(icon=ft.Icons.PEOPLE_OUTLINED, selected_icon=ft.Icons.PEOPLE, label="Team")
            )
        
        return ft.Container(
            content=rail,
            width=200,
            expand=True,
        )

    # Page routing
    pages = ft.Stack(
        expand=True,
    )
    
    current_page_index = 0
    
    def change_page(index):
        nonlocal current_page_index
        current_page_index = index
        
        # Hide all pages
        for i in range(len(pages.controls)):
            pages.controls[i].visible = False
        
        # Show selected page
        if index < len(pages.controls):
            pages.controls[index].visible = True
            update_page_content(index)
        
        page.update()
    
    # Content area
    content_area = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            navigation_drawer(),
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
            pages,
        ],
    )
    
    # Login page
    username_field = ft.TextField(
        label="Username",
        autofocus=True,
        width=300,
    )
    
    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=300,
    )
    
    login_message = ft.Text(
        color=ft.Colors.RED_400,
        visible=False,
    )
    
    def login_click(e):
        if app.authenticate_user(username_field.value, password_field.value):
            # Authentication successful
            setup_app_ui()
            page.update()
        else:
            # Authentication failed
            login_message.value = "Invalid username or password"
            login_message.visible = True
            page.update()
    
    login_page = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(height=50),
            ft.Text("Task & Performance Management System", size=28, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Text("Login to your account", size=16),
            ft.Container(height=30),
            username_field,
            password_field,
            login_message,
            ft.Container(height=20),
            ft.ElevatedButton(
                text="Login",
                width=300,
                on_click=login_click,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=primary_color,
                ),
            ),
            ft.Container(height=10),
            ft.Text("Demo credentials:", size=14, italic=True),
            ft.Text("Username: manager, Password: manager123", size=12, italic=True),
            ft.Text("Username: employee, Password: employee123", size=12, italic=True),
        ]
    )
    
    page.add(login_page)
    
    # Setup app UI after successful login
    def setup_app_ui():
        # Clear existing controls (removes login page)
        page.controls.clear()
        
        # Set up the app bar
        page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.EVENT_NOTE),
            leading_width=40,
            title=ft.Text(f"Task Management - Welcome {app.current_user.full_name}"),
            center_title=False,
            bgcolor=primary_color,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    tooltip="Logout",
                    on_click=lambda _: logout(),
                ),
            ],
        )
        
        # Create pages (Stack) and mark them to expand
        dashboard_page = ft.Container(visible=True, expand=True)
        tasks_page = ft.Container(visible=False, expand=True)
        goals_page = ft.Container(visible=False, expand=True)
        wellness_page = ft.Container(visible=False, expand=True)
        training_page = ft.Container(visible=False, expand=True)
        rewards_page = ft.Container(visible=False, expand=True)
        feedback_page = ft.Container(visible=False, expand=True)
        
        pages.controls = [
            dashboard_page,
            tasks_page,
            goals_page,
            wellness_page,
            training_page,
            rewards_page,
            feedback_page,
        ]
        
        # Add team page for managers
        if app.current_user.is_manager:
            team_page = ft.Container(visible=False, expand=True)
            pages.controls.append(team_page)
        
        update_page_content(0)
        
        # Assemble the main layout using a Row to hold the navigation drawer and pages
        content_area = ft.Row(
            controls=[
                navigation_drawer(),
                ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                ft.Container(content=pages, expand=True),
            ],
            expand=True,
        )
        
        page.add(content_area)
        page.update()
    
    # Logout function
    def logout():
        app.current_user = None
        page.appbar = None
        page.controls.clear()
        
        # Reset form fields
        username_field.value = ""
        password_field.value = ""
        login_message.visible = False
        
        # Show login page
        page.add(login_page)
        page.update()
    
    # Update page content based on selected index
    def update_page_content(index):
        if index == 0:  # Dashboard
            render_dashboard_page()
        elif index == 1:  # Tasks
            render_tasks_page()
        elif index == 2:  # Goals
            render_goals_page()
        elif index == 3:  # Wellness
            render_wellness_page()
        elif index == 4:  # Training
            render_training_page()
        elif index == 5:  # Rewards
            render_rewards_page()
        elif index == 6:  # Feedback
            render_feedback_page()
        elif index == 7 and app.current_user.is_manager:  # Team (manager only)
            render_team_page()
    
    # Dashboard page
    def render_dashboard_page():
        metrics = app.get_user_metrics()
        dashboard_page = pages.controls[0]
        
        # Clear existing content
        dashboard_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
                
                # User summary section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        controls=[
                            ft.Text("Your Summary", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                controls=[
                                    ft.Card(
                                        content=ft.Container(
                                            width=180,
                                            height=100,
                                            padding=15,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Text("Total Tasks", size=14),
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.TASK, size=30, color=primary_color),
                                                            ft.Text(str(metrics["total_tasks"]), size=30, weight=ft.FontWeight.BOLD),
                                                        ],
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                    ft.Card(
                                        content=ft.Container(
                                            width=180,
                                            height=100,
                                            padding=15,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Text("Completed Tasks", size=14),
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.TASK_ALT, size=30, color=ft.Colors.GREEN),
                                                            ft.Text(str(metrics["completed_tasks"]), size=30, weight=ft.FontWeight.BOLD),
                                                        ],
                                                        alignment=ft.MainAxisAlignment.CENTER,),
                                                ]
                                            )
                                        )
                                    ),
                                    ft.Card(
                                        content=ft.Container(
                                            width=180,
                                            height=100,
                                            padding=15,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Text("Completion Rate", size=14),
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.PERCENT, size=30, color=accent_color),
                                                            ft.Text(f"{metrics['completion_rate']:.1f}%", size=30, weight=ft.FontWeight.BOLD),
                                                        ],
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                    ft.Card(
                                        content=ft.Container(
                                            width=180,
                                            height=100,
                                            padding=15,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Text("Points Balance", size=14),
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.STARS, size=30, color=accent_color),
                                                            ft.Text(str(metrics["points"]), size=30, weight=ft.FontWeight.BOLD),
                                                        ],
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                ],
                                wrap=True,
                                spacing=10,
                            ),
                        ]
                    ),
                ),
                
                # Goals section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        controls=[
                            ft.Text("Your Goals", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                controls=[
                                    ft.Card(
                                        content=ft.Container(
                                            width=180,
                                            height=100,
                                            padding=15,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Text("Total Goals", size=14),
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.FLAG, size=30, color=primary_color),
                                                            ft.Text(str(metrics["total_goals"]), size=30, weight=ft.FontWeight.BOLD),
                                                        ],
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                    ft.Card(
                                        content=ft.Container(
                                            width=180,
                                            height=100,
                                            padding=15,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Text("Completed Goals", size=14),
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.EMOJI_FLAGS, size=30, color=ft.Colors.GREEN),
                                                            ft.Text(str(metrics["completed_goals"]), size=30, weight=ft.FontWeight.BOLD),
                                                        ],
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                    ft.Card(
                                        content=ft.Container(
                                            width=180,
                                            height=100,
                                            padding=15,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Text("Goal Completion", size=14),
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.PERCENT, size=30, color=accent_color),
                                                            ft.Text(f"{metrics['goal_completion_rate']:.1f}%", size=30, weight=ft.FontWeight.BOLD),
                                                        ],
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                ],
                                wrap=True,
                                spacing=10,
                            ),
                        ]
                    ),
                ),
                
                # Team metrics (for managers)
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    visible=app.current_user.is_manager,
                    content=ft.Column(
                        controls=[
                            ft.Text("Team Overview", size=18, weight=ft.FontWeight.BOLD),
                            ft.DataTable(
                                columns=[
                                    ft.DataColumn(ft.Text("Name")),
                                    ft.DataColumn(ft.Text("Department")),
                                    ft.DataColumn(ft.Text("Tasks"), numeric=True),
                                    ft.DataColumn(ft.Text("Completed"), numeric=True),
                                    ft.DataColumn(ft.Text("Rate"), numeric=True),
                                    ft.DataColumn(ft.Text("Points"), numeric=True),
                                ],
                                rows=get_team_data_rows(),
                            ),
                        ]
                    ),
                ),
                
                # Recent tasks section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        controls=[
                            ft.Text("Recent Tasks", size=18, weight=ft.FontWeight.BOLD),
                            get_recent_tasks_list(),
                        ]
                    ),
                ),
            ]
        )
        page.update()
    
    def get_team_data_rows():
        """Generate DataTable rows for team metrics"""
        if not app.current_user.is_manager:
            return []
        
        team_metrics = app.get_team_metrics()
        rows = []
        
        for member in team_metrics:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(member["full_name"])),
                        ft.DataCell(ft.Text(member["department"])),
                        ft.DataCell(ft.Text(str(member["total_tasks"]))),
                        ft.DataCell(ft.Text(str(member["completed_tasks"]))),
                        ft.DataCell(ft.Text(f"{member['completion_rate']:.1f}%")),
                        ft.DataCell(ft.Text(str(member["points"]))),
                    ]
                )
            )
        
        return rows
    
    def get_recent_tasks_list():
        """Generate list of recent tasks"""
        tasks = app.get_user_tasks()
        if not tasks:
            return ft.Text("No tasks found.")
        
        tasks_list = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=False,
            height=300,
        )
        
        for task in tasks[:5]:  # Show up to 5 recent tasks
            due_date = task.due_date.strftime("%Y-%m-%d") if task.due_date else "No due date"
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN) if task.completed else ft.Icon(ft.Icons.PENDING, color=ft.Colors.ORANGE)
            
            tasks_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Row(
                            controls=[
                                status_icon,
                                ft.Column(
                                    expand=True,
                                    spacing=5,
                                    controls=[
                                        ft.Text(task.title, weight=ft.FontWeight.BOLD),
                                        ft.Text(task.description[:50] + "..." if len(task.description) > 50 else task.description, size=12),
                                        ft.Text(f"Due: {due_date}", size=12, color=ft.Colors.GREY_700),
                                    ],
                                ),
                            ],
                        ),
                    ),
                )
            )
        
        return tasks_list
    
    # Tasks page
    def render_tasks_page():
        tasks_page = pages.controls[1]
        
        tasks_view = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=False,
            expand=True,
        )
        
        # Function to refresh tasks
        def refresh_tasks():
            tasks = app.get_user_tasks()
            tasks_view.controls.clear()
            
            for task in tasks:
                due_date = task.due_date.strftime("%Y-%m-%d") if task.due_date else "No due date"
                status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN) if task.completed else ft.Icon(ft.Icons.PENDING, color=ft.Colors.ORANGE)
                
                # Create task card
                task_card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    controls=[
                                        status_icon,
                                        ft.Text(task.title, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Text(f"Due: {due_date}", size=12, color=ft.Colors.GREY_700),
                                    ],
                                ),
                                ft.Text(task.description, size=14),
                                ft.Row(
                                    controls=[
                                        ft.ElevatedButton(
                                            "Mark Complete",
                                            icon=ft.Icons.DONE,
                                            on_click=lambda e, task_id=task.id: complete_task(task_id),
                                            disabled=task.completed,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.END,
                                ),
                            ],
                        ),
                    ),
                )
                
                tasks_view.controls.append(task_card)
            
            page.update()
        
        # Function to complete a task
        def complete_task(task_id):
            if app.complete_task(task_id):
                refresh_tasks()
                # Show snackbar confirmation
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Task completed successfully!"),
                    action="OK",
                )
                page.snack_bar.open = True
                page.update()
        
        # Task creation form
        task_title = ft.TextField(
            label="Task Title",
            width=300,
        )
        
        task_description = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=300,
        )
        
        task_due_date = ft.TextField(
            label="Due Date (YYYY-MM-DD)",
            width=300,
        )
        
        def clear_task_form():
            task_title.value = ""
            task_description.value = ""
            task_due_date.value = ""
            page.update()
        
        def add_task_click(e):
            # Validate inputs
            if not task_title.value:
                task_title.error_text = "Title is required"
                page.update()
                return
            
            due_date = None
            if task_due_date.value:
                try:
                    due_date = datetime.datetime.strptime(task_due_date.value, "%Y-%m-%d")
                except ValueError:
                    task_due_date.error_text = "Invalid date format"
                    page.update()
                    return
            
            # Create task
            app.create_task(
                title=task_title.value,
                description=task_description.value,
                due_date=due_date,
            )
            
            # Clear form and refresh tasks
            clear_task_form()
            refresh_tasks()
            
            # Show snackbar confirmation
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Task created successfully!"),
                action="OK",
            )
            page.snack_bar.open = True
            page.update()
        
        # Manager section for assigning tasks
        user_dropdown = ft.Dropdown(
            label="Assign to User",
            width=300,
        )
        
        def load_users():
            if app.current_user.is_manager:
                users = app.get_all_users()
                user_dropdown.options = [
                    ft.dropdown.Option(key=str(user.id), text=user.full_name)
                    for user in users
                ]
                page.update()
        
        def assign_task_click(e):
            # Validate inputs
            if not task_title.value:
                task_title.error_text = "Title is required"
                page.update()
                return
            
            if not user_dropdown.value:
                user_dropdown.error_text = "Please select a user"
                page.update()
                return
            
            due_date = None
            if task_due_date.value:
                try:
                    due_date = datetime.datetime.strptime(task_due_date.value, "%Y-%m-%d")
                except ValueError:
                    task_due_date.error_text = "Invalid date format"
                    page.update()
                    return
            
            # Create task
            app.create_task(
                title=task_title.value,
                description=task_description.value,
                due_date=due_date,
                assigned_user_id=int(user_dropdown.value),
            )
            
            # Clear form and refresh tasks
            clear_task_form()
            
            # Show snackbar confirmation
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Task assigned successfully!"),
                action="OK",
            )
            page.snack_bar.open = True
            page.update()
        
        # Add task form
        add_task_form = ft.Column(
            spacing=10,
            controls=[
                ft.Text("Create New Task", size=18, weight=ft.FontWeight.BOLD),
                task_title,
                task_description,
                task_due_date,
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Add Task",
                            icon=ft.Icons.ADD,
                            on_click=add_task_click,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=primary_color,
                            ),
                        ),
                        ft.OutlinedButton("Clear", on_click=lambda _: clear_task_form()),
                    ],
                ),
            ],
        )
        
        # Manager section for assigning tasks
        manager_section = ft.Column(
            visible=app.current_user.is_manager,
            spacing=10,
            controls=[
                ft.Divider(),
                ft.Text("Assign Task to Team Member", size=18, weight=ft.FontWeight.BOLD),
                user_dropdown,
                ft.ElevatedButton(
                    "Assign Task",
                    icon=ft.Icons.ASSIGNMENT_IND,
                    on_click=assign_task_click,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=primary_color,
                    ),
                ),
            ],
        )
        
        # Load users for dropdown if manager
        if app.current_user.is_manager:
            load_users()
        
        # Assemble page layout
        tasks_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Tasks Management", size=24, weight=ft.FontWeight.BOLD),
                
                # Tasks form section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        controls=[
                            add_task_form,
                            manager_section,
                        ]
                    ),
                ),
                
                # Tasks list section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Your Tasks", size=18, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        tooltip="Refresh",
                                        on_click=lambda _: refresh_tasks(),
                                    ),
                                ],
                            ),
                            tasks_view,
                        ]
                    ),
                ),
            ]
        )
        
        # Initial load of tasks
        refresh_tasks()
    
    # Goals page
    def render_goals_page():
        goals_page = pages.controls[2]
        
        goals_view = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=False,
            expand=True,
        )
        
        # Function to refresh goals
        def refresh_goals():
            goals = app.get_user_goals()
            goals_view.controls.clear()
            
            for goal in goals:
                due_date = goal.due_date.strftime("%Y-%m-%d") if goal.due_date else "No due date"
                status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN) if goal.completed else ft.Icon(ft.Icons.PENDING, color=ft.Colors.ORANGE)
                
                # Create goal card
                goal_card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    controls=[
                                        status_icon,
                                        ft.Text(goal.title, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Text(f"Due: {due_date}", size=12, color=ft.Colors.GREY_700),
                                    ],
                                ),
                                ft.Text(goal.description, size=14),
                                # Show feedback if available
                                ft.Container(
                                    visible=bool(goal.feedback),
                                    padding=10,
                                    bgcolor=ft.Colors.BLUE_100,
                                    border_radius=5,
                                    content=ft.Column(
                                        controls=[
                                            ft.Text("Manager Feedback:", weight=ft.FontWeight.BOLD, size=12),
                                            ft.Text(goal.feedback if goal.feedback else "", size=14),
                                        ],
                                    ),
                                ),
                                ft.Row(
                                    controls=[
                                        ft.ElevatedButton(
                                            "Mark Complete",
                                            icon=ft.Icons.DONE,
                                            on_click=lambda e, goal_id=goal.id: complete_goal(goal_id),
                                            disabled=goal.completed,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.END,
                                ),
                            ],
                        ),
                    ),
                )
                
                goals_view.controls.append(goal_card)
            
            page.update()
        
        # Function to complete a goal
        def complete_goal(goal_id):
            if app.complete_goal(goal_id):
                refresh_goals()
                # Show snackbar confirmation
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Goal completed successfully! You earned 50 points!"),
                    action="OK",
                )
                page.snack_bar.open = True
                page.update()
        
        # Manager section for goals
        manager_section = ft.Column(
            visible=app.current_user.is_manager,
            spacing=10,
            controls=[
                ft.Text("Set Goals for Team Members", size=18, weight=ft.FontWeight.BOLD),
            ],
        )
        
        # Goal creation form for managers
        goal_title = ft.TextField(
            label="Goal Title",
            width=300,
        )
        
        goal_description = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=300,
        )
        
        goal_due_date = ft.TextField(
            label="Due Date (YYYY-MM-DD)",
            width=300,
        )
        
        goal_user_dropdown = ft.Dropdown(
            label="Assign to User",
            width=300,
        )
        
        def load_users_for_goals():
            if app.current_user.is_manager:
                users = app.get_all_users()
                goal_user_dropdown.options = [
                    ft.dropdown.Option(key=str(user.id), text=user.full_name)
                    for user in users
                ]
                page.update()
        
        def clear_goal_form():
            goal_title.value = ""
            goal_description.value = ""
            goal_due_date.value = ""
            if app.current_user.is_manager:
                goal_user_dropdown.value = None
            page.update()
        
        def create_goal_click(e):
            # Validate inputs
            if not goal_title.value:
                goal_title.error_text = "Title is required"
                page.update()
                return
            
            if not goal_user_dropdown.value:
                goal_user_dropdown.error_text = "Please select a user"
                page.update()
                return
            
            due_date = None
            if goal_due_date.value:
                try:
                    due_date = datetime.datetime.strptime(goal_due_date.value, "%Y-%m-%d")
                except ValueError:
                    goal_due_date.error_text = "Invalid date format"
                    page.update()
                    return
            
            # Create goal
            app.create_goal(
                title=goal_title.value,
                description=goal_description.value,
                due_date=due_date,
                assigned_user_id=int(goal_user_dropdown.value),
            )
            
            # Clear form
            clear_goal_form()
            
            # Show snackbar confirmation
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Goal created successfully!"),
                action="OK",
            )
            page.snack_bar.open = True
            page.update()
        
        # Add manager form controls
        if app.current_user.is_manager:
            manager_section.controls.extend([
                goal_title,
                goal_description,
                goal_due_date,
                goal_user_dropdown,
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Create Goal",
                            icon=ft.Icons.ADD,
                            on_click=create_goal_click,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=primary_color,
                            ),
                        ),
                        ft.OutlinedButton("Clear", on_click=lambda _: clear_goal_form()),
                    ],
                ),
            ])
            
            # Load users for dropdown
            load_users_for_goals()
        
        # Assemble page layout
        goals_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Goals Management", size=24, weight=ft.FontWeight.BOLD),
                
                # Manager goals form section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    visible=app.current_user.is_manager,
                    content=manager_section,
                ),

                # Goals list section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Your Goals", size=18, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        tooltip="Refresh",
                                        on_click=lambda _: refresh_goals(),
                                    ),
                                ],
                            ),
                            goals_view,
                        ]
                    ),
                ),
            ]
        )
        
        # Initial load of goals
        refresh_goals()
    
    # Wellness page
    def render_wellness_page():
        wellness_page = pages.controls[3]
        
        wellness_entries_view = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=False,
            height=300,
        )
        
        # Function to refresh wellness entries
        def refresh_wellness_entries():
            entries = app.get_wellness_entries()
            wellness_entries_view.controls.clear()
            
            for entry in entries:
                # Determine stress level color
                stress_color = ft.Colors.GREEN
                if entry.stress_level > 3 and entry.stress_level <= 7:
                    stress_color = ft.Colors.ORANGE
                elif entry.stress_level > 7:
                    stress_color = ft.Colors.RED
                
                entry_card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            entry.date.strftime("%Y-%m-%d %H:%M"),
                                            size=12,
                                            color=ft.Colors.GREY_700,
                                        ),
                                        ft.Container(expand=True),
                                        ft.Container(
                                            padding=5,
                                            border_radius=5,
                                            bgcolor=stress_color,
                                            content=ft.Text(
                                                f"Stress: {entry.stress_level}/10",
                                                color=ft.Colors.WHITE,
                                                weight=ft.FontWeight.BOLD,
                                                size=12,
                                            ),
                                        ),
                                        ft.Container(
                                            padding=5,
                                            border_radius=5,
                                            bgcolor=ft.Colors.BLUE,
                                            content=ft.Text(
                                                f"Workload: {entry.workload}",
                                                color=ft.Colors.WHITE,
                                                weight=ft.FontWeight.BOLD,
                                                size=12,
                                            ),
                                        ),
                                    ],
                                ),
                                ft.Text(entry.notes),
                            ],
                        ),
                    ),
                )
                
                wellness_entries_view.controls.append(entry_card)
            
            page.update()
        
        # Wellness entry form
        stress_slider = ft.Slider(
            min=1,
            max=10,
            divisions=9,
            label="{value}",
            value=5,
            width=300,
        )
        
        workload_dropdown = ft.Dropdown(
            label="Workload",
            width=300,
            options=[
                ft.dropdown.Option("Low"),
                ft.dropdown.Option("Medium"),
                ft.dropdown.Option("High"),
            ],
            value="Medium",
        )
        
        wellness_notes = ft.TextField(
            label="Notes",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=300,
        )
        
        def clear_wellness_form():
            stress_slider.value = 5
            workload_dropdown.value = "Medium"
            wellness_notes.value = ""
            page.update()
        
        def add_wellness_entry_click(e):
            # Create wellness entry
            app.create_wellness_entry(
                stress_level=int(stress_slider.value),
                workload=workload_dropdown.value,
                notes=wellness_notes.value,
            )
            
            # Clear form and refresh entries
            clear_wellness_form()
            refresh_wellness_entries()
            
            # Show snackbar confirmation
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Wellness entry recorded successfully!"),
                action="OK",
            )
            page.snack_bar.open = True
            page.update()
        
        # Assemble page layout
        wellness_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Wellness Tracking", size=24, weight=ft.FontWeight.BOLD),
                
                # Wellness form section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Log Your Wellness", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text("Stress Level (1-10):"),
                            stress_slider,
                            workload_dropdown,
                            wellness_notes,
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Submit Entry",
                                        icon=ft.Icons.ADD,
                                        on_click=add_wellness_entry_click,
                                        style=ft.ButtonStyle(
                                            color=ft.Colors.WHITE,
                                            bgcolor=primary_color,
                                        ),
                                    ),
                                    ft.OutlinedButton("Clear", on_click=lambda _: clear_wellness_form()),
                                ],
                            ),
                        ]
                    ),
                ),
                
                # Wellness history section
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Your Wellness History", size=18, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        tooltip="Refresh",
                                        on_click=lambda _: refresh_wellness_entries(),
                                    ),
                                ],
                            ),
                            wellness_entries_view,
                        ]
                    ),
                ),
            ]
        )
        
        # Initial load of wellness entries
        refresh_wellness_entries()
    
        # Training page
    def render_training_page():
        training_page = pages.controls[4]
        
        training_view = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=False,
            expand=True,
        )
        
        # Function to refresh training resources
        def refresh_training():
            resources = app.get_training_resources()
            training_view.controls.clear()
            
            for resource in resources:
                resource_card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.SCHOOL, color=primary_color),
                                        ft.Text(resource.title, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Container(
                                            padding=5,
                                            border_radius=5,
                                            bgcolor=ft.Colors.BLUE_100,
                                            content=ft.Text(resource.category, size=12),
                                        ),
                                    ],
                                ),
                                ft.Text(resource.description, size=14),
                                ft.Row(
                                    controls=[
                                        ft.Text("Resource Link:", size=12),
                                        ft.TextButton(
                                            text="Open Link",
                                            icon=ft.Icons.LINK,
                                            on_click=lambda e, url=resource.url: page.launch_url(url),
                                        ),
                                    ],
                                    spacing=10,
                                ),
                            ],
                        ),
                    ),
                )
                training_view.controls.append(resource_card)
            
            page.update()
        
        # Training resource creation form (for managers)
        training_title = ft.TextField(
            label="Title",
            width=300,
        )
        
        training_description = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=300,
        )
        
        training_url = ft.TextField(
            label="URL",
            width=300,
        )
        
        training_category = ft.Dropdown(
            label="Category",
            width=300,
            options=[
                ft.dropdown.Option("Programming"),
                ft.dropdown.Option("Soft Skills"),
                ft.dropdown.Option("Leadership"),
                ft.dropdown.Option("Technical"),
            ],
        )
        
        def clear_training_form():
            training_title.value = ""
            training_description.value = ""
            training_url.value = ""
            training_category.value = ""
            page.update()
        
        def add_training_click(e):
            if not training_title.value:
                training_title.error_text = "Title is required"
                page.update()
                return
            
            if not training_url.value:
                training_url.error_text = "URL is required"
                page.update()
                return
            
            app.add_training_resource(
                title=training_title.value,
                description=training_description.value,
                url=training_url.value,
                category=training_category.value,
            )
            
            clear_training_form()
            refresh_training()
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Training resource added successfully!"),
                action="OK",
            )
            page.snack_bar.open = True
            page.update()
        
        # Assemble page layout
        training_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Training Resources", size=24, weight=ft.FontWeight.BOLD),
                
                # Manager section for adding resources
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    visible=app.current_user.is_manager,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Add New Training Resource", size=18, weight=ft.FontWeight.BOLD),
                            training_title,
                            training_description,
                            training_url,
                            training_category,
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Add Resource",
                                        icon=ft.Icons.ADD,
                                        on_click=add_training_click,
                                        style=ft.ButtonStyle(
                                            color=ft.Colors.WHITE,
                                            bgcolor=primary_color,
                                        ),
                                    ),
                                    ft.OutlinedButton("Clear", on_click=lambda _: clear_training_form()),
                                ],
                            ),
                        ]
                    ),
                ),
                
                # Training resources list
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Available Resources", size=18, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        tooltip="Refresh",
                                        on_click=lambda _: refresh_training(),
                                    ),
                                ],
                            ),
                            training_view,
                        ]
                    ),
                ),
            ]
        )
        
        # Initial load of resources
        refresh_training()

        # Rewards page
    def render_rewards_page():
        rewards_page = pages.controls[5]

        rewards_view = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=False,
            expand=True,
        )

        def refresh_rewards():
            rewards = app.get_rewards()
            rewards_view.controls.clear()
            for reward in rewards:
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(reward.title, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Text(f"{reward.points_required} pts", size=12),
                                    ],
                                ),
                                ft.Text(reward.description, size=14),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                    controls=[
                                        ft.ElevatedButton(
                                            text="Redeem",
                                            icon=ft.Icons.REDEEM,
                                            on_click=lambda e, rid=reward.id: redeem_reward(rid),
                                            disabled=app.current_user.points < reward.points_required,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                )
                rewards_view.controls.append(card)
            page.update()

        def redeem_reward(reward_id):
            if app.redeem_reward(reward_id):
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Reward redeemed successfully!"),
                    action="OK",
                )
                page.snack_bar.open = True
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Unable to redeem reward."),
                    action="OK",
                )
                page.snack_bar.open = True
            refresh_rewards()
            page.update()

        # Assemble page
        rewards_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Rewards Catalog", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Your Points: {app.current_user.points}", size=18),
                        ],
                    ),
                ),
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    expand=True,
                    content=rewards_view,
                ),
            ],
        )
        refresh_rewards()

    # Feedback page
    def render_feedback_page():
        feedback_page = pages.controls[6]

        # Feedback form
        category_dropdown = ft.Dropdown(
            label="Category",
            width=300,
            options=[
                ft.dropdown.Option("System"),
                ft.dropdown.Option("Process"),
                ft.dropdown.Option("Team"),
                ft.dropdown.Option("Other"),
            ],
            value="System",
        )
        feedback_content = ft.TextField(
            label="Your Feedback",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=400,
        )

        feedback_list = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=False,
            expand=True,
        )

        def refresh_feedback():
            feedback_list.controls.clear()
            entries = app.get_all_feedback() if app.current_user.is_manager else app.db_session.query(app.Feedback).filter_by(user_id=app.current_user.id).all()
            for entry in entries:
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(entry.category, weight=ft.FontWeight.BOLD),
                                        ft.Container(expand=True),
                                        ft.Text(entry.date.strftime("%Y-%m-%d %H:%M"), size=12, color=ft.Colors.GREY_600),
                                    ],
                                ),
                                ft.Text(entry.content, size=14),
                            ],
                        ),
                    ),
                )
                feedback_list.controls.append(card)
            page.update()

        def submit_feedback_click(e):
            if not feedback_content.value:
                feedback_content.error_text = "Please enter feedback"
                page.update()
                return
            app.submit_feedback(category_dropdown.value, feedback_content.value)
            feedback_content.value = ""
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Feedback submitted!"),
                action="OK",
            )
            page.snack_bar.open = True
            refresh_feedback()
            page.update()

        # Assemble page
        feedback_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Submit Feedback", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            category_dropdown,
                            feedback_content,
                            ft.ElevatedButton(
                                text="Submit",
                                icon=ft.Icons.SEND,
                                on_click=submit_feedback_click,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    expand=True,
                    content=ft.Column(
                        controls=[
                            ft.Text("Feedback History", size=18, weight=ft.FontWeight.BOLD),
                            feedback_list,
                        ],
                    ),
                ),
            ],
        )
        refresh_feedback()

    # Team page (managers only)
    def render_team_page():
        team_page = pages.controls[7]
        team_metrics = app.get_team_metrics()

        rows = []
        for m in team_metrics:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(m["full_name"])),
                        ft.DataCell(ft.Text(m["department"])),
                        ft.DataCell(ft.Text(str(m["total_tasks"]))),
                        ft.DataCell(ft.Text(str(m["completed_tasks"]))),
                        ft.DataCell(ft.Text(f"{m['completion_rate']:.1f}%")),
                        ft.DataCell(ft.Text(str(m["points"]))),
                    ]
                )
            )

        team_page.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Team Performance", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Name")),
                            ft.DataColumn(ft.Text("Department")),
                            ft.DataColumn(ft.Text("Tasks"), numeric=True),
                            ft.DataColumn(ft.Text("Completed"), numeric=True),
                            ft.DataColumn(ft.Text("Rate"), numeric=True),
                            ft.DataColumn(ft.Text("Points"), numeric=True),
                        ],
                        rows=rows,
                    ),
                ),
            ],
        )

    # End of page rendering functions

if __name__ == "__main__":
    ft.app(target=main)