import os
from datetime import datetime, timedelta

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import app, db, Appointment, Doctor, Patient, User


@pytest.fixture
def client():
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.drop_all()
        db.create_all()
        doctor = Doctor(name="Test Doctor", specialty="General Medicine")
        patient = Patient(name="Test Patient", dob=datetime(1990, 1, 1).date())
        db.session.add_all([doctor, patient])
        db.session.flush()
        db.session.add(User(username="patient", password_hash="scrypt:32768:8:1$placeholder$placeholder", role="patient", patient_id=patient.id))
        db.session.commit()
    with app.test_client() as test_client:
        yield test_client


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"SmartClinic+" in response.data


def test_protected_dashboard_redirects(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_invalid_login(client):
    response = client.post("/login", data={"username": "nobody", "password": "wrong"})
    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_double_booking_is_rejected(client):
    with client.application.app_context():
        doctor = Doctor.query.first()
        patient = Patient.query.first()
        when = datetime.utcnow() + timedelta(days=1)
        db.session.add(Appointment(patient_id=patient.id, doctor_id=doctor.id, scheduled_at=when))
        db.session.commit()
        db.session.add(Appointment(patient_id=patient.id, doctor_id=doctor.id, scheduled_at=when))
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


def test_role_access_blocks_patient_from_queue(client):
    with client.session_transaction() as session:
        user = User.query.filter_by(username="patient").first()
        session["user_id"] = user.id
        session["role"] = "patient"
        session["patient_id"] = user.patient_id
    response = client.get("/queue")
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]
