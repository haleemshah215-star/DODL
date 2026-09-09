# DODL Internship Management System

A full-stack Flask internship management platform for DODL with:

- Role-based authentication for admin, supervisor, and intern
- Daily logs and weekly summaries
- Learning diary and skill ambassador tracking
- Task planner and document management
- Notifications, reports, and dashboards
- Profile management with optional profile image upload
- Ready for local development and one-click Vercel deployment

## Tech Stack

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- SQLite / PostgreSQL
- Bootstrap CSS

## Project Structure

- `app.py` - Local Flask app entry point
- `api/index.py` - Vercel serverless function entry point
- `vercel.json` - Vercel deployment routing configuration
- `internship_app/` - Core application package (models, routes, database)
- `templates/` - HTML templates
- `static/` - CSS, JS, and uploaded files
- `requirements.txt` - Python dependencies

---

## Deploy to Vercel (GitHub Integration)

1. **Commit and push all changes to GitHub**:
   ```bash
   git add .
   git commit -m "Fix Vercel deployment configuration and bugs"
   git push origin main
   ```

2. **Deploy on Vercel**:
   - Go to [vercel.com](https://vercel.com) and log in.
   - Click **Add New...** -> **Project**.
   - Select your GitHub repository (`DODL`).
   - Keep default settings:
     - **Framework Preset**: Other
     - **Root Directory**: `./` (leave as default root)
     - **Build Command**: (leave blank)
     - **Output Directory**: (leave blank)
   - Click **Deploy**.

3. **(Optional) Persistent Cloud Database**:
   - By default, the app initializes sample demo data automatically in `/tmp/dodl_internship.db`.
   - If you want persistent database storage across all serverless cold starts, create a free database on [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com).
   - In Vercel Project **Settings** -> **Environment Variables**, add:
     - `DATABASE_URL`: `postgresql://user:password@host/database?sslmode=require`
     - `SECRET_KEY`: `your-secure-random-secret-key`
   - Redeploy the project.

---

## Run Locally

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

---

## Demo Accounts

- **Admin**: `admin@dodl.edu` / `Admin@123`
- **Supervisor**: `supervisor@dodl.edu` / `Supervisor@123`
- **Intern**: `intern@dodl.edu` / `Intern@123`

---

## Notes

- Uploaded profile images are saved safely in `static/uploads/` (or `/tmp/uploads` on Vercel).
- Vercel reverse proxy headers are handled via `ProxyFix` middleware.
