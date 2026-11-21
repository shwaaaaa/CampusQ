"""Run once to create the main admin account:  py create_admin.py

After that, run the app, log in, and use the Services and Staff pages to set up
each department's services and staff accounts."""
from getpass import getpass

from database import Database

db = Database("campusq.db")

name = input("Full name: ")
department = input("Department (e.g. Administration): ")
username = input("Username: ")
password = getpass("Password: ")

try:
    db.add_staff("S-" + username, name, department, username, password, is_admin=True)
    print("Main admin account created. You can now run:  py app.py")
    print("Then log in and add your services and staff accounts from the navbar.")
except ValueError as e:
    print("Error:", e)
