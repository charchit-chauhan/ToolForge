# ToolForge AI — Phase 1 Stabilization Changelog

## Scope
This phase hardens the existing Flask application without removing its current PDF, conversion, OCR, image, translation, text-to-speech, QR, utilities, theme, or browser-history features.

## Changes made

1. Protected every `/api/` route with the existing sign-in session gate. Unauthenticated API requests receive JSON HTTP 401 responses rather than HTML redirects.
2. Added centralized upload checks for expected file extensions and basic content validation for PDF, image, and DOCX uploads.
3. Kept the existing 80 MB request limit and clarified its error response.
4. Removed the predictable hard-coded Flask secret fallback. Local development generates a random key if none is configured; production refuses to start without `SECRET_KEY`.
5. Added secure session-cookie settings and standard response security headers.
6. Replaced detailed exception messages returned to clients with generic errors and server-side exception logging.
7. Changed PDF compression, image extraction, and Word/PDF conversion to use request-unique temporary directories. This prevents concurrent requests from overwriting shared temporary filenames.
8. Updated the login-page copy so it does not incorrectly claim that name/email access is full authentication or device-only storage.
9. Sanitized `.env.example`; the duplicate `env.example` file was removed from the clean project because it contained a credential. No API key is included in this package.
10. Added initial Phase 1 regression tests in `tests/test_phase1_security.py`.

## Important limitation
The current name/email sign-in remains a compatibility gate, not secure account authentication. Phase 2 will replace it with MySQL-backed registration, password hashing, session management, role-based access, and CSRF protection. Do not treat the Phase 1 login as production-grade user authentication.

## Required actions before using external translation services
An API credential was present in the uploaded `env.example`. It has been removed from this clean package, but removing it from a ZIP does not revoke it. Revoke/rotate that provider key in its dashboard and update your private local `.env`. If the ZIP or repository was pushed to a public or shared Git remote, rotate the key and clean the exposed Git history as well.

## Validation status
- Python syntax compilation: checked successfully.
- Flask runtime smoke tests: not executed in this environment because Flask and the project dependencies are not installed here.
- Automated regression tests: included; run after installing `requirements.txt` with `pytest -q`.
