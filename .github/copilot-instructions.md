# GCX Supplier Application Portal — AI Agent Instructions

## Project Overview
- **Architecture**: Django 5.2.6 backend with REST API, real-time features (Channels/Redis), and multi-step HTML/Bootstrap frontend. Key apps: `accounts`, `applications`, `core`, `documents`, `notifications`, `reviews`.
- **Major Data Flows**:
  - Applicants submit via `/apply/` (multi-step form, tracking code generated).
  - Admins review, request docs, approve/reject via backoffice.
  - Document upload, verification, and review are tightly coupled across `applications`, `documents`, and `reviews`.
  - Notifications (email/SMS) sent via `notifications` app and external API.

## Developer Workflows
- **Setup**:
  - Create `.env` (see README for required keys).
  - Use `python -m venv venv` and `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac).
  - Install dependencies: `pip install -r requirements.txt`.
  - Migrate DB: `python manage.py migrate`.
  - Seed data: `python manage.py seed_data`.
  - Create superuser: `python manage.py createsuperuser` (or use seeded admin).
- **Run/Debug**:
  - Start all services: `start_all.bat` (Windows) or run each: `start_redis.bat`, `start_celery.bat`, `start_celery_beat.bat`, `start_django.bat`.
  - For real-time debugging, see `REALTIME_SETUP.md` for Redis, Celery, and WebSocket checks.
- **Testing**:
  - Run all tests: `python manage.py test`.
  - App-specific: `python manage.py test applications`.
  - Automated scripts: see `TESTING.md` for batch/sh scripts and CI config.

## Key Conventions & Patterns
- **Custom User Model**: All auth logic in `accounts/`.
- **Application Workflow**: Statuses (`PENDING_REVIEW`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`) drive business logic and notification triggers.
- **Document Requirements**: Defined in `core` and `documents` apps; checklist in `reviews/models.py`.
- **Notifications**: Use `NotificationService` in `notifications/services.py` for all outbound messages. External API URL is configurable via settings/migrations.
- **Audit Logging**: All admin actions logged in `core/models.py:AuditLog`.
- **Security**: File type/size validation, phone/email validation, signed tokens for uploads, role-based access.

## Integration Points
- **External Notification API**: URL and timeout in settings/migrations; see `notifications/services.py`.
- **WebSockets**: Routing in `applications/routing.py`.
- **Celery**: Background and scheduled tasks in `applications/background_tasks.py` and `applications/tasks.py`.

## Examples
- **Seed Data**: `python manage.py seed_data` creates regions, commodities, document requirements.
- **API Endpoints**: See README for public/admin endpoints and usage.
- **Review Checklist**: See `reviews/models.py:ReviewChecklist` for required docs.

## References
- `README.md`, `TESTING.md`, `DOCKER_SETUP.md`, `REALTIME_SETUP.md` — for setup, workflow, and troubleshooting.
- `applications/`, `documents/`, `reviews/`, `notifications/` — for main business logic and integration.

---
**Feedback:** If any section is unclear or missing, please specify so it can be improved for future AI agents.
