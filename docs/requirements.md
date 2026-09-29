# Requirements and implementation mapping

The project brief describes SmartClinic+ as an integrated outpatient healthcare management system covering appointments, queue management, staff coordination, clinical records, diagnostics and analytics. The prototype implements the main workflow areas below.

| Brief area | Implemented prototype feature |
|---|---|
| Online appointment booking | Appointment creation with doctor availability protected by database constraints |
| Reschedule/cancel | Appointment rescheduling and cancellation |
| Smart queue | Check-in, priority, call and completion states |
| Notifications | In-app appointment notification records |
| Doctor dashboard/workflow | Role-based doctor access to appointments and EHR/prescriptions |
| E-prescription | Doctor-only prescription creation linked to a patient |
| Task assignment | Staff task creation, assignment and completion |
| EHR | Patient history, allergies and diagnoses/history fields |
| Lab/test integration | Lab results linked to patient records |
| Data privacy | Role-based route controls and patient self-record restriction |
| Operational dashboard | Appointment, queue, patient and doctor counts |
| Analytics | Hourly appointment volume and average queue wait |
| Predictive insight | Historical peak-hour insight to support staffing decisions |

## Security and integrity

Passwords are stored as Werkzeug password hashes rather than plain text. Sensitive patient routes are protected by role checks. Appointment conflicts are enforced at database level with unique constraints on doctor/time and patient/time. This is important for concurrent requests because an application-only availability check can still race; the database constraint is the final integrity control.

## Known prototype limitations

The brief calls for SMS/email reminders and encryption for sensitive data. This prototype provides an in-app notification log and hashed passwords, but does not connect to an external SMS/email provider or implement production database-at-rest encryption. Those controls should be added for deployment beyond the academic prototype.
