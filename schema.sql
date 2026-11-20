CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    course     TEXT,
    year       INTEGER
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id      TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    department    TEXT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
    service_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    counter      TEXT
);

CREATE TABLE IF NOT EXISTS queue (
    queue_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_number INTEGER NOT NULL,
    student_id   TEXT NOT NULL REFERENCES students(student_id),
    service_id   INTEGER NOT NULL REFERENCES services(service_id),
    date         TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'waiting'
                 CHECK (status IN ('waiting','serving','served','cancelled')),
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (service_id, date, queue_number)
);
