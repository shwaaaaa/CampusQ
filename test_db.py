"""Run this first:  python test_db.py   (no web pages needed)"""
import os

from database import Database
from models import Staff, Student

if os.path.exists("test_campusq.db"):
    os.remove("test_campusq.db")

db = Database("test_campusq.db")

# Setup data
registrar = db.add_service("Registrar", "Window 1")
cashier = db.add_service("Cashier", "Window 2")
db.add_student("2024-0001", "Juan Dela Cruz", "BSIT", 2)
db.add_student("2024-0002", "Maria Santos", "BSIT", 2)
db.add_student("2024-0003", "Pedro Reyes", "BSED", 3)
db.add_staff("S-001", "Ana Cruz", "Registrar", "ana", "secret123")

# Login
print("Login ok:   ", db.verify_login("ana", "secret123") is not None)
print("Login wrong:", db.verify_login("ana", "wrong") is None)

# Queue numbers
for sid in ("2024-0001", "2024-0002", "2024-0003"):
    r = db.add_queue(sid, registrar)
    print(f"{sid} got Registrar #{r['queue_number']}")
print("Cashier #", db.add_queue("2024-0001", cashier)["queue_number"], "(numbers are per service)")

# Duplicate check
try:
    db.add_queue("2024-0001", registrar)
except ValueError as e:
    print("Duplicate blocked:", e)

# Call next x4
for i in range(4):
    nxt = db.call_next(registrar)
    if nxt:
        print(f"Now serving #{nxt['queue_number']} - {nxt['student_name']} at {nxt['counter']}")
    else:
        print("Queue is empty.")

# Position check
ids = [r["queue_id"] for r in db.get_queue(cashier)]
print("Cashier position of first student:", db.get_position(ids[0]))
print("Served history:", [(r["queue_number"], r["student_name"]) for r in db.get_history()])

# Can't delete a student with queue records
try:
    db.delete_student("2024-0001")
except ValueError as e:
    print("Delete blocked:", e)

# OOP demo
print(Student("2024-0001", "Juan Dela Cruz", "BSIT", 2).show_info())
print(Staff("S-001", "Ana Cruz", "Registrar").show_info())

db.close()
os.remove("test_campusq.db")
