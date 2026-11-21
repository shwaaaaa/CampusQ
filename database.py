"""Database class: hides all SQL so the rest of the app just calls methods."""
import sqlite3
from datetime import date
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash  # comes with Flask

VALID_STATUS = ("waiting", "serving", "served", "cancelled")


class Database:
    def __init__(self, db_path="campusq.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        schema = (Path(__file__).parent / "schema.sql").read_text()
        self._conn.executescript(schema)
        self._conn.commit()
        self._upgrade_old_database()

    def _upgrade_old_database(self):
        """An older campusq.db is missing the new columns, so add them once.
        If the column is already there, SQLite complains and we just move on."""
        try:
            self._conn.execute("ALTER TABLE staff ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
            # the first account ever created becomes the main admin
            self._conn.execute(
                "UPDATE staff SET is_admin=1 WHERE rowid=(SELECT MIN(rowid) FROM staff)"
            )
        except sqlite3.OperationalError:
            pass
        try:
            self._conn.execute("ALTER TABLE services ADD COLUMN department TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            self._conn.execute("ALTER TABLE services ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        self._conn.commit()

    @staticmethod
    def _today():
        return date.today().isoformat()

    def close(self):
        self._conn.close()

    # ---------------- Students ----------------
    def add_student(self, student_id, name, course, year):
        try:
            self._conn.execute(
                "INSERT INTO students (student_id, name, course, year) VALUES (?,?,?,?)",
                (student_id, name, course, year),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Student ID {student_id} already exists.")

    def get_students(self):
        return self._conn.execute("SELECT * FROM students ORDER BY name").fetchall()

    def get_student(self, student_id):
        return self._conn.execute(
            "SELECT * FROM students WHERE student_id=?", (student_id,)
        ).fetchone()

    def search_students(self, keyword):
        like = f"%{keyword}%"
        return self._conn.execute(
            "SELECT * FROM students WHERE student_id LIKE ? OR name LIKE ? ORDER BY name",
            (like, like),
        ).fetchall()

    def update_student(self, student_id, name, course, year):
        self._conn.execute(
            "UPDATE students SET name=?, course=?, year=? WHERE student_id=?",
            (name, course, year, student_id),
        )
        self._conn.commit()

    def delete_student(self, student_id):
        try:
            self._conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Cannot delete: this student has queue records.")

    # ---------------- Staff / Login ----------------
    def add_staff(self, staff_id, name, department, username, password, is_admin=False):
        try:
            self._conn.execute(
                "INSERT INTO staff (staff_id, name, department, username, password_hash, is_admin) "
                "VALUES (?,?,?,?,?,?)",
                (staff_id, name, department, username,
                 generate_password_hash(password), int(is_admin)),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Staff ID or username already exists.")

    def get_staff(self):
        return self._conn.execute(
            "SELECT staff_id, name, department, username, is_admin FROM staff "
            "ORDER BY is_admin DESC, name"
        ).fetchall()

    def verify_login(self, username, password):
        """Returns the staff row if the login is correct, otherwise None."""
        row = self._conn.execute(
            "SELECT * FROM staff WHERE username=?", (username,)
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            return row
        return None

    def get_departments(self):
        """Department names already used, for the suggestion lists."""
        rows = self._conn.execute(
            "SELECT department FROM staff UNION SELECT department FROM services "
            "ORDER BY department"
        ).fetchall()
        return [r["department"] for r in rows if r["department"]]

    # ---------------- Services ----------------
    def add_service(self, service_name, counter, department):
        cur = self._conn.execute(
            "INSERT INTO services (service_name, counter, department) VALUES (?,?,?)",
            (service_name, counter, department),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_service(self, service_id):
        return self._conn.execute(
            "SELECT * FROM services WHERE service_id=?", (service_id,)
        ).fetchone()

    def get_services(self, department=None, include_archived=False):
        """Leave department empty (None) to get every department's services.
        Archived services are left out unless include_archived is True."""
        sql = "SELECT * FROM services WHERE 1=1"
        params = []
        if not include_archived:
            sql += " AND archived=0"
        if department is not None:
            sql += " AND LOWER(department)=LOWER(?)"
            params.append(department)
        sql += " ORDER BY service_name"
        return self._conn.execute(sql, params).fetchall()

    def update_service(self, service_id, service_name, counter, department):
        self._conn.execute(
            "UPDATE services SET service_name=?, counter=?, department=? WHERE service_id=?",
            (service_name, counter, department, service_id),
        )
        self._conn.commit()

    def set_service_archived(self, service_id, archived):
        """Archiving hides a service but keeps its queue history."""
        self._conn.execute(
            "UPDATE services SET archived=? WHERE service_id=?",
            (int(archived), service_id),
        )
        self._conn.commit()

    # ---------------- Queue ----------------
    def add_queue(self, student_id, service_id):
        """Gives the student the next queue number for that service today."""
        service = self.get_service(service_id)
        if service is None or service["archived"]:
            raise ValueError("That service is not available.")

        today = self._today()
        already = self._conn.execute(
            "SELECT 1 FROM queue WHERE student_id=? AND service_id=? AND date=? "
            "AND status IN ('waiting','serving')",
            (student_id, service_id, today),
        ).fetchone()
        if already:
            raise ValueError("Student is already in this queue.")

        number = self._conn.execute(
            "SELECT COALESCE(MAX(queue_number), 0) + 1 FROM queue "
            "WHERE service_id=? AND date=?",
            (service_id, today),
        ).fetchone()[0]

        try:
            cur = self._conn.execute(
                "INSERT INTO queue (queue_number, student_id, service_id, date) VALUES (?,?,?,?)",
                (number, student_id, service_id, today),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Student or service does not exist.")
        return {"queue_id": cur.lastrowid, "queue_number": number}

    _QUEUE_SELECT = (
        "SELECT q.queue_id, q.queue_number, q.status, q.date, q.created_at, "
        "s.student_id, s.name AS student_name, sv.service_id, sv.service_name, sv.counter "
        "FROM queue q "
        "JOIN students s ON s.student_id = q.student_id "
        "JOIN services sv ON sv.service_id = q.service_id "
    )

    def get_queue_entry(self, queue_id):
        return self._conn.execute(
            self._QUEUE_SELECT + "WHERE q.queue_id=?", (queue_id,)
        ).fetchone()

    def get_queue(self, service_id=None, status=None, on_date=None):
        sql = self._QUEUE_SELECT + "WHERE q.date=?"
        params = [on_date or self._today()]
        if service_id is not None:
            sql += " AND q.service_id=?"
            params.append(service_id)
        if status is not None:
            sql += " AND q.status=?"
            params.append(status)
        sql += " ORDER BY q.queue_number"
        return self._conn.execute(sql, params).fetchall()

    def call_next(self, service_id):
        """Finishes the student being served, then calls the next waiting one.
        Returns the newly called row, or None if nobody is waiting."""
        today = self._today()
        self._conn.execute(
            "UPDATE queue SET status='served' "
            "WHERE service_id=? AND date=? AND status='serving'",
            (service_id, today),
        )
        nxt = self._conn.execute(
            "SELECT queue_id FROM queue WHERE service_id=? AND date=? AND status='waiting' "
            "ORDER BY queue_number LIMIT 1",
            (service_id, today),
        ).fetchone()
        if nxt is None:
            self._conn.commit()
            return None
        self._conn.execute(
            "UPDATE queue SET status='serving' WHERE queue_id=?", (nxt["queue_id"],)
        )
        self._conn.commit()
        return self.get_queue_entry(nxt["queue_id"])

    def update_status(self, queue_id, status):
        if status not in VALID_STATUS:
            raise ValueError(f"Status must be one of {VALID_STATUS}")
        self._conn.execute("UPDATE queue SET status=? WHERE queue_id=?", (status, queue_id))
        self._conn.commit()

    def get_position(self, queue_id):
        """How many students are ahead of this one (0 = you're next/being served)."""
        entry = self.get_queue_entry(queue_id)
        if entry is None or entry["status"] != "waiting":
            return 0
        return self._conn.execute(
            "SELECT COUNT(*) FROM queue WHERE service_id=? AND date=? "
            "AND status='waiting' AND queue_number < ?",
            (entry["service_id"], entry["date"], entry["queue_number"]),
        ).fetchone()[0]

    def get_history(self, department=None):
        """Leave department empty (None) to get every department's history."""
        sql = self._QUEUE_SELECT + "WHERE q.status='served'"
        params = []
        if department is not None:
            sql += " AND LOWER(sv.department)=LOWER(?)"
            params.append(department)
        sql += " ORDER BY q.date DESC, q.queue_number DESC"
        return self._conn.execute(sql, params).fetchall()