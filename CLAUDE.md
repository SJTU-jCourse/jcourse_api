# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run all tests
python manage.py test

# Run a specific test module
python manage.py test jcourse_api.tests.test_course

# Run tests with coverage
coverage run manage.py test && coverage report
```

## Architecture

**Stack**: Django 6 + Django REST Framework, PostgreSQL, Redis, Huey (async tasks), Authlib (OAuth)

**Django apps**:
- `jcourse_api/` — core domain: courses, reviews, semesters, notifications, enrollments
- `oauth/` — JAccount (SJTU) OAuth authentication with custom `LastSeenAtMiddleware`
- `ad/` — promotions/announcements

**Module layout** (each app follows this pattern):
- `models/` — split by domain (e.g. `course.py`, `review.py`, `user.py`)
- `serializers/` — DRF serializers mirroring model split
- `views/` — ViewSets and APIViews mirroring model split
- `urls.py` — `DefaultRouter` for ViewSets + manual `path()` for custom endpoints
- `admin.py` — uses `django-import-export` for bulk CSV import/export

**REST framework defaults** (in `jcourse/settings.py`):
- Auth: `SessionAuthentication`
- Permissions: `IsAuthenticated`
- Pagination: 20 items, configurable via `size` query param
- Throttling: `UserRateThrottle` (10/s); additional named throttles for email, auth verification, reactions

**Environment config**: All secrets and infrastructure URLs come from `.env` (loaded via `python-dotenv`). Required vars: `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `JACCOUNT_CLIENT_ID`, `JACCOUNT_CLIENT_SECRET`. Optional: `REDIS_HOST`, email SMTP vars, Qiniu storage vars, `HASH_SALT`, `SECRET_KEY`.

**Async tasks**: Huey backed by Redis; task definitions live alongside the feature code they serve.

**File uploads**: Qiniu cloud storage; upload logic in `jcourse_api/views/upload.py`.

**CI**: GitHub Actions (`.github/workflows/django.yml`) runs on Python 3.12 and 3.13 with PostgreSQL 13 + Redis services.
