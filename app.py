from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from database import VALID_STATUS, Database

app = Flask(__name__)
app.secret_key = "change-this-to-any-random-text"   # needed for login sessions
db = Database("campusq.db")


def login_required(view):
    """Only logged-in staff can open pages that use this."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "staff_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------- Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        staff = db.verify_login(request.form["username"].strip(), request.form["password"])
        if staff:
            session["staff_id"] = staff["staff_id"]
            session["staff_name"] = staff["name"]
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------ Dashboard
@app.route("/")
@login_required
def dashboard():
    waiting = len(db.get_queue(status="waiting"))
    serving = len(db.get_queue(status="serving"))
    served = len(db.get_queue(status="served"))

    services = []
    for s in db.get_services():
        current = db.get_queue(service_id=s["service_id"], status="serving")
        waiting_here = len(db.get_queue(service_id=s["service_id"], status="waiting"))
        services.append({"info": s,
                         "current": current[0] if current else None,
                         "waiting": waiting_here})

    return render_template("dashboard.html", waiting=waiting, serving=serving,
                           served=served, services=services)


# ------------------------------------------------------------- Students
def _read_student_form():
    student_id = request.form["student_id"].strip()
    name = request.form["name"].strip()
    course = request.form["course"].strip()
    try:
        year = int(request.form.get("year", ""))
    except ValueError:
        year = None
    return student_id, name, course, year


@app.route("/students")
@login_required
def students():
    q = request.args.get("q", "").strip()
    rows = db.search_students(q) if q else db.get_students()
    return render_template("students.html", students=rows, q=q)


@app.route("/students/add", methods=["POST"])
@login_required
def student_add():
    student_id, name, course, year = _read_student_form()
    if not student_id or not name:
        flash("Student ID and name are required.", "danger")
    else:
        try:
            db.add_student(student_id, name, course, year)
            flash(f"Student {name} added.", "success")
        except ValueError as e:
            flash(str(e), "danger")
    return redirect(url_for("students"))


@app.route("/students/update", methods=["POST"])
@login_required
def student_update():
    student_id, name, course, year = _read_student_form()
    if not student_id or not name:
        flash("Click a student in the table first, then edit the details.", "danger")
    else:
        db.update_student(student_id, name, course, year)
        flash(f"Student {name} updated.", "success")
    return redirect(url_for("students"))


@app.route("/students/delete", methods=["POST"])
@login_required
def student_delete():
    student_id = request.form["student_id"].strip()
    if not student_id:
        flash("Click a student in the table first.", "danger")
    else:
        try:
            db.delete_student(student_id)
            flash("Student deleted.", "success")
        except ValueError as e:
            flash(str(e), "danger")
    return redirect(url_for("students"))


# ---------------------------------------------------------------- Queue
@app.route("/queue")
@login_required
def queue():
    services = db.get_services()
    selected = request.args.get("service", type=int)
    if selected is None and services:
        selected = services[0]["service_id"]

    entries = db.get_queue(service_id=selected) if selected else []
    current = next((e for e in entries if e["status"] == "serving"), None)
    return render_template("queue.html", services=services, selected=selected,
                           entries=entries, current=current,
                           students=db.get_students(), statuses=VALID_STATUS)


@app.route("/queue/add", methods=["POST"])
@login_required
def queue_add():
    student_id = request.form["student_id"].strip()
    service_id = int(request.form["service_id"])
    try:
        result = db.add_queue(student_id, service_id)
        flash(f"Queue number #{result['queue_number']} assigned.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("queue", service=service_id))


@app.route("/queue/call-next/<int:service_id>", methods=["POST"])
@login_required
def queue_call_next(service_id):
    called = db.call_next(service_id)
    if called:
        flash(f"Now serving #{called['queue_number']} - {called['student_name']}.", "success")
    else:
        flash("No more students waiting.", "info")
    return redirect(url_for("queue", service=service_id))


@app.route("/queue/<int:queue_id>/status", methods=["POST"])
@login_required
def queue_status(queue_id):
    service_id = request.form["service_id"]
    try:
        db.update_status(queue_id, request.form["status"])
        flash("Status updated.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("queue", service=service_id))


# -------------------------------------------------------------- History
@app.route("/history")
@login_required
def history():
    return render_template("history.html", rows=db.get_history())


# ------------------------------------- Student pages (no login needed)
@app.route("/get-number", methods=["GET", "POST"])
def get_number():
    services = db.get_services()
    if request.method == "POST":
        student_id = request.form["student_id"].strip()
        service_id = request.form.get("service_id", type=int)
        if not db.get_student(student_id):
            flash("Student ID not found. Please register first using the link below.", "danger")
        else:
            try:
                result = db.add_queue(student_id, service_id)
                flash(f"Your queue number is #{result['queue_number']}.", "success")
            except ValueError as e:
                flash(str(e), "warning")
            return redirect(url_for("my_queue", student_id=student_id))
    return render_template("get_number.html", services=services)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_id, name, course, year = _read_student_form()
        if not student_id or not name:
            flash("Student ID and name are required.", "danger")
        else:
            try:
                db.add_student(student_id, name, course, year)
                flash(f"Registered! You can now get a queue number, {name}.", "success")
                return redirect(url_for("get_number"))
            except ValueError as e:
                flash(str(e), "warning")
    return render_template("register.html")


@app.route("/my-queue")
def my_queue():
    student_id = request.args.get("student_id", "").strip()
    student = db.get_student(student_id) if student_id else None
    if not student:
        flash("Student ID not found.", "danger")
        return redirect(url_for("get_number"))

    tickets = []
    for entry in db.get_queue():
        if entry["student_id"] == student_id:
            tickets.append({"entry": entry, "ahead": db.get_position(entry["queue_id"])})
    return render_template("my_queue.html", student=student, tickets=tickets)


@app.route("/board")
def board():
    data = []
    for s in db.get_services():
        current = db.get_queue(service_id=s["service_id"], status="serving")
        waiting = db.get_queue(service_id=s["service_id"], status="waiting")
        data.append({"info": s,
                     "current": current[0] if current else None,
                     "next": [w["queue_number"] for w in waiting[:3]],
                     "waiting": len(waiting)})
    return render_template("board.html", services=data)


if __name__ == "__main__":
    app.run(debug=True)
