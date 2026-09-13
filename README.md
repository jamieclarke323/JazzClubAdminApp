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

1. Create a PythonAnywhere account and a new web app using Manual Configuration.
2. In the Bash console, create a virtual environment and install dependencies:
   ```bash
   mkvirtualenv --python=/usr/local/bin/python3.11 jazzclub
   pip install -r /home/<your-user>/<your-project>/requirements.txt
   ```
3. Configure PostgreSQL and set environment variables in the web app configuration:
   ```bash
   DJANGO_SECRET_KEY=...
   DEBUG=False
   ALLOWED_HOSTS=<your-pythonanywhere-domain>,<your-username>.pythonanywhere.com
   USE_POSTGRES=true
   DB_NAME=...
   DB_USER=...
   DB_PASSWORD=...
   DB_HOST=...
   DB_PORT=5432
   ```
4. Run migrations on the server:
   ```bash
   python manage.py migrate
   python manage.py create_household
   ```
5. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```
6. Configure the WSGI file to point to `jazzclub.wsgi.application`.
7. Add scheduled tasks for recurring job processing if needed.

## Production settings notes

- Store secrets in environment variables.
- Keep Google OAuth credentials and AI keys outside source control.
- Use SQLite locally and PostgreSQL on PythonAnywhere.
- Static files should be served via the web app collector.

## Helpful management commands

```bash
python manage.py createsuperuser
python manage.py create_household
python manage.py test
```
