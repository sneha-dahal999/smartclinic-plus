# SmartClinic+

SmartClinic+ is a Python/Flask outpatient healthcare management prototype aligned to the SENG205 T2 2026 project brief.

## Team

- **Dinuwan Kavinda Karunathilaka — K250309 — Requirements and project analysis**
- **Sneha Dahal — K250068 — Design, architecture and prototype**
- **Adarsha Panta — K250081 — QA, testing and project management**

## Implemented prototype

- Role-based login for admin, doctor, nurse and patient users
- Appointment booking, rescheduling and cancellation
- Database-level protection against double booking
- Patient check-in and smart queue states
- Patient EHR with allergies and medical history
- Lab result tracking
- Doctor e-prescription workflow
- Staff task assignment and completion
- In-app appointment notifications
- Operational analytics: appointment volume by hour and average queue wait
- PostgreSQL database through SQLAlchemy
- Pytest automated tests and GitHub Actions CI

## Technology

Python, Flask, Flask-SQLAlchemy, PostgreSQL, HTML/CSS, GitHub Actions and Pytest.

## Run locally

1. Install Docker Desktop.
2. Start PostgreSQL:
   `docker compose up -d db`
3. Create a virtual environment and install dependencies:
   `python -m pip install -r requirements.txt`
4. Set the database URL if required:
   `DATABASE_URL=postgresql+psycopg2://smartclinic:smartclinic@localhost:5432/smartclinic`
5. Start the app:
   `python app.py`
6. Open `http://127.0.0.1:5000/login`.

The database and demo records are created automatically on first startup.

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin123! |
| Doctor | doctor | Doctor123! |
| Nurse | nurse | Nurse123! |
| Patient | patient | Patient123! |

These are development/demo credentials only and must be changed or removed before production use.

## Testing

Run:

```text
python -m pytest -v
```

GitHub Actions runs the same test suite on pushes and pull requests to `main` and `development`.

## Project structure

- `app.py` — Flask application, database models and routes
- `templates/` — web interface
- `static/` — CSS
- `tests/` — automated tests
- `docs/` — architecture, requirements and testing notes
- `.github/workflows/` — continuous integration
- `docker-compose.yml` — local PostgreSQL service

## Scope note

External SMS/email delivery and production-grade deployment controls are outside this prototype. The current notification feature records in-app notifications. Production deployment should use managed PostgreSQL, TLS, secret management, backups, audit logging and a real SMS/email provider.
