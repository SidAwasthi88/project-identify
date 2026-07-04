import sys
import os
from datetime import datetime

# Ensure the src directory is in the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_queries import (
    start_session, end_session, mark_attendance, 
    get_students_in_subject, get_attendance_for_session, login_admin
)
from recognition.recognize import recognize_student

LATE_THRESHOLD_MINUTES = 15

def begin_session(subject_id: int, admin_id: int, admin_username: str, password: str):
    """Verifies teacher password, initializes session, and presets everyone as Absent."""
    admin = login_admin(admin_username, password)
    if not admin:
        return None
        
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    session_id = start_session(subject_id, admin_id, date_str, time_str)
    
    # Pre-mark everyone as Absent initially
    students = get_students_in_subject(subject_id)
    for student in students:
        mark_attendance(session_id, student['id'], 'Absent', 'manual')
        
    return session_id

def close_session(session_id: int, admin_username: str, password: str):
    """Verifies credentials and closes the active session window."""
    admin = login_admin(admin_username, password)
    if not admin:
        return False
        
    time_str = datetime.now().strftime("%H:%M:%S")
    end_session(session_id, time_str)
    return True

def determine_status(session_start_time: str) -> str:
    """Calculates if the student arrived within the allowed on-time threshold."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    start_dt = datetime.strptime(f"{today} {session_start_time}", "%Y-%m-%d %H:%M:%S")
    diff = (now - start_dt).total_seconds() / 60
    return 'Late' if diff > LATE_THRESHOLD_MINUTES else 'Present'

def process_student_scan(session_id: int, session_start_time: str, max_attempts: int = 2):
    """Flashes camera framework to match a dynamic biometric input against pickled records."""
    student_id = None
    for attempt in range(1, max_attempts + 1):
        student_id = recognize_student(attempt=attempt)
        if student_id:
            break
            
    if student_id:
        status = determine_status(session_start_time)
        mark_attendance(session_id, student_id, status, marked_by='face')
        return student_id
    return None

def manually_mark_student(session_id: int, student_id: int, status: str):
    """Allows manual admin override to adjust student status."""
    mark_attendance(session_id, student_id, status, marked_by='manual')

def get_session_attendance(session_id: int):
    return get_attendance_for_session(session_id)