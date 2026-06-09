import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/attendance.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT UNIQUE NOT NULL,
        last_name TEXT NOT NULL,
        first_name TEXT NOT NULL,
        middle_name TEXT,
        gender TEXT CHECK(gender IN ('Male','Female','Prefer not to say')),
        program TEXT CHECK(program IN ('BBA','BBIS','Transfer')),
        year TEXT CHECK(year IN ('First','Second','Third','Fourth')),
        semester TEXT CHECK(semester IN ('First','Second')),
        face_enrolled INTEGER DEFAULT 0
    )""")

    conn.commit()
    conn.close()
    print("Database ready.")

if __name__ == "__main__":
    init_db()
