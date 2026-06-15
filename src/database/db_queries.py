"""
db_queries.py — All database read/write functions using MySQL
Every module imports from here. Nobody writes raw SQL outside this file.

Key MySQL differences from SQLite:
- Use cursor = conn.cursor(dictionary=True) to get dict-like rows
- Use %s as placeholder instead of ?
- Always close cursor AND connection
"""

import hashlib
from .db import get_connection


# ─────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Returns True if the password matches the stored hash."""
    return hash_password(password) == hashed


# ─────────────────────────────────────────────
# ADMIN QUERIES
# ─────────────────────────────────────────────

def add_admin(username: str, password: str, full_name: str, created_by=None):
    """Adds a new admin. Returns True on success, False if username taken."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO admins (username, password_hash, full_name, created_by) VALUES (%s, %s, %s, %s)",
            (username, hash_password(password), full_name, created_by)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cursor.close()
        conn.close()


def get_admin_by_username(username: str):
    """Returns admin row as dict by username, or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_all_admins():
    """Returns list of all admins."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, full_name, created_at FROM admins")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def login_admin(username: str, password: str):
    """Returns admin dict if credentials are valid, else None."""
    admin = get_admin_by_username(username)
    if admin and verify_password(password, admin['password_hash']):
        return admin
    return None


# ─────────────────────────────────────────────
# SUBJECT QUERIES
# ─────────────────────────────────────────────

def add_subject(course_code: str, course_title: str, program: str, year: str, semester: str, admin_id: int):
    """Adds a new subject."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subjects (course_code, course_title, program, year, semester, admin_id) VALUES (%s, %s, %s, %s, %s, %s)",
        (course_code, course_title, program, year, semester, admin_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def remove_subject(subject_id: int):
    """Deletes a subject by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
    conn.commit()
    cursor.close()
    conn.close()


def get_subjects_by_admin(admin_id: int):
    """Returns all subjects taught by a given admin."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE admin_id = %s", (admin_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_all_subjects():
    """Returns all subjects with admin name."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, a.full_name as admin_name
        FROM subjects s
        JOIN admins a ON s.admin_id = a.id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ─────────────────────────────────────────────
# STUDENT QUERIES
# ─────────────────────────────────────────────

def add_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester):
    """Adds a new student. Returns True on success, False if reg_no exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (reg_no, last_name, first_name, middle_name, gender, program, year, semester)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (reg_no, last_name, first_name, middle_name, gender, program, year, semester))
        conn.commit()
        assign_roll_numbers(program, year, semester)
        return True
    except Exception:
        return False
    finally:
        cursor.close()
        conn.close()


def remove_student(student_id: int):
    """Removes a student by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()


def assign_roll_numbers(program: str, year: str, semester: str):
    """
    Auto-assigns roll numbers to students in a group
    sorted by reg_no ascending. Roll numbers start from 1.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id FROM students
        WHERE program = %s AND year = %s AND semester = %s
        ORDER BY reg_no ASC
    """, (program, year, semester))
    students = cursor.fetchall()

    update_cursor = conn.cursor()
    for i, student in enumerate(students, start=1):
        update_cursor.execute("UPDATE students SET roll_no = %s WHERE id = %s", (i, student['id']))

    conn.commit()
    cursor.close()
    update_cursor.close()
    conn.close()


def get_all_students():
    """Returns all students ordered by program, year, semester, reg_no."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students ORDER BY program, year, semester, reg_no ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_student_by_id(student_id: int):
    """Returns a single student by ID."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_student_by_reg(reg_no: str):
    """Returns a student by registration number."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE reg_no = %s", (reg_no,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_students_by_group(program: str, year: str, semester: str):
    """Returns all students in a program/year/semester group."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM students
        WHERE program = %s AND year = %s AND semester = %s
        ORDER BY reg_no ASC
    """, (program, year, semester))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def mark_face_enrolled(student_id: int):
    """Marks a student as having their face enrolled."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET face_enrolled = 1 WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ─────────────────────────────────────────────
# SUBJECT-STUDENT ENROLLMENT
# ─────────────────────────────────────────────

def enroll_student_in_subject(subject_id: int, student_id: int):
    """Links a student to a subject."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO subject_students (subject_id, student_id) VALUES (%s, %s)",
            (subject_id, student_id)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cursor.close()
        conn.close()


def remove_student_from_subject(subject_id: int, student_id: int):
    """Removes a student from a subject."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM subject_students WHERE subject_id = %s AND student_id = %s",
        (subject_id, student_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_students_in_subject(subject_id: int):
    """Returns all students enrolled in a subject."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*
        FROM students s
        JOIN subject_students ss ON s.id = ss.student_id
        WHERE ss.subject_id = %s
        ORDER BY s.reg_no ASC
    """, (subject_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ─────────────────────────────────────────────
# SESSION QUERIES
# ─────────────────────────────────────────────

def start_session(subject_id: int, admin_id: int, date: str, start_time: str):
    """Creates a new session and returns its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (subject_id, admin_id, date, start_time) VALUES (%s, %s, %s, %s)",
        (subject_id, admin_id, date, start_time)
    )
    conn.commit()
    session_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return session_id


def end_session(session_id: int, end_time: str):
    """Sets the end time of a session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET end_time = %s WHERE id = %s", (end_time, session_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_sessions_by_subject(subject_id: int):
    """Returns all sessions for a subject."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM sessions WHERE subject_id = %s ORDER BY date DESC, start_time DESC",
        (subject_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ─────────────────────────────────────────────
# ATTENDANCE QUERIES
# ─────────────────────────────────────────────

def mark_attendance(session_id: int, student_id: int, status: str, marked_by: str = 'manual'):
    """
    Marks or updates attendance for a student in a session.
    Uses INSERT ... ON DUPLICATE KEY UPDATE to handle overwrites.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attendance (session_id, student_id, status, marked_by)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE status = VALUES(status), marked_by = VALUES(marked_by)
    """, (session_id, student_id, status, marked_by))
    conn.commit()
    cursor.close()
    conn.close()


def get_attendance_for_session(session_id: int):
    """Returns full attendance list for a session with student details."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            s.reg_no,
            s.roll_no,
            CONCAT(s.last_name, ' ', s.first_name, ' ', COALESCE(s.middle_name, '')) AS full_name,
            a.status,
            a.marked_by,
            a.marked_at
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.session_id = %s
        ORDER BY s.reg_no ASC
    """, (session_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_attendance_by_subject(subject_id: int):
    """Returns all attendance records for a subject across all sessions."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            ss.date,
            ss.start_time,
            s.reg_no,
            s.roll_no,
            CONCAT(s.last_name, ' ', s.first_name, ' ', COALESCE(s.middle_name, '')) AS full_name,
            a.status,
            a.marked_by
        FROM attendance a
        JOIN sessions ss ON a.session_id = ss.id
        JOIN students s ON a.student_id = s.id
        WHERE ss.subject_id = %s
        ORDER BY ss.date DESC, s.reg_no ASC
    """, (subject_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows