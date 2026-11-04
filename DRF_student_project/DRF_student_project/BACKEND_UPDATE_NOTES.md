# SAMS backend update notes

## Changes in this package

- Preserved the existing Django app, models, API views, serializers, role setup, profile-correction/OCR workflow, subject selection, skills, jobs, applications, interviews, selections and notification code.
- Added `EligibilityCheck.input_fingerprint` and migration `0025_eligibilitycheck_input_fingerprint`.
- Eligibility checks now avoid creating a duplicate check when the same student/job inputs have not changed. Teachers can check only students in their assigned courses. Admins can also run checks.
- The `eligible-students/?job=<job_id>` endpoint now returns saved, current results in separate eligible, ineligible and stale lists. Teachers are limited to assigned courses. Registration Officers can inspect a selected teacher's saved results using `&teacher=<user_id>`; they cannot run checks.
- Job opportunity notification sending accepts Teacher and Registration Officer roles. Teachers remain restricted to their assigned courses. Notifications are sent only when a current saved eligible check exists.
- Admin application listing accepts both `?course=<course_id>` and `?job=<job_id>` filters.
- Removed the uploaded `.env` containing credentials and moved Django secret/database settings to environment variables. Added `.env.example`.
- Replaced the incomplete requirements list with the packages used by the project, including PostgreSQL, CORS, dotenv, Celery/Redis and OCR dependencies.

## Apply on Windows

1. Back up your current project folder and database first.
2. Copy this backend folder into your workspace (do not overwrite your only backup).
3. Create/activate your virtual environment.
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and enter your local PostgreSQL credentials and a new Django secret key.
6. Ensure PostgreSQL is running and the database named in `.env` exists.
7. Run: `python manage.py check`
8. Run: `python manage.py showmigrations students`
9. Run: `python manage.py migrate`
10. Run: `python manage.py runserver`

Redis/Celery and OCR system binaries (Tesseract and Poppler for PDF OCR) may need separate installation/configuration depending on which background/OCR functions you use. Email/SMS delivery also requires provider credentials; the package does not claim SMS delivery is configured.

## Verification limitation

Python source compilation passed (`python -m compileall`). Django runtime checks, migrations against your PostgreSQL database, API integration tests and Excel import workflows were not run in this environment. Review and test those in your Windows virtual environment before replacing a live deployment.

## API notes

- Teacher check: `POST /api/eligibility/check/` with `{ "student": <student_id>, "job": <job_id> }`
- Saved results: `GET /api/eligible-students/?job=<job_id>`
- Officer saved results: `GET /api/eligible-students/?job=<job_id>&teacher=<teacher_user_id>`
- Send eligible job notifications: `POST /api/notifications/send-eligible-job/` with `{ "job": <job_id>, "student_ids": [<student_id>, ...] }`
- Admin application filters: `GET /api/applications/?course=<course_id>&job=<job_id>`
