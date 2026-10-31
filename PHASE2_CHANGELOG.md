# Phase 2 changelog

## Added
- SQLAlchemy database layer and `User` / `ActivityLog` models.
- MySQL support through `DATABASE_URL` and PyMySQL; SQLite local-development fallback.
- Registration and password-based login.
- Werkzeug scrypt password hashing.
- User/admin roles and an admin-only dashboard.
- Interactive `flask --app app create-admin` command.
- Account validation on each request and authenticated API checks.
- CSRF tokens for browser forms and same-origin checks for existing JSON API mutations.
- Login/logout/registration activity records.

## Preserved
- Existing PDF, Word conversion, OCR, image, translation, TTS, QR, utility, and history routes and processors.
- Existing Phase 1 upload validation, security headers, session settings, and temporary-file isolation.

## Validation
- Python syntax compilation completed for `app.py`, `models.py`, `processors.py`, and the security tests.
- Full pytest runtime execution was not possible in the build environment because Flask and the new dependencies are not installed and package network access is unavailable. Run the setup and test commands in `PHASE2_SETUP.md` locally.
