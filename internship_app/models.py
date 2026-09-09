from datetime import datetime, date

from flask_login import UserMixin

from . import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    internship_id = db.Column(db.String(80), unique=True, nullable=True)
    department = db.Column(db.String(120), default="General")
    role = db.Column(db.String(30), default="intern")
    is_active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(255), default="default.png")
    internship_start = db.Column(db.Date, nullable=True, default=date.today)
    internship_end = db.Column(db.Date, nullable=True)
    bio = db.Column(db.Text, default="")
    skills = db.Column(db.Text, default="")
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    supervisor = db.relationship("User", remote_side=[id], backref=db.backref("interns", lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    daily_logs = db.relationship("DailyLog", backref="user", lazy=True)
    weekly_summaries = db.relationship("WeeklySummary", backref="user", lazy=True)
    learning_diaries = db.relationship("LearningDiary", backref="user", lazy=True)
    skill_ambassadors = db.relationship("SkillAmbassador", backref="user", lazy=True)
    documents = db.relationship("DocumentRecord", backref="user", lazy=True)
    tasks = db.relationship("Task", backref="user", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)
    performances = db.relationship("Performance", backref="user", lazy=True)
    activity_logs = db.relationship("ActivityLog", backref="user", lazy=True)

    @property
    def password(self):
        raise AttributeError("Password is not readable")


class DailyLog(db.Model):
    __tablename__ = "daily_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    day = db.Column(db.String(50), nullable=False)
    task_description = db.Column(db.Text, nullable=False)
    working_start_time = db.Column(db.String(20), nullable=False)
    working_end_time = db.Column(db.String(20), nullable=False)
    working_status = db.Column(db.String(50), default="Present")
    daily_working_hours = db.Column(db.Float, default=0.0)
    tomorrow_action = db.Column(db.Text)
    target = db.Column(db.String(200))
    daily_report_plan = db.Column(db.Text)
    learning_response = db.Column(db.Text)
    meeting_remarks = db.Column(db.Text)
    ideas_suggestions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WeeklySummary(db.Model):
    __tablename__ = "weekly_summaries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_working_hours = db.Column(db.Float, default=0.0)
    achievements = db.Column(db.Text)
    work_links = db.Column(db.Text)
    technical_learnings = db.Column(db.Text)
    challenges = db.Column(db.Text)
    next_week_plan = db.Column(db.Text)
    self_satisfaction = db.Column(db.Integer, default=0)
    mood = db.Column(db.String(50), default="Neutral")
    status = db.Column(db.String(30), default="Draft")
    supervisor_comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LearningDiary(db.Model):
    __tablename__ = "learning_diary"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    technical_insight = db.Column(db.Text, nullable=False)
    learning_time = db.Column(db.Float, default=0.0)
    applied_in_dodl = db.Column(db.Text)
    proficiency_level = db.Column(db.String(30), default="Beginner")
    reflection = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SkillAmbassador(db.Model):
    __tablename__ = "skill_ambassador"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    enrolled_learners = db.Column(db.Integer, default=0)
    selected_training = db.Column(db.String(200))
    social_media_promotion = db.Column(db.String(200))
    role = db.Column(db.String(50), default="Ambassador")
    ideas = db.Column(db.Text)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DocumentRecord(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    document_name = db.Column(db.String(200), nullable=False)
    required_date = db.Column(db.Date, nullable=False)
    submission_date = db.Column(db.Date, nullable=True)
    verification_status = db.Column(db.String(30), default="Pending")
    hard_copy_status = db.Column(db.String(30), default="Pending")
    soft_copy_link = db.Column(db.String(255))
    verification_link = db.Column(db.String(255))
    remarks = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    domain = db.Column(db.String(100), default="General")
    assigned_date = db.Column(db.Date, nullable=False, default=date.today)
    deadline = db.Column(db.Date, nullable=False)
    week = db.Column(db.Integer, default=1)
    priority = db.Column(db.String(20), default="Medium")
    status = db.Column(db.String(30), default="Pending")
    progress_percentage = db.Column(db.Integer, default=0)
    assigned_by = db.Column(db.String(150), default="System")
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TaskComment(db.Model):
    __tablename__ = "task_comments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SupervisorFeedback(db.Model):
    __tablename__ = "supervisor_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    entity_type = db.Column(db.String(50), default="Task")
    entity_id = db.Column(db.Integer, default=0)
    rating = db.Column(db.Integer, default=0)
    comment = db.Column(db.Text)
    approval_state = db.Column(db.String(30), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default="info")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    present = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Performance(db.Model):
    __tablename__ = "performance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    month = db.Column(db.String(60), nullable=False)
    attendance_rate = db.Column(db.Float, default=0.0)
    working_hours = db.Column(db.Float, default=0.0)
    task_completion_rate = db.Column(db.Float, default=0.0)
    learning_progress = db.Column(db.Float, default=0.0)
    weekly_reports = db.Column(db.Integer, default=0)
    document_completion = db.Column(db.Float, default=0.0)
    overall_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
