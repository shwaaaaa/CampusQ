# Campus Queue Management System

Python (OOP) + Flask + SQLite web system.

## Run (Windows)
Open a terminal INSIDE this folder, then:

    py -m pip install -r requirements.txt
    py create_admin.py      (first time only: creates a staff account + starter services)
    py app.py

Open http://127.0.0.1:5000

## Pages
Staff (login required): /  (Dashboard), /students, /queue, /history
Students (no login):    /register, /get-number, /my-queue?student_id=..., /board

## Files
- app.py            Flask routes
- database.py       Database class (all SQL)
- models.py         Person, Student, Staff classes
- schema.sql        Table definitions (the database design)
- campusq.db        The database itself (created automatically on first run)
- create_admin.py   Creates the first staff account
- test_db.py        Tests the database logic without the website
- templates/        HTML pages
