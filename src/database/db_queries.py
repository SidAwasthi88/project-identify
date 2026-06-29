import hashlib
from .db import get_connection

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def verify_password(p, h):
    return hash_password(p) == h

def add_admin(u, p, n, cb=None):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO admins (username, password_hash, full_name, created_by) VALUES (%s,%s,%s,%s)",
                  (u, hash_password(p), n, cb))
        conn.commit(); return True
    except: return False
    finally: c.close(); conn.close()

def login_admin(u, p):
    conn = get_connection(); c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM admins WHERE username=%s", (u,))
    r = c.fetchone(); c.close(); conn.close()
    return r if r and verify_password(p, r['password_hash']) else None

def add_subject(code, title, prog, yr, sem, aid):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO subjects (course_code, course_title, program, year, semester, admin_id) VALUES (%s,%s,%s,%s,%s,%s)",
              (code, title, prog, yr, sem, aid))
    conn.commit(); c.close(); conn.close()

def get_subjects_by_admin(aid):
    conn = get_connection(); c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM subjects WHERE admin_id=%s", (aid,))
    r = c.fetchall(); c.close(); conn.close()
    return r

def add_student(reg, ln, fn, mn, g, prog, yr, sem):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO students (reg_no, last_name, first_name, middle_name, gender, program, year, semester) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                  (reg, ln, fn, mn, g, prog, yr, sem))
        conn.commit()
        c2 = conn.cursor(dictionary=True)
        c2.execute("SELECT id FROM students WHERE program=%s AND year=%s AND semester=%s ORDER BY reg_no", (prog, yr, sem))
        for i, s in enumerate(c2.fetchall(), 1):
            c.execute("UPDATE students SET roll_no=%s WHERE id=%s", (i, s['id']))
        conn.commit(); c2.close()
        return True
    except: return False
    finally: c.close(); conn.close()

def get_all_students():
    conn = get_connection(); c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM students ORDER BY reg_no ASC")
    r = c.fetchall(); c.close(); conn.close()
    return r

def get_student_by_id(sid):
    conn = get_connection(); c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM students WHERE id=%s", (sid,))
    r = c.fetchone(); c.close(); conn.close()
    return r

def mark_face_enrolled(sid):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE students SET face_enrolled=1 WHERE id=%s", (sid,))
    conn.commit(); c.close(); conn.close()

def enroll_student_in_subject(sub_id, stu_id):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO subject_students (subject_id, student_id) VALUES (%s,%s)", (sub_id, stu_id))
        conn.commit(); return True
    except: return False
    finally: c.close(); conn.close()

def get_students_in_subject(sub_id):
    conn = get_connection(); c = conn.cursor(dictionary=True)
    c.execute("SELECT s.* FROM students s JOIN subject_students ss ON s.id=ss.student_id WHERE ss.subject_id=%s ORDER BY s.reg_no", (sub_id,))
    r = c.fetchall(); c.close(); conn.close()
    return r

def start_session(sub_id, aid, date, time):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO sessions (subject_id, admin_id, date, start_time) VALUES (%s,%s,%s,%s)", (sub_id, aid, date, time))
    conn.commit(); sid = c.lastrowid; c.close(); conn.close()
    return sid

def end_session(sid, time):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE sessions SET end_time=%s WHERE id=%s", (time, sid))
    conn.commit(); c.close(); conn.close()

def mark_attendance(session_id, student_id, status, marked_by='manual'):
    conn = get_connection(); c = conn.cursor()
    c.execute("""INSERT INTO attendance (session_id, student_id, status, marked_by) VALUES (%s,%s,%s,%s)
                 ON DUPLICATE KEY UPDATE status=VALUES(status), marked_by=VALUES(marked_by)""",
              (session_id, student_id, status, marked_by))
    conn.commit(); c.close(); conn.close()

def get_attendance_for_session(sid):
    conn = get_connection(); c = conn.cursor(dictionary=True)
    c.execute("""SELECT s.reg_no, s.roll_no, CONCAT(s.last_name,' ',s.first_name,' ',COALESCE(s.middle_name,'')) AS full_name,
                 a.status, a.marked_by, a.marked_at FROM attendance a
                 JOIN students s ON a.student_id=s.id WHERE a.session_id=%s ORDER BY s.reg_no""", (sid,))
    r = c.fetchall(); c.close(); conn.close()
    return r

def get_attendance_by_subject(sub_id):
    conn = get_connection(); c = conn.cursor(dictionary=True)
    c.execute("""SELECT ss.date, ss.start_time, s.reg_no, s.roll_no,
                 CONCAT(s.last_name,' ',s.first_name,' ',COALESCE(s.middle_name,'')) AS full_name,
                 a.status, a.marked_by FROM attendance a
                 JOIN sessions ss ON a.session_id=ss.id
                 JOIN students s ON a.student_id=s.id
                 WHERE ss.subject_id=%s ORDER BY ss.date DESC, s.reg_no""", (sub_id,))
    r = c.fetchall(); c.close(); conn.close()
    return r