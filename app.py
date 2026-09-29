import os
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"))


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    allergies = db.Column(db.Text, default="")
    medical_history = db.Column(db.Text, default="")


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    specialty = db.Column(db.String(120), nullable=False)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Booked")
    reason = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint("doctor_id", "scheduled_at", name="uq_doctor_slot"),
        UniqueConstraint("patient_id", "scheduled_at", name="uq_patient_slot"),
    )


class QueueEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), unique=True, nullable=False)
    check_in_at = db.Column(db.DateTime, default=datetime.utcnow)
    called_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    priority = db.Column(db.String(20), default="Normal")
    status = db.Column(db.String(30), default="Waiting")


class LabResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    test_name = db.Column(db.String(120), nullable=False)
    result = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="Final")
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    medication = db.Column(db.String(160), nullable=False)
    dosage = db.Column(db.String(120), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(30), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    kind = db.Column(db.String(30), default="Reminder")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://smartclinic:smartclinic@localhost:5432/smartclinic",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_demo_data()

    return app


def seed_demo_data():
    if Doctor.query.count() == 0:
        db.session.add_all([
            Doctor(name="Dr. Maya Chen", specialty="General Medicine"),
            Doctor(name="Dr. Liam Patel", specialty="Cardiology"),
            Doctor(name="Dr. Sofia Nguyen", specialty="Dermatology"),
        ])
        db.session.flush()

    if Patient.query.count() == 0:
        db.session.add_all([
            Patient(
                name="Alex Morgan",
                dob=datetime(1995, 5, 12).date(),
                phone="0400000001",
                email="alex@example.com",
                allergies="Penicillin",
                medical_history="Asthma",
            ),
            Patient(
                name="Jordan Lee",
                dob=datetime(1988, 9, 3).date(),
                phone="0400000002",
                email="jordan@example.com",
                allergies="None known",
                medical_history="Hypertension",
            ),
        ])
        db.session.flush()

    if User.query.count() == 0:
        patients = Patient.query.order_by(Patient.id).all()
        doctors = Doctor.query.order_by(Doctor.id).all()
        db.session.add_all([
            User(username="admin", password_hash=generate_password_hash("Admin123!"), role="admin"),
            User(username="doctor", password_hash=generate_password_hash("Doctor123!"), role="doctor", doctor_id=doctors[0].id),
            User(username="nurse", password_hash=generate_password_hash("Nurse123!"), role="nurse"),
            User(username="patient", password_hash=generate_password_hash("Patient123!"), role="patient", patient_id=patients[0].id),
        ])
        db.session.commit()


app = create_app()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_current_user():
    user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    return {"current_user": user}


@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            session["patient_id"] = user.patient_id
            session["doctor_id"] = user.doctor_id
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    today = datetime.utcnow().date()
    appointment_count = Appointment.query.filter(func.date(Appointment.scheduled_at) == today).count()
    waiting_count = QueueEntry.query.filter_by(status="Waiting").count()
    patient_count = Patient.query.count()
    doctor_count = Doctor.query.count()
    notifications = Notification.query.filter_by(user_id=session["user_id"], read=False).order_by(Notification.created_at.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        appointment_count=appointment_count,
        waiting_count=waiting_count,
        patient_count=patient_count,
        doctor_count=doctor_count,
        notifications=notifications,
    )


@app.route("/appointments")
@login_required
def appointments():
    query = Appointment.query.order_by(Appointment.scheduled_at.desc()).all()
    patients = {p.id: p for p in Patient.query.all()}
    doctors = {d.id: d for d in Doctor.query.all()}
    return render_template("appointments.html", appointments=query, patients=patients, doctors=doctors)


@app.route("/appointments/new", methods=["GET", "POST"])
@login_required
def new_appointment():
    doctors = Doctor.query.order_by(Doctor.name).all()
    patients = Patient.query.order_by(Patient.name).all()

    if request.method == "POST":
        try:
            doctor_id = int(request.form["doctor_id"])
            scheduled_at = datetime.fromisoformat(request.form["scheduled_at"])
            patient_id = session.get("patient_id") if session.get("role") == "patient" else int(request.form["patient_id"])
            reason = request.form.get("reason", "").strip()

            if scheduled_at <= datetime.utcnow():
                flash("Appointment time must be in the future.", "danger")
                return render_template("appointment_form.html", doctors=doctors, patients=patients)

            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                scheduled_at=scheduled_at,
                reason=reason,
            )
            db.session.add(appointment)
            db.session.flush()

            user = User.query.filter_by(patient_id=patient_id).first()
            if user:
                db.session.add(Notification(
                    user_id=user.id,
                    message=f"Appointment booked for {scheduled_at:%d %b %Y %H:%M}.",
                    kind="Appointment",
                ))
            db.session.commit()
            flash("Appointment booked successfully.", "success")
            return redirect(url_for("appointments"))
        except (ValueError, TypeError, KeyError):
            db.session.rollback()
            flash("Please provide valid appointment details.", "danger")
        except IntegrityError:
            db.session.rollback()
            flash("That time slot is already booked for the doctor or patient.", "danger")

    return render_template("appointment_form.html", doctors=doctors, patients=patients)


@app.route("/appointments/<int:appointment_id>/reschedule", methods=["POST"])
@login_required
def reschedule_appointment(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("appointments"))
    if session["role"] == "patient" and appointment.patient_id != session.get("patient_id"):
        flash("You can only reschedule your own appointments.", "danger")
        return redirect(url_for("appointments"))
    try:
        new_time = datetime.fromisoformat(request.form["scheduled_at"])
        if new_time <= datetime.utcnow():
            flash("New appointment time must be in the future.", "danger")
            return redirect(url_for("appointments"))
        appointment.scheduled_at = new_time
        db.session.commit()
        flash("Appointment rescheduled.", "success")
    except (ValueError, KeyError):
        db.session.rollback()
        flash("Please provide a valid date and time.", "danger")
    except IntegrityError:
        db.session.rollback()
        flash("That new time is already booked for the doctor or patient.", "danger")
    return redirect(url_for("appointments"))


@app.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("appointments"))

    if session["role"] == "patient" and appointment.patient_id != session.get("patient_id"):
        flash("You can only cancel your own appointments.", "danger")
        return redirect(url_for("appointments"))

    appointment.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("appointments"))


@app.route("/queue")
@roles_required("admin", "doctor", "nurse")
def queue():
    entries = QueueEntry.query.order_by(
        QueueEntry.status.asc(),
        QueueEntry.priority.desc(),
        QueueEntry.check_in_at.asc(),
    ).all()
    appointments = {a.id: a for a in Appointment.query.all()}
    patients = {p.id: p for p in Patient.query.all()}
    return render_template("queue.html", entries=entries, appointments=appointments, patients=patients)


@app.route("/queue/check-in/<int:appointment_id>", methods=["POST"])
@roles_required("admin", "doctor", "nurse", "patient")
def check_in(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment or appointment.status == "Cancelled":
        flash("Appointment cannot be checked in.", "danger")
        return redirect(url_for("appointments"))
    if session["role"] == "patient" and appointment.patient_id != session.get("patient_id"):
        flash("You can only check in for your own appointment.", "danger")
        return redirect(url_for("appointments"))

    if not QueueEntry.query.filter_by(appointment_id=appointment_id).first():
        db.session.add(QueueEntry(appointment_id=appointment_id, priority="Emergency" if request.form.get("priority") == "Emergency" else "Normal"))
        appointment.status = "Checked-in"
        db.session.commit()
        flash("Patient added to the queue.", "success")
    return redirect(url_for("queue" if session["role"] != "patient" else "appointments"))


@app.route("/queue/<int:entry_id>/call", methods=["POST"])
@roles_required("admin", "doctor", "nurse")
def call_queue(entry_id):
    entry = db.session.get(QueueEntry, entry_id)
    if entry:
        entry.status = "In Consultation"
        entry.called_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for("queue"))


@app.route("/queue/<int:entry_id>/complete", methods=["POST"])
@roles_required("admin", "doctor", "nurse")
def complete_queue(entry_id):
    entry = db.session.get(QueueEntry, entry_id)
    if entry:
        entry.status = "Completed"
        entry.completed_at = datetime.utcnow()
        appointment = db.session.get(Appointment, entry.appointment_id)
        appointment.status = "Completed"
        db.session.commit()
    return redirect(url_for("queue"))


@app.route("/patients")
@roles_required("admin", "doctor", "nurse")
def patients():
    return render_template("patients.html", patients=Patient.query.order_by(Patient.name).all())


@app.route("/patients/<int:patient_id>")
@login_required
def patient_record(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("dashboard"))

    if session["role"] == "patient" and session.get("patient_id") != patient_id:
        flash("You can only view your own health record.", "danger")
        return redirect(url_for("dashboard"))

    labs = LabResult.query.filter_by(patient_id=patient_id).order_by(LabResult.recorded_at.desc()).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()
    return render_template("patient_record.html", patient=patient, labs=labs, prescriptions=prescriptions)


@app.route("/patients/<int:patient_id>/labs", methods=["POST"])
@roles_required("admin", "doctor", "nurse")
def add_lab(patient_id):
    db.session.add(LabResult(
        patient_id=patient_id,
        test_name=request.form.get("test_name", "").strip(),
        result=request.form.get("result", "").strip(),
        status=request.form.get("status", "Final"),
    ))
    db.session.commit()
    flash("Lab result recorded.", "success")
    return redirect(url_for("patient_record", patient_id=patient_id))


@app.route("/patients/<int:patient_id>/prescriptions", methods=["POST"])
@roles_required("admin", "doctor")
def add_prescription(patient_id):
    user = db.session.get(User, session["user_id"])
    if not user.doctor_id:
        flash("A doctor account is required to issue prescriptions.", "danger")
        return redirect(url_for("patient_record", patient_id=patient_id))

    db.session.add(Prescription(
        patient_id=patient_id,
        doctor_id=user.doctor_id,
        medication=request.form.get("medication", "").strip(),
        dosage=request.form.get("dosage", "").strip(),
        instructions=request.form.get("instructions", "").strip(),
    ))
    db.session.commit()
    flash("Prescription created.", "success")
    return redirect(url_for("patient_record", patient_id=patient_id))


@app.route("/tasks")
@roles_required("admin", "doctor", "nurse")
def tasks():
    task_rows = Task.query.order_by(Task.created_at.desc()).all()
    users = {u.id: u for u in User.query.all()}
    patients = {p.id: p for p in Patient.query.all()}
    return render_template("tasks.html", tasks=task_rows, users=users, patients=patients)


@app.route("/tasks/new", methods=["POST"])
@roles_required("admin", "doctor", "nurse")
def new_task():
    db.session.add(Task(
        title=request.form.get("title", "").strip(),
        patient_id=int(request.form["patient_id"]) if request.form.get("patient_id") else None,
        assigned_to=int(request.form["assigned_to"]) if request.form.get("assigned_to") else None,
    ))
    db.session.commit()
    flash("Task assigned.", "success")
    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
@roles_required("admin", "doctor", "nurse")
def complete_task(task_id):
    task = db.session.get(Task, task_id)
    if task:
        task.status = "Completed"
        db.session.commit()
    return redirect(url_for("tasks"))


@app.route("/notifications")
@login_required
def notifications():
    rows = Notification.query.filter_by(user_id=session["user_id"]).order_by(Notification.created_at.desc()).all()
    for row in rows:
        row.read = True
    db.session.commit()
    return render_template("notifications.html", notifications=rows)


@app.route("/analytics")
@roles_required("admin", "doctor", "nurse")
def analytics():
    appointments = Appointment.query.all()
    by_hour = {}
    for appointment in appointments:
        hour = appointment.scheduled_at.hour
        by_hour[hour] = by_hour.get(hour, 0) + 1
    peak_hour = max(by_hour, key=by_hour.get) if by_hour else None

    completed_waits = []
    for entry in QueueEntry.query.filter(QueueEntry.called_at.isnot(None)).all():
        completed_waits.append((entry.called_at - entry.check_in_at).total_seconds() / 60)
    average_wait = round(sum(completed_waits) / len(completed_waits), 1) if completed_waits else 0

    return render_template(
        "analytics.html",
        by_hour=sorted(by_hour.items()),
        peak_hour=peak_hour,
        average_wait=average_wait,
    )


if __name__ == "__main__":
    app.run(debug=True)
