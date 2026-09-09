import os
from datetime import datetime, date

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))


def seed_demo_data():
    from .models import (ActivityLog, DailyLog, DocumentRecord, LearningDiary,
                         Notification, Performance, SkillAmbassador,
                         Task, User, WeeklySummary)

    if User.query.count() > 0:
        return

    admin = User(
        full_name="Admin User",
        email="admin@dodl.edu",
        password_hash=bcrypt.generate_password_hash("Admin@123").decode("utf-8"),
        internship_id="ADM-001",
        department="Administration",
        role="admin",
        is_active=True,
        bio="Institutional administrator managing the full internship system.",
        skills="Operations, Reporting, Governance",
    )
    db.session.add(admin)
    db.session.flush()

    supervisor = User(
        full_name="Sarah Johnson",
        email="supervisor@dodl.edu",
        password_hash=bcrypt.generate_password_hash("Supervisor@123").decode("utf-8"),
        internship_id="SUP-001",
        department="Software Engineering",
        role="supervisor",
        is_active=True,
        bio="Supervises internship operations and reviews work progress.",
        skills="Mentoring, Code Review, Team Leadership",
    )
    db.session.add(supervisor)
    db.session.flush()

    intern = User(
        full_name="Aisha Rahman",
        email="intern@dodl.edu",
        password_hash=bcrypt.generate_password_hash("Intern@123").decode("utf-8"),
        internship_id="INT-101",
        department="Information Systems",
        role="intern",
        supervisor_id=supervisor.id,
        is_active=True,
        internship_start=date(2026, 8, 1),
        internship_end=date(2026, 12, 31),
        bio="Passionate software engineering intern focused on building practical digital solutions.",
        skills="Python, Flask, SQL, UI Design",
    )
    db.session.add(intern)
    db.session.flush()

    task1 = Task(
        task_name="Build internship dashboard wireframe",
        description="Create a dashboard layout and discuss it with the supervisor.",
        domain="Frontend",
        assigned_date=date.today(),
        deadline=date.today(),
        week=1,
        priority="High",
        status="Completed",
        progress_percentage=100,
        assigned_by="Sarah Johnson",
        comments="Excellent progress and ready for review.",
        user_id=intern.id,
    )
    task2 = Task(
        task_name="Prepare weekly summary",
        description="Summarize tasks completed and challenges faced this week.",
        domain="Documentation",
        assigned_date=date.today(),
        deadline=date.today(),
        week=2,
        priority="Medium",
        status="In Progress",
        progress_percentage=60,
        assigned_by="Sarah Johnson",
        comments="Needs more evidence and technical learning detail.",
        user_id=intern.id,
    )
    db.session.add_all([task1, task2])

    db.session.add_all([
        DailyLog(
            user_id=intern.id,
            date=date.today(),
            day="Monday",
            task_description="Built frontend mockups and reviewed internship dashboard ideas.",
            working_start_time="09:00",
            working_end_time="17:00",
            working_status="Present",
            daily_working_hours=8.0,
            tomorrow_action="Finalize dashboard component structure.",
            target="Complete dashboard structure",
            daily_report_plan="Reviewed requirements and built the initial interface.",
            learning_response="Learned how to structure a dashboard with cards and charts.",
            meeting_remarks="Discussed workflow and milestones with supervisor.",
            ideas_suggestions="Add a task summary chart for quick updates.",
        ),
        DailyLog(
            user_id=intern.id,
            date=date.today(),
            day="Tuesday",
            task_description="Worked on task planner and database relationships.",
            working_start_time="08:30",
            working_end_time="16:30",
            working_status="Present",
            daily_working_hours=8.0,
            tomorrow_action="Continue with document and task trackers.",
            target="Train on database models",
            daily_report_plan="Reviewed entity relationships and validated data flow.",
            learning_response="Improved understanding of relational database design.",
            meeting_remarks="Supervisor recommended working on the CRUD flow.",
            ideas_suggestions="Add progress tracking and better visual states.",
        )
    ])

    db.session.add_all([
        WeeklySummary(
            user_id=intern.id,
            week=1,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 7),
            total_working_hours=40.0,
            achievements="Built dashboard wireframe, reviewed task flow, completed first project plan.",
            work_links="https://example.com/dodl-report",
            technical_learnings="Explored database modelling and dashboard planning.",
            challenges="Need better time scheduling for documentation tasks.",
            next_week_plan="Focus on full-stack integration and task management flow.",
            self_satisfaction=4,
            mood="Motivated",
            status="Approved",
            supervisor_comments="Strong first week with good progress and clear planning.",
        ),
        LearningDiary(
            user_id=intern.id,
            date=date.today(),
            week=1,
            topic="Flask route organization",
            technical_insight="Used modular blueprint structure to manage routes and templates efficiently.",
            learning_time=2.5,
            applied_in_dodl="Implemented better separation of auth and dashboard logic.",
            proficiency_level="Intermediate",
            reflection="This improved my understanding of maintainable app structure.",
        ),
        SkillAmbassador(
            user_id=intern.id,
            week=1,
            enrolled_learners=20,
            selected_training="Introduction to Digital Skills",
            social_media_promotion="Instagram, WhatsApp",
            role="Campus Ambassador",
            ideas="Partner with student leaders to encourage social campaigns.",
            remarks="Strong promotion engagement during the first outreach cycle.",
        ),
        DocumentRecord(
            user_id=intern.id,
            document_name="Offer Letter",
            required_date=date.today(),
            submission_date=date.today(),
            verification_status="Verified",
            hard_copy_status="Submitted",
            soft_copy_link="https://drive.example.com/offer-letter",
            verification_link="https://example.com/verification/offer-letter",
            remarks="Verified by admin.",
            file_name="offer-letter.pdf",
        ),
        Notification(
            user_id=intern.id,
            title="Task assigned",
            content="A new task was assigned: Prepare weekly summary.",
            type="task",
            is_read=False,
            created_at=datetime.utcnow(),
        ),
        Notification(
            user_id=intern.id,
            title="Supervisor feedback",
            content="Supervisor approved the first weekly summary.",
            type="feedback",
            is_read=False,
            created_at=datetime.utcnow(),
        ),
        Performance(
            user_id=intern.id,
            month="September 2026",
            attendance_rate=96,
            working_hours=40,
            task_completion_rate=88,
            learning_progress=75,
            weekly_reports=2,
            document_completion=100,
            overall_score=88,
        )
    ])

    db.session.add_all([
        ActivityLog(user_id=intern.id, action="User created account", details="Intern profile was created.", created_at=datetime.utcnow()),
        ActivityLog(user_id=intern.id, action="Daily log added", details="First daily log created.", created_at=datetime.utcnow()),
        ActivityLog(user_id=supervisor.id, action="Task assigned", details="Task assigned to intern.", created_at=datetime.utcnow()),
    ])

    db.session.commit()


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = "dodl_internship_management_system_secret_key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dodl_internship.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from . import models

    with app.app_context():
        db.create_all()
        seed_demo_data()

    from .routes import bp
    app.register_blueprint(bp)

    @app.context_processor
    def inject_globals():
        return {"now": datetime.utcnow()}

    return app
