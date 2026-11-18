import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-before-deployment")
client = MongoClient(os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"), serverSelectionTimeoutMS=3000)
db = client["FixMyCampus"]
complaints = db["complaints"]

CATEGORIES = ["Electrical", "Plumbing", "Cleanliness", "Furniture", "Internet", "Water Supply", "Classroom", "Laboratory", "Other"]
DEPARTMENTS = ["Computer Science", "Information Technology", "Mechanical", "Civil", "Electrical", "Electronics", "Administration", "Housekeeping", "Maintenance"]
STATUSES = ["Pending", "In Progress", "Resolved"]
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please sign in as admin.", "error")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

def stats_for(items):
    return {"total": len(items),
            "pending": sum(x.get("status", "Pending") == "Pending" for x in items),
            "in_progress": sum(x.get("status", "Pending") == "In Progress" for x in items),
            "resolved": sum(x.get("status", "Pending") == "Resolved" for x in items)}

@app.route("/")
def index():
    try:
        items = list(complaints.find({}, {"title":1, "category":1, "department":1, "location":1, "status":1}).sort("_id", -1).limit(100))
        return render_template("index.html", complaints=items, categories=CATEGORIES, departments=DEPARTMENTS)
    except PyMongoError:
        return render_template("error.html", message="MongoDB is not connected. Start MongoDB and try again."), 503

@app.route("/complaints/add", methods=["POST"])
def add_complaint():
    fields = {key: request.form.get(key, "").strip() for key in ["name", "title", "description", "category", "department", "location"]}
    if not all(fields.values()):
        flash("Please fill in every field.", "error")
    elif fields["category"] not in CATEGORIES or fields["department"] not in DEPARTMENTS:
        flash("Choose a valid category and department.", "error")
    else:
        try:
            fields["status"] = "Pending"
            complaints.insert_one(fields)
            flash("Complaint submitted successfully.", "success")
        except PyMongoError:
            flash("Could not save the complaint. Check MongoDB.", "error")
    return redirect(url_for("index"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        if request.form.get("username", "").strip() == ADMIN_USER and request.form.get("password", "") == ADMIN_PASS:
            session.clear()
            session["is_admin"] = True
            session["admin_username"] = ADMIN_USER
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    try:
        items = list(complaints.find().sort("_id", -1))
        return render_template("admin_dashboard.html", complaints=items, categories=CATEGORIES,
                               departments=DEPARTMENTS, statuses=STATUSES, stats=stats_for(items))
    except PyMongoError:
        return render_template("error.html", message="MongoDB is not connected. Start MongoDB and try again."), 503

@app.route("/admin/complaints/add", methods=["POST"])
@admin_required
def admin_add_complaint():
    fields = {key: request.form.get(key, "").strip() for key in ["name", "title", "description", "category", "department", "location"]}
    status = request.form.get("status", "Pending")
    if not all(fields.values()):
        flash("Please fill in every field.", "error")
    elif fields["category"] not in CATEGORIES or fields["department"] not in DEPARTMENTS or status not in STATUSES:
        flash("Choose valid category, department, and status.", "error")
    else:
        try:
            fields["status"] = status
            complaints.insert_one(fields)
            flash("Complaint added.", "success")
        except PyMongoError:
            flash("Could not add complaint.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/complaints/<complaint_id>/status", methods=["POST"])
@admin_required
def admin_update_status(complaint_id):
    status = request.form.get("status", "")
    if not ObjectId.is_valid(complaint_id) or status not in STATUSES:
        flash("Invalid complaint ID or status.", "error")
    else:
        try:
            result = complaints.update_one({"_id": ObjectId(complaint_id)}, {"$set": {"status": status}})
            flash("Status updated." if result.matched_count else "Complaint not found.", "success" if result.matched_count else "error")
        except PyMongoError:
            flash("Could not update status.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/complaints/<complaint_id>/delete", methods=["POST"])
@admin_required
def admin_delete_complaint(complaint_id):
    if not ObjectId.is_valid(complaint_id):
        flash("Invalid complaint ID.", "error")
    else:
        try:
            result = complaints.delete_one({"_id": ObjectId(complaint_id)})
            flash("Complaint deleted." if result.deleted_count else "Complaint not found.", "success" if result.deleted_count else "error")
        except PyMongoError:
            flash("Could not delete complaint.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/health")
def health():
    try:
        client.admin.command("ping")
        return {"status":"ok", "mongodb_connected":True, "database":db.name, "collection":complaints.name}
    except PyMongoError:
        return {"status":"error", "mongodb_connected":False}, 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
