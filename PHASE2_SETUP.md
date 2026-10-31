# ToolForge Phase 2 — MySQL and secure authentication

Phase 2 adds database-backed accounts, password hashing, role-based access, CSRF protection for browser forms, and an admin overview. Existing tool routes and processors are retained.

## 1. Install dependencies

Activate your existing virtual environment and run:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Create a MySQL database

In MySQL Workbench or the MySQL command line, run:

```sql
CREATE DATABASE toolforge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'toolforge_user'@'localhost' IDENTIFIED BY 'CHOOSE_A_LONG_UNIQUE_PASSWORD';
GRANT ALL PRIVILEGES ON toolforge.* TO 'toolforge_user'@'localhost';
FLUSH PRIVILEGES;
```

For a hosted MySQL service, use the host, port, username, password, and database name supplied by that provider.

## 3. Configure `.env`

Copy `.env.example` to `.env`, generate a persistent secret, and set:

```env
SECRET_KEY=PASTE_A_LONG_RANDOM_SECRET_HERE
APP_ENV=development
DATABASE_URL=mysql+pymysql://toolforge_user:YOUR_PASSWORD@localhost:3306/toolforge
```

If your password contains characters such as `@`, `#`, `/`, or `:`, URL-encode those characters in the connection string. Never commit `.env` or share its contents.

If `DATABASE_URL` is left as `sqlite:///toolforge_dev.db`, the app uses a local SQLite database for development. Production mode requires a MySQL URL.

## 4. Start the app and create the schema

```powershell
python app.py
```

The first request creates the Phase 2 tables (`users` and `activity_logs`). For an initial setup, open the app once, then stop it if needed.

## 5. Create the first administrator

With the virtual environment active and from the project folder:

```powershell
flask --app app create-admin
```

Enter the administrator email, name, and password when prompted. Public registration always creates a normal `user` account; it cannot create an admin.

## 6. Verify

- Open `/register` and create a normal user.
- Sign out and sign back in at `/login`.
- Confirm normal users cannot access `/admin` (403).
- Sign in with the administrator account and open `/admin`.
- Confirm PDF, image, OCR, translator, TTS, QR, and utility pages still open and their API requests work.

## Security notes and current scope

- Passwords are stored as Werkzeug scrypt hashes, never as plain text.
- Login errors do not reveal whether an email is registered.
- Browser form POSTs require CSRF tokens; JSON API mutations reject explicit cross-origin Origin/Referer hosts.
- Sessions contain the account ID and role display data; protected views verify the user record for admin access.
- Phase 2 does not yet implement email verification, password reset, account lockout/rate limiting, admin user-disable controls, or database migrations. Those should be added before a public production launch.
- `db.create_all()` is used for this initial development phase. Use Alembic/Flask-Migrate migrations before evolving an existing production database.
