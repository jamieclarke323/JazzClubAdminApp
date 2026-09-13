# Jazz Club

A two-person household life admin app built with Django for a calm, mobile-first daily dashboard focused on admin tasks and shared shopping.

## Local development

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Set environment variables (optional for local SQLite):
   ```bash
   export DJANGO_SECRET_KEY='your-secret-key'
   export DEBUG='True'
   export ALLOWED_HOSTS='localhost,127.0.0.1'
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create the default household and categories:
   ```bash
   python manage.py create_household
   ```
6. Create the initial users:
   ```bash
   python manage.py createsuperuser
   ```
   Then create two normal users via the admin or shell.
7. Run the app:
   ```bash
   python manage.py runserver
   ```

## PythonAnywhere deployment

One-time setup:

1. Create a PythonAnywhere account, then open a **Bash console** there.
2. Clone the repo and create a virtual environment inside the project folder:
   ```bash
   git clone https://github.com/jamieclarke323/JazzClubAdminApp.git
   cd JazzClubAdminApp
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root (this stays only on the server; it's git-ignored so `git pull` never touches it):
   ```bash
   DJANGO_SECRET_KEY=<a-long-random-string>
   DEBUG=False
   ALLOWED_HOSTS=<your-username>.pythonanywhere.com
   ```
4. Set up the database and static files:
   ```bash
   python manage.py migrate
   python manage.py create_household
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```
5. Go to the **Web** tab → **Add a new web app** → **Manual configuration** → pick the same Python version as your venv.
   - Set **Source code** to `/home/<your-username>/JazzClubAdminApp`.
   - Set **Virtualenv** to `/home/<your-username>/JazzClubAdminApp/venv`.
   - Edit the **WSGI configuration file** it links to so it points at `jazzclub.wsgi.application` (add the project path to `sys.path` and set `DJANGO_SETTINGS_MODULE=jazzclub.settings`, matching [jazzclub/wsgi.py](jazzclub/wsgi.py)).
   - Under **Static files**, add a mapping: URL `/static/` → Directory `/home/<your-username>/JazzClubAdminApp/staticfiles`.
6. Click **Reload** on the Web tab.

Updating after a change / pull request merge — from a Bash console:
```bash
cd ~/JazzClubAdminApp
git pull
bash deploy.sh
```
Then click **Reload** on the Web tab (or run `touch /var/www/<your-username>_pythonanywhere_com_wsgi.py`) to pick up the change. `deploy.sh` re-installs any new dependencies and runs migrations + `collectstatic` for you.

## Production settings notes

- Secrets and per-environment config (`DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) live in a `.env` file loaded by `python-dotenv` (see [jazzclub/settings.py](jazzclub/settings.py)). `.env` is git-ignored, so it's set once per server and never touched by `git pull`.
- `db.sqlite3`, `staticfiles/`, and `__pycache__/` are git-ignored — they're server-local/build artifacts, not source code, so `git pull` never overwrites production data.
- Static files are served via the PythonAnywhere static files mapping after running `collectstatic`.

## Helpful management commands

```bash
python manage.py createsuperuser
python manage.py create_household
python manage.py test
```
