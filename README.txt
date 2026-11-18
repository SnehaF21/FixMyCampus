FixMyCampus updated project
==========================
Student portal: http://127.0.0.1:5000/
Admin login:    http://127.0.0.1:5000/admin/login
Health check:   http://127.0.0.1:5000/health

1. Start MongoDB Community Server, or set MONGO_URI to your Atlas connection string.
2. Open terminal in this folder and run:
   python -m pip install -r requirements.txt
   python app.py
3. Open the URLs above.

Local development admin login:
Username: admin
Password: ChangeMe123!

Before public deployment, change the admin password and FLASK_SECRET_KEY.
Optional environment variables: MONGO_URI, FLASK_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD.
Database: FixMyCampus; collection: complaints.
