import hashlib
from .db import get_connection

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()

def add_admin(username, password, full_name):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO admins (username, password_hash, full_name) VALUES (?,?,?)",
                     (username, hash_password(password), full_name))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login_admin(username, password):
    conn = get_connection()
    row = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row and dict(row)['password_hash'] == hash_password(password):
        return dict(row)
    return None

def add_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO students (reg_no, last_name, first_name, middle_name, gender, program, year, semester) VALUES (?,?,?,?,?,?,?,?)",
                     (reg_no, last_name, first_name, middle_name, gender, program, year, semester))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_all_students():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY reg_no").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_student_by_id(sid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def mark_face_enrolled(sid):
    conn = get_connection()
    conn.execute("UPDATE students SET face_enrolled = 1 WHERE id = ?", (sid,))
    conn.commit()
    conn.close()