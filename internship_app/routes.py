from datetime import datetime, date
from functools import wraps
import csv
import os
from io import BytesIO
from uuid import uuid4

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, send_file, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename

from . import bcrypt, db
from .models import (ActivityLog, Attendance, DailyLog, DocumentRecord,
                     LearningDiary, Notification, Performance, SkillAmbassador,
                     SupervisorFeedback, Task, User, WeeklySummary)

bp = Blueprint("main", __name__)


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("main.dashboard"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_activity(user_id, action, details):
    db.session.add(ActivityLog(user_id=user_id, action=action, details=details, created_at=datetime.utcnow()))
    db.session.commit()


def calculate_hours(start_time, end_time):
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        if end < start:
            end = end.replace(day=end.day + 1)
        return round((end - start).total_seconds() / 3600, 2)
    except Exception:
        return 0.0


@bp.route("/")
def landing():
    return render_template("landing.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.is_active and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(request.form.get("remember_me")))
            log_activity(user.id, "User logged in", "User signed in successfully.")
            flash("Welcome back!", "success")
            return redirect(url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        internship_id = request.form.get("internship_id", "").strip()
        department = request.form.get("department", "").strip()
        role = request.form.get("role", "intern").strip().lower()

        if not all([full_name, email, password, confirm_password, internship_id, department]):
            flash("Please complete all required fields.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account already exists with that email.", "danger")
        elif User.query.filter_by(internship_id=internship_id).first():
            flash("That internship ID is already in use.", "danger")
        elif role not in {"intern", "supervisor", "admin"}:
            flash("Please select a valid role.", "danger")
        else:
            new_user = User(
                full_name=full_name,
                email=email,
                password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
                internship_id=internship_id,
                department=department,
                role=role,
                is_active=True,
                bio="",
                skills="",
            )
            db.session.add(new_user)
            db.session.commit()
            log_activity(new_user.id, "User created account", "New account created.")
            flash("Your account has been created successfully.", "success")
            return redirect(url_for("main.login"))

    return render_template("register.html")


@bp.route("/logout")
@login_required
def logout():
    log_activity(current_user.id, "User logged out", "User signed out from the system.")
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))


@bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        return admin_dashboard()
    if current_user.role == "supervisor":
        return supervisor_dashboard()
    return intern_dashboard()


@bp.route("/intern-dashboard")
@login_required
def intern_dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.deadline.asc()).all()
    logs = DailyLog.query.filter_by(user_id=current_user.id).order_by(DailyLog.date.desc()).all()
    summaries = WeeklySummary.query.filter_by(user_id=current_user.id).order_by(WeeklySummary.created_at.desc()).all()
    learning = LearningDiary.query.filter_by(user_id=current_user.id).order_by(LearningDiary.date.desc()).all()
    documents = DocumentRecord.query.filter_by(user_id=current_user.id).order_by(DocumentRecord.uploaded_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()

    total_hours = sum(log.daily_working_hours or 0 for log in logs)
    learning_hours = sum(record.learning_time or 0 for record in learning)
    completed_tasks = sum(1 for task in tasks if task.status == "Completed")
    pending_tasks = sum(1 for task in tasks if task.status != "Completed")
    doc_submitted = sum(1 for doc in documents if doc.verification_status in {"Submitted", "Under Review", "Verified"})
    doc_pending = sum(1 for doc in documents if doc.verification_status == "Pending")
    tasks_progress = {
        "Pending": sum(1 for task in tasks if task.status == "Pending"),
        "In Progress": sum(1 for task in tasks if task.status == "In Progress"),
        "Completed": sum(1 for task in tasks if task.status == "Completed"),
    }

    latest_performance = Performance.query.filter_by(user_id=current_user.id).order_by(Performance.created_at.desc()).first()
    attendance_rate = latest_performance.attendance_rate if latest_performance else 0
    performance_score = latest_performance.overall_score if latest_performance else 0

    stats = {
        "total_working_hours": round(total_hours, 2),
        "learning_hours": round(learning_hours, 2),
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "attendance": attendance_rate,
        "documents_submitted": doc_submitted,
        "documents_pending": doc_pending,
        "weekly_performance": performance_score,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        tasks=tasks[:5],
        logs=logs[:5],
        notifications=notifications,
        task_progress=tasks_progress,
        recent_activity=ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.desc()).limit(5).all(),
        weekly_reports=summaries,
        learning=learning,
        documents=documents,
    )


@bp.route("/supervisor-dashboard")
@login_required
def supervisor_dashboard():
    interns = User.query.filter_by(role="intern").order_by(User.full_name.asc()).all()
    total_interns = len(interns)
    pending_reports = WeeklySummary.query.filter(WeeklySummary.status.in_(["Submitted", "Under Review"]) ).count()
    active_tasks = Task.query.filter(Task.status != "Completed").count()
    feedback_count = SupervisorFeedback.query.filter_by(supervisor_id=current_user.id).count()
    stats = {
        "total_interns": total_interns,
        "pending_reports": pending_reports,
        "active_tasks": active_tasks,
        "feedback_count": feedback_count,
    }
    return render_template("supervisor_dashboard.html", interns=interns, stats=stats)


@bp.route("/admin-dashboard")
@login_required
def admin_dashboard():
    interns = User.query.filter_by(role="intern").all()
    supervisors = User.query.filter_by(role="supervisor").all()
    tasks = Task.query.all()
    pending_documents = DocumentRecord.query.filter(DocumentRecord.verification_status == "Pending").count()
    total_hours = sum((item.working_hours or 0) for item in Performance.query.all())
    average_score = round(sum((item.overall_score or 0) for item in Performance.query.all()) / Performance.query.count(), 2) if Performance.query.count() else 0
    stats = {
        "total_interns": len(interns),
        "active_interns": sum(1 for user in interns if user.is_active),
        "total_supervisors": len(supervisors),
        "total_tasks": len(tasks),
        "completed_tasks": sum(1 for task in tasks if task.status == "Completed"),
        "pending_tasks": sum(1 for task in tasks if task.status != "Completed"),
        "total_working_hours": round(total_hours, 2),
        "average_performance": average_score,
        "pending_documents": pending_documents,
    }
    return render_template("admin_dashboard.html", stats=stats, interns=interns[:5], tasks=tasks[:5])


@bp.route("/daily-logs", methods=["GET", "POST"])
@login_required
def daily_logs():
    selected_log = None
    if request.args.get("edit_id"):
        selected_log = DailyLog.query.get_or_404(request.args.get("edit_id"))
        if current_user.role != "admin" and selected_log.user_id != current_user.id:
            abort(403)

    if request.method == "POST":
        log_id = request.form.get("log_id")
        action = request.form.get("action")
        if action == "delete" and log_id:
            log = DailyLog.query.get_or_404(log_id)
            if current_user.role != "admin" and log.user_id != current_user.id:
                abort(403)
            db.session.delete(log)
            db.session.commit()
            flash("Daily log deleted.", "success")
            return redirect(url_for("main.daily_logs"))

        date_value = request.form.get("date")
        task_description = request.form.get("task_description").strip()
        start_time = request.form.get("working_start_time")
        end_time = request.form.get("working_end_time")
        status = request.form.get("working_status")
        if not all([date_value, task_description, start_time, end_time]):
            flash("Please complete all required daily log fields.", "danger")
            return redirect(url_for("main.daily_logs"))

        daily_hours = calculate_hours(start_time, end_time)
        payload = {
            "user_id": current_user.id,
            "date": date_value,
            "day": datetime.strptime(date_value, "%Y-%m-%d").strftime("%A"),
            "task_description": task_description,
            "working_start_time": start_time,
            "working_end_time": end_time,
            "working_status": status,
            "daily_working_hours": daily_hours,
            "tomorrow_action": request.form.get("tomorrow_action"),
            "target": request.form.get("target"),
            "daily_report_plan": request.form.get("daily_report_plan"),
            "learning_response": request.form.get("learning_response"),
            "meeting_remarks": request.form.get("meeting_remarks"),
            "ideas_suggestions": request.form.get("ideas_suggestions"),
        }

        if log_id:
            log = DailyLog.query.get_or_404(log_id)
            if current_user.role != "admin" and log.user_id != current_user.id:
                abort(403)
            for key, value in payload.items():
                setattr(log, key, value)
            log.created_at = datetime.utcnow()
            message = "Daily log updated."
        else:
            log = DailyLog(**payload)
            db.session.add(log)
            message = "Daily log added."

        db.session.commit()
        log_activity(current_user.id, "Daily log added", f"Daily log for {date_value} saved.")
        flash(message, "success")
        return redirect(url_for("main.daily_logs"))

    logs = DailyLog.query.filter_by(user_id=current_user.id).order_by(DailyLog.date.desc()).all() if current_user.role == "intern" else DailyLog.query.order_by(DailyLog.date.desc()).all()
    return render_template("daily_logs.html", logs=logs, selected_log=selected_log)


@bp.route("/weekly-summaries", methods=["GET", "POST"])
@login_required
def weekly_summaries():
    selected_summary = None
    if request.args.get("edit_id"):
        selected_summary = WeeklySummary.query.get_or_404(request.args.get("edit_id"))
        if current_user.role != "admin" and selected_summary.user_id != current_user.id:
            abort(403)

    if request.method == "POST":
        summary_id = request.form.get("summary_id")
        if request.form.get("action") == "delete" and summary_id:
            summary = WeeklySummary.query.get_or_404(summary_id)
            if current_user.role != "admin" and summary.user_id != current_user.id:
                abort(403)
            db.session.delete(summary)
            db.session.commit()
            flash("Weekly summary deleted.", "success")
            return redirect(url_for("main.weekly_summaries"))

        data = {
            "user_id": current_user.id,
            "week": int(request.form.get("week", 1)),
            "start_date": request.form.get("start_date"),
            "end_date": request.form.get("end_date"),
            "total_working_hours": float(request.form.get("total_working_hours") or 0),
            "achievements": request.form.get("achievements"),
            "work_links": request.form.get("work_links"),
            "technical_learnings": request.form.get("technical_learnings"),
            "challenges": request.form.get("challenges"),
            "next_week_plan": request.form.get("next_week_plan"),
            "self_satisfaction": int(request.form.get("self_satisfaction", 0) or 0),
            "mood": request.form.get("mood"),
            "status": request.form.get("status", "Draft"),
            "supervisor_comments": request.form.get("supervisor_comments"),
        }

        if summary_id:
            summary = WeeklySummary.query.get_or_404(summary_id)
            if current_user.role != "admin" and summary.user_id != current_user.id:
                abort(403)
            for key, value in data.items():
                setattr(summary, key, value)
            message = "Weekly summary updated."
        else:
            db.session.add(WeeklySummary(**data))
            message = "Weekly summary created."
        db.session.commit()
        flash(message, "success")
        return redirect(url_for("main.weekly_summaries"))

    if current_user.role == "intern":
        summaries = WeeklySummary.query.filter_by(user_id=current_user.id).order_by(WeeklySummary.week.desc()).all()
    else:
        summaries = WeeklySummary.query.order_by(WeeklySummary.created_at.desc()).all()
    return render_template("weekly_summary.html", summaries=summaries, selected_summary=selected_summary)


@bp.route("/learning-diary", methods=["GET", "POST"])
@login_required
def learning_diary():
    selected_diary = None
    if request.args.get("edit_id"):
        selected_diary = LearningDiary.query.get_or_404(request.args.get("edit_id"))
        if current_user.role != "admin" and selected_diary.user_id != current_user.id:
            abort(403)

    if request.method == "POST":
        diary_id = request.form.get("diary_id")
        if request.form.get("action") == "delete" and diary_id:
            diary = LearningDiary.query.get_or_404(diary_id)
            if current_user.role != "admin" and diary.user_id != current_user.id:
                abort(403)
            db.session.delete(diary)
            db.session.commit()
            flash("Learning diary entry deleted.", "success")
            return redirect(url_for("main.learning_diary"))

        data = {
            "user_id": current_user.id,
            "date": request.form.get("date"),
            "week": int(request.form.get("week", 1)),
            "topic": request.form.get("topic"),
            "technical_insight": request.form.get("technical_insight"),
            "learning_time": float(request.form.get("learning_time") or 0),
            "applied_in_dodl": request.form.get("applied_in_dodl"),
            "proficiency_level": request.form.get("proficiency_level", "Beginner"),
            "reflection": request.form.get("reflection"),
        }

        if diary_id:
            diary = LearningDiary.query.get_or_404(diary_id)
            if current_user.role != "admin" and diary.user_id != current_user.id:
                abort(403)
            for key, value in data.items():
                setattr(diary, key, value)
            message = "Learning diary entry updated."
        else:
            db.session.add(LearningDiary(**data))
            message = "Learning diary entry created."

        db.session.commit()
        flash(message, "success")
        return redirect(url_for("main.learning_diary"))

    if current_user.role == "intern":
        entries = LearningDiary.query.filter_by(user_id=current_user.id).order_by(LearningDiary.date.desc()).all()
    else:
        entries = LearningDiary.query.order_by(LearningDiary.date.desc()).all()
    return render_template("learning_diary.html", entries=entries, selected_diary=selected_diary)


@bp.route("/skill-ambassador", methods=["GET", "POST"])
@login_required
def skill_ambassador():
    if request.method == "POST":
        entry_id = request.form.get("entry_id")
        data = {
            "user_id": current_user.id,
            "week": int(request.form.get("week", 1)),
            "enrolled_learners": int(request.form.get("enrolled_learners") or 0),
            "selected_training": request.form.get("selected_training"),
            "social_media_promotion": request.form.get("social_media_promotion"),
            "role": request.form.get("role"),
            "ideas": request.form.get("ideas"),
            "remarks": request.form.get("remarks"),
        }
        if entry_id:
            entry = SkillAmbassador.query.get_or_404(entry_id)
            if current_user.role != "admin" and entry.user_id != current_user.id:
                abort(403)
            for key, value in data.items():
                setattr(entry, key, value)
        else:
            db.session.add(SkillAmbassador(**data))
        db.session.commit()
        flash("Skill ambassador entry saved.", "success")
        return redirect(url_for("main.skill_ambassador"))

    entries = SkillAmbassador.query.filter_by(user_id=current_user.id).all() if current_user.role == "intern" else SkillAmbassador.query.all()
    return render_template("skill_ambassador.html", entries=entries)


@bp.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    selected_task = None
    if request.args.get("edit_id"):
        selected_task = Task.query.get_or_404(request.args.get("edit_id"))
        if current_user.role != "admin" and selected_task.user_id != current_user.id:
            abort(403)

    if request.method == "POST":
        task_id = request.form.get("task_id")
        if request.form.get("action") == "delete" and task_id:
            task = Task.query.get_or_404(task_id)
            if current_user.role != "admin" and task.user_id != current_user.id:
                abort(403)
            db.session.delete(task)
            db.session.commit()
            flash("Task deleted.", "success")
            return redirect(url_for("main.tasks"))

        data = {
            "user_id": current_user.id,
            "task_name": request.form.get("task_name"),
            "description": request.form.get("description"),
            "domain": request.form.get("domain"),
            "assigned_date": request.form.get("assigned_date") or date.today(),
            "deadline": request.form.get("deadline"),
            "week": int(request.form.get("week") or 1),
            "priority": request.form.get("priority", "Medium"),
            "status": request.form.get("status", "Pending"),
            "progress_percentage": int(request.form.get("progress_percentage") or 0),
            "assigned_by": request.form.get("assigned_by") or current_user.full_name,
            "comments": request.form.get("comments"),
        }

        if task_id:
            task = Task.query.get_or_404(task_id)
            if current_user.role != "admin" and task.user_id != current_user.id:
                abort(403)
            for key, value in data.items():
                setattr(task, key, value)
            message = "Task updated."
        else:
            db.session.add(Task(**data))
            message = "Task created."

        db.session.commit()
        flash(message, "success")
        return redirect(url_for("main.tasks"))

    if current_user.role == "intern":
        all_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.deadline.asc()).all()
    else:
        all_tasks = Task.query.order_by(Task.deadline.asc()).all()
    return render_template("tasks.html", tasks=all_tasks, selected_task=selected_task)


@bp.route("/documents", methods=["GET", "POST"])
@login_required
def documents():
    if request.method == "POST":
        document_id = request.form.get("document_id")
        file = request.files.get("file")
        saved_file = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            saved_file = filename
            file.save(current_app.config["UPLOAD_FOLDER"] + "/" + filename)

        data = {
            "user_id": current_user.id,
            "document_name": request.form.get("document_name"),
            "required_date": request.form.get("required_date"),
            "submission_date": request.form.get("submission_date") or date.today(),
            "verification_status": request.form.get("verification_status", "Pending"),
            "hard_copy_status": request.form.get("hard_copy_status", "Pending"),
            "soft_copy_link": request.form.get("soft_copy_link") or (f"/static/uploads/{saved_file}" if saved_file else ""),
            "verification_link": request.form.get("verification_link"),
            "remarks": request.form.get("remarks"),
            "file_name": saved_file,
        }

        if document_id:
            document = DocumentRecord.query.get_or_404(document_id)
            if current_user.role != "admin" and document.user_id != current_user.id:
                abort(403)
            for key, value in data.items():
                setattr(document, key, value)
            message = "Document updated."
        else:
            db.session.add(DocumentRecord(**data))
            message = "Document uploaded."
        db.session.commit()
        flash(message, "success")
        return redirect(url_for("main.documents"))

    if current_user.role == "intern":
        documents_list = DocumentRecord.query.filter_by(user_id=current_user.id).order_by(DocumentRecord.required_date.desc()).all()
    else:
        documents_list = DocumentRecord.query.order_by(DocumentRecord.required_date.desc()).all()
    return render_template("documents.html", documents=documents_list)


@bp.route("/notifications")
@login_required
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    for item in items:
        item.is_read = True
    db.session.commit()
    return render_template("notifications.html", notifications=items)


@bp.route("/performance")
@login_required
def performance():
    records = Performance.query.filter_by(user_id=current_user.id).order_by(Performance.created_at.desc()).all() if current_user.role == "intern" else Performance.query.order_by(Performance.created_at.desc()).all()
    return render_template("performance.html", performances=records)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name") or current_user.full_name
        current_user.email = request.form.get("email") or current_user.email
        current_user.department = request.form.get("department") or current_user.department
        current_user.internship_id = request.form.get("internship_id") or current_user.internship_id
        current_user.bio = request.form.get("bio") or current_user.bio
        current_user.skills = request.form.get("skills") or current_user.skills
        if request.form.get("password"):
            current_user.password_hash = bcrypt.generate_password_hash(request.form.get("password")).decode("utf-8")

        file = request.files.get("profile_picture")
        if file and file.filename:
            filename = secure_filename(file.filename)
            allowed_ext = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
            ext = os.path.splitext(filename)[1].lower()
            if ext in allowed_ext:
                os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
                unique_name = f"{current_user.id}_{uuid4().hex}{ext}"
                file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
                file.save(file_path)

                old_picture = current_user.profile_picture
                if old_picture and old_picture != "default.png" and old_picture != "default-avatar.svg":
                    old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], old_picture)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                current_user.profile_picture = unique_name
            else:
                flash("Only image files are allowed for profile pictures.", "warning")

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("main.profile"))

    return render_template("profile.html", user=current_user)


@bp.route("/reports")
@login_required
def reports():
    if current_user.role == "intern":
        user_id = current_user.id
        records = DailyLog.query.filter_by(user_id=user_id).all()
    else:
        records = DailyLog.query.all()
    return render_template("reports.html", records=records)


@bp.route("/reports/export/<format>")
@login_required
def export_reports(format):
    if current_user.role == "intern":
        records = DailyLog.query.filter_by(user_id=current_user.id).all()
    else:
        records = DailyLog.query.all()

    if format == "csv":
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Day", "Task", "Start Time", "End Time", "Hours", "Status"])
        for item in records:
            writer.writerow([item.date, item.day, item.task_description, item.working_start_time, item.working_end_time, item.daily_working_hours, item.working_status])
        output.seek(0)
        return send_file(output, mimetype="text/csv", as_attachment=True, download_name="daily_logs.csv")

    if format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "Daily Logs"
        ws.append(["Date", "Day", "Task", "Start Time", "End Time", "Hours", "Status"])
        for item in records:
            ws.append([item.date, item.day, item.task_description, item.working_start_time, item.working_end_time, item.daily_working_hours, item.working_status])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="daily_logs.xlsx")

    if format == "pdf":
        output = BytesIO()
        pdf = SimpleDocTemplate(output, pagesize=letter)
        elements = [Paragraph("Daily Logs Report"), Spacer(1, 12)]
        data = [["Date", "Day", "Hours", "Status"]]
        for item in records:
            data.append([str(item.date), item.day, str(item.daily_working_hours), item.working_status])
        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(table)
        pdf.build(elements)
        output.seek(0)
        return send_file(output, mimetype="application/pdf", as_attachment=True, download_name="daily_logs.pdf")

    flash("Unsupported export format.", "danger")
    return redirect(url_for("main.reports"))


@bp.route("/admin/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_users():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        if request.form.get("action") == "delete" and user_id:
            user = User.query.get_or_404(user_id)
            db.session.delete(user)
            db.session.commit()
            flash("User deleted.", "success")
            return redirect(url_for("main.admin_users"))

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        role = request.form.get("role")
        department = request.form.get("department")
        if not all([full_name, email, role, department]):
            flash("Please fill all required user fields.", "danger")
            return redirect(url_for("main.admin_users"))

        if user_id:
            user = User.query.get_or_404(user_id)
            user.full_name = full_name
            user.email = email
            user.role = role
            user.department = department
            if request.form.get("password"):
                user.password_hash = bcrypt.generate_password_hash(request.form.get("password")).decode("utf-8")
        else:
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash("A user with that email already exists.", "danger")
                return redirect(url_for("main.admin_users"))
            user = User(
                full_name=full_name,
                email=email,
                department=department,
                role=role,
                internship_id=request.form.get("internship_id") or f"USER-{User.query.count() + 1}",
                password_hash=bcrypt.generate_password_hash(request.form.get("password") or "Password@123").decode("utf-8"),
                is_active=True,
            )
            db.session.add(user)
        db.session.commit()
        flash("User saved successfully.", "success")
        return redirect(url_for("main.admin_users"))

    users = User.query.order_by(User.full_name.asc()).all()
    return render_template("admin_users.html", users=users)


@bp.route("/interns")
@login_required
def interns():
    interns_list = User.query.filter_by(role="intern").all() if current_user.role in {"admin", "supervisor"} else [current_user]
    return render_template("interns.html", interns=interns_list)


@bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        user_id = int(request.form.get("user_id") or current_user.id)
        if current_user.role == "intern":
            supervisor_id = current_user.supervisor_id or 1
        else:
            supervisor_id = current_user.id
        feedback_entry = SupervisorFeedback(
            user_id=user_id,
            supervisor_id=supervisor_id,
            entity_type=request.form.get("entity_type", "Task"),
            entity_id=int(request.form.get("entity_id") or 0),
            rating=int(request.form.get("rating") or 0),
            comment=request.form.get("comment"),
            approval_state=request.form.get("approval_state", "Pending"),
        )
        db.session.add(feedback_entry)
        db.session.commit()
        flash("Feedback submitted.", "success")
        return redirect(url_for("main.feedback"))

    feedback_list = SupervisorFeedback.query.filter_by(user_id=current_user.id).all() if current_user.role == "intern" else SupervisorFeedback.query.filter_by(supervisor_id=current_user.id).all()
    return render_template("feedback.html", feedback_list=feedback_list)


@bp.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@bp.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


@bp.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500
