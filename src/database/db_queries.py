import hashlib
import mysql.connector
from mysql.connector.errors import IntegrityError
from .db import get_connection, fetch_one_dict, fetch_all_dict

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

def add_admin(username: str, password: str, full_name: str, created_by: int = None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO admins (username, password_hash, full_name, created_by) VALUES (%s, %s, %s, %s)",
            (username, hash_password(password), full_name, created_by)
        )
        conn.commit()
        return True
    except IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()

def get_admin_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
    row = fetch_one_dict(cursor)
    cursor.close()
    conn.close()
    return row

def get_all_admins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, created_at FROM admins")
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

def login_admin(username: str, password: str):
    admin = get_admin_by_username(username)
    if admin and verify_password(password, admin['password_hash']):
        return admin
    return None

# ─────────────────────────────────────────────
# SUBJECT QUERIES
# ─────────────────────────────────────────────

def add_subject(course_code: str, course_title: str, program: str, year: str, semester: str, admin_id: int):
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
    """
    Delete a subject and all related data in the correct order.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Delete attendance records linked to sessions of this subject
        cursor.execute("""
            DELETE attendance FROM attendance
            INNER JOIN sessions ON attendance.session_id = sessions.id
            WHERE sessions.subject_id = %s
        """, (subject_id,))
        
        # Step 2: Delete sessions for this subject
        cursor.execute("DELETE FROM sessions WHERE subject_id = %s", (subject_id,))
        
        # Step 3: Delete subject-student enrollments
        cursor.execute("DELETE FROM subject_students WHERE subject_id = %s", (subject_id,))
        
        # Step 4: Finally, delete the subject
        cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
        
        conn.commit()
        print(f"✅ Subject {subject_id} and all related data deleted successfully.")
        return True
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"❌ Database error: {err}")
        return False
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_subjects_by_admin(admin_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects WHERE admin_id = %s", (admin_id,))
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

def get_all_subjects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, a.full_name as admin_name
        FROM subjects s
        JOIN admins a ON s.admin_id = a.id
    """)
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

# ─────────────────────────────────────────────
# STUDENT QUERIES
# ─────────────────────────────────────────────

def add_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester):
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
    except IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()

def remove_student(student_id: int):
    """
    Delete a student and all related data:
    - Attendance records
    - Subject enrollments
    - Face encoding file
    - Student record
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Delete attendance records
        cursor.execute("DELETE FROM attendance WHERE student_id = %s", (student_id,))
        
        # Step 2: Delete subject enrollments
        cursor.execute("DELETE FROM subject_students WHERE student_id = %s", (student_id,))
        
        # Step 3: Delete the student
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        
        conn.commit()
        return True
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"❌ Database error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def assign_roll_numbers(program: str, year: str, semester: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM students
        WHERE program = %s AND year = %s AND semester = %s
        ORDER BY reg_no ASC
    """, (program, year, semester))
    students = fetch_all_dict(cursor)

    for i, student in enumerate(students, start=1):
        cursor.execute("UPDATE students SET roll_no = %s WHERE id = %s", (i, student['id']))

    conn.commit()
    cursor.close()
    conn.close()

def get_students_by_group(program: str, year: str, semester: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM students
        WHERE program = %s AND year = %s AND semester = %s
        ORDER BY reg_no ASC
    """, (program, year, semester))
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM students
        ORDER BY program, year, semester, reg_no ASC
    """)
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

def get_student_by_id(student_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    row = fetch_one_dict(cursor)
    cursor.close()
    conn.close()
    return row

def mark_face_enrolled(student_id: int):
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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO subject_students (subject_id, student_id) VALUES (%s, %s)",
            (subject_id, student_id)
        )
        conn.commit()
        return True
    except IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()

def remove_student_from_subject(subject_id: int, student_id: int):
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*
        FROM students s
        JOIN subject_students ss ON s.id = ss.student_id
        WHERE ss.subject_id = %s
        ORDER BY s.reg_no ASC
    """, (subject_id,))
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

# ─────────────────────────────────────────────
# SESSION QUERIES
# ─────────────────────────────────────────────

def start_session(subject_id: int, admin_id: int, date: str, start_time: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (subject_id, admin_id, date, start_time) VALUES (%s, %s, %s, %s)",
        (subject_id, admin_id, date, start_time)
    )
    session_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return session_id

def end_session(session_id: int, end_time: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET end_time = %s WHERE id = %s", (end_time, session_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_session_by_id(session_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
    row = fetch_one_dict(cursor)
    cursor.close()
    conn.close()
    return row

def get_active_session(subject_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sessions
        WHERE subject_id = %s AND end_time IS NULL
        ORDER BY id DESC LIMIT 1
    """, (subject_id,))
    row = fetch_one_dict(cursor)
    cursor.close()
    conn.close()
    return row

def get_sessions_by_subject(subject_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sessions WHERE subject_id = %s ORDER BY date DESC, start_time DESC",
        (subject_id,)
    )
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

# ─────────────────────────────────────────────
# ATTENDANCE QUERIES
# ─────────────────────────────────────────────

def mark_attendance(session_id: int, student_id: int, status: str, marked_by: str = 'manual'):
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.reg_no, s.roll_no,
               TRIM(CONCAT_WS(' ', s.first_name, s.middle_name, s.last_name)) AS full_name,
               s.first_name, s.middle_name, s.last_name,
               a.status, a.marked_by, a.marked_at
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.session_id = %s
        ORDER BY s.reg_no ASC
    """, (session_id,))
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows

def get_attendance_by_subject(subject_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ss.date, ss.start_time, s.reg_no, s.roll_no,
               TRIM(CONCAT_WS(' ', s.first_name, s.middle_name, s.last_name)) AS full_name,
               s.first_name, s.middle_name, s.last_name,
               a.status, a.marked_by
        FROM attendance a
        JOIN sessions ss ON a.session_id = ss.id
        JOIN students s ON a.student_id = s.id
        WHERE ss.subject_id = %s
        ORDER BY ss.date DESC, s.reg_no ASC
    """, (subject_id,))
    rows = fetch_all_dict(cursor)
    cursor.close()
    conn.close()
    return rows