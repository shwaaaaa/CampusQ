"""Run once to create the first staff account:  python create_admin.py"""
from getpass import getpass

from database import Database

db = Database("campusq.db")

name = input("Full name: ")
department = input("Department (e.g. Registrar): ")
username = input("Username: ")
password = getpass("Password: ")

try:
    db.add_staff("S-" + username, name, department, username, password)
    print("Staff account created. You can now run:  python app.py")
except ValueError as e:
    print("Error:", e)

# Optional: add some starting services if there are none yet
if not db.get_services():
    for service, counter in [("Registrar", "Window 1"), ("Cashier", "Window 2"),
                             ("Library", "Desk 3"), ("Clinic", "Room 4")]:
        db.add_service(service, counter)
    print("Added starter services: Registrar, Cashier, Library, Clinic")
