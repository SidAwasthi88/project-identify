import sys, os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_queries import *
from recognition.recognize import recognize_student

LATE_THRESHOLD_MINUTES = 15

def begin_session(subject_id, admin_id, username, password):
    if not login_admin(username, password): return None
    now = datetime.now()
    sid = start_session(subject_id, admin_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
    for s in get_students_in_subject(subject_id):
        mark_attendance(sid, s['id'], 'Absent', 'manual')
    return sid

def close_session(sid, username, password):
    if not login_admin(username, password): return False
    end_session(sid, datetime.now().strftime("%H:%M:%S"))
    return True

def determine_status(start_time):
    now = datetime.now()
    start = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M:%S")
    return 'Late' if (now - start).total_seconds()/60 > LATE_THRESHOLD_MINUTES else 'Present'

def process_student_scan(sid, start_time, max_attempts=2):
    sid_stu = None
    for i in range(1, max_attempts+1):
        sid_stu = recognize_student(attempt=i)
        if sid_stu: break
    if sid_stu:
        mark_attendance(sid, sid_stu, determine_status(start_time), 'face')
        return sid_stu
    return None

def manually_mark_student(sid, stu_id, status):
    mark_attendance(sid, stu_id, status, 'manual')