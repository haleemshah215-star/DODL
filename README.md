# DODL Internship Management System

A full-stack Flask internship management platform for DODL with:

- Role-based authentication for admin, supervisor, and intern
- Daily logs and weekly summaries
- Learning diary and skill ambassador tracking
- Task planner and document management
- Notifications, reports, and dashboards
- Profile management with optional profile image upload

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- SQLite
- Bootstrap CSS

## Project Structure

- `app.py` - app entry point
- `internship_app/` - core application package
- `templates/` - HTML templates
- `static/` - CSS, JS, and uploaded files
- `requirements.txt` - Python dependencies

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open in browser:
   ```text
   http://localhost:5000/
   ```

## Demo Accounts

- Admin: `admin@dodl.edu` / `Admin@123`
- Supervisor: `supervisor@dodl.edu` / `Supervisor@123`
- Intern: `intern@dodl.edu` / `Intern@123`

## Notes

- Uploaded profile images are stored in `static/uploads/`.
- A default placeholder avatar is included for users without a profile picture.
