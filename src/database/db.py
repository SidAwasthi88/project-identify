import sqlite3
import os

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/attendance.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access to rows
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Creates all tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- ADMINS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES admins(id)
        )
    """)

    # --- SUBJECTS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            course_title TEXT NOT NULL,
            program TEXT NOT NULL CHECK(program IN ('BBA', 'BBIS')),
            year TEXT NOT NULL CHECK(year IN ('First', 'Second', 'Third', 'Fourth')),
            semester TEXT NOT NULL CHECK(semester IN ('First', 'Second')),
            admin_id INTEGER NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
    """)

    # --- STUDENTS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT UNIQUE NOT NULL,
            roll_no INTEGER,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            gender TEXT CHECK(gender IN ('Male', 'Female', 'Prefer not to say')),
            program TEXT NOT NULL CHECK(program IN ('BBA', 'BBIS', 'Transfer')),
            year TEXT CHECK(year IN ('First', 'Second', 'Third', 'Fourth')),
            semester TEXT CHECK(semester IN ('First', 'Second')),
            face_enrolled INTEGER DEFAULT 0,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- SUBJECT-STUDENT ENROLLMENT TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(subject_id, student_id)
        )
    """)

    # --- SESSIONS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
    """)

    # --- ATTENDANCE TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late')),
            marked_by TEXT DEFAULT 'manual' CHECK(marked_by IN ('face', 'manual')),
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(session_id, student_id)
        )
    """)

    # Seed an initial default admin account if none exists
    row = cursor.execute("SELECT COUNT(*) as count FROM admins").fetchone()
    if row['count'] == 0:
        # Password hash for 'admin123'
        import hashlib
        default_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO admins (username, password_hash, full_name, created_by)
            VALUES (?, ?, ?, ?)
        """, ('admin', default_hash, 'System Administrator', None))

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")

if __name__ == "__main__":
    init_db()