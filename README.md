Task & Performance Management System

A Python application built with Flet and backed by SQLite (via SQLAlchemy) to manage tasks, goals, wellness, training resources, rewards, feedback, and team performance. Passwords are securely encrypted at every layer using Fernet.

Table of Contents

Features

Architecture

Requirements

Installation

Usage

Demo Credentials

Project Structure

Contributing

License

Features

Encrypted Authentication: Password hashes encrypted with Fernet for an additional security layer.

Role-Based Access: Manager vs. Employee views, with managers able to view team metrics and assign tasks/goals.

Task & Goal Management: Create, assign, track, and complete tasks and goals, earning points on completion.

Wellness Tracking: Log and view personal stress & workload entries.

Training Resources: Manage and browse training materials.

Rewards System: Redeem points for rewards and track redemptions.

Feedback: Submit and view feedback entries.

Dashboard & Metrics: Summary cards and detailed tables for individual and team performance.

Architecture

Flet: UI framework for building the multi-page interface.

SQLite + SQLAlchemy ORM: Data persistence with models for Users, Tasks, Goals, WellnessEntries, TrainingResources, Rewards, Feedback, and RewardRedemptions.

Cryptography (Fernet): Generates/stores a symmetric key (key.key) for encrypting user password hashes.

Requirements

Python 3.8+

Dependencies listed in requirements.txt:

flet
sqlalchemy
cryptography

Installation

Clone the repository

git clone https://github.com/yourusername/your-repo.git
cd your-repo

Create a virtual environment (optional but recommended)

python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate     # Windows

Install dependencies

pip install -r requirements.txt

Usage

Generate or load the encryption key

On first run, the app will generate key.key automatically.

Run the application

python main.py

Interact via the UI

Log in with demo credentials (see below).

Navigate pages using the side rail to manage tasks, goals, wellness, resources, rewards, and feedback.

Demo Credentials

Role

Username

Password

Manager

john

managerpw

Employee

jane

employeepw

Project Structure

├── main.py            # App entrypoint and UI definitions
├── key.key            # Fernet key (auto-generated)
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── ...                # Other project files

Contributing

Contributions are welcome! Please:

Fork the repository

Create a branch (git checkout -b feature/YourFeature)

Commit your changes (git commit -m 'Add YourFeature')

Push to the branch (git push origin feature/YourFeature)

Open a Pull Request

License

This project is licensed under the MIT License. See LICENSE for details.
