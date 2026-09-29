# SmartClinic+ Architecture

## Implemented stack
- Python + Flask web application
- PostgreSQL relational database
- SQLAlchemy ORM
- HTML/CSS interface
- Git/GitHub for version control
- Pytest and GitHub Actions for automated testing

## Main modules
1. Authentication and role-based access
2. Appointment management with conflict prevention
3. Smart queue and check-in
4. Patient EHR, allergies and history
5. Lab result tracking
6. E-prescription workflow
7. Staff task assignment
8. In-app notifications
9. Operational analytics and peak-hour insight

The database uses unique constraints on doctor/time and patient/time. This provides a database-level protection against double booking and supports concurrent booking requests more safely than an application-only check.
