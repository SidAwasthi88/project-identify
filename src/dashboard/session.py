import sys
import os
from datetime import datetime
import pickle
import streamlit as st

# Ensure the src directory is in the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_queries import (
    start_session, end_session, mark_attendance, 
    get_students_in_subject, get_attendance_for_session, login_admin,
    get_session_by_id
)

LATE_THRESHOLD_MINUTES = 15

# ─────────────────────────────────────────────
# HELPER: Load Face Encodings
# ─────────────────────────────────────────────
def load_face_encodings(student_id: int):
    encodings_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'encodings')
    filepath = os.path.join(encodings_dir, f"{student_id}.pkl")
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return pickle.load(f)


# ─────────────────────────────────────────────
# SESSION MANAGEMENT
# ─────────────────────────────────────────────
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
    if students:
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
    
    if isinstance(session_start_time, str):
        time_parts = session_start_time.split(':')
        if len(time_parts) == 2:
            session_start_time = f"{session_start_time}:00"
        start_dt = datetime.strptime(f"{today} {session_start_time}", "%Y-%m-%d %H:%M:%S")
    else:
        start_dt = session_start_time

    diff = (now - start_dt).total_seconds() / 60.0
    return 'Late' if diff > LATE_THRESHOLD_MINUTES else 'Present'


# ─────────────────────────────────────────────
# LIVE ATTENDANCE SCANNER (Inside Streamlit)
# ─────────────────────────────────────────────
def process_student_scan(session_id: int, session_start_time: str):
    """
    Uses streamlit-webrtc to show camera inside Streamlit and mark attendance.
    """
    # --- HEAVY IMPORTS MOVED INSIDE ---
    import cv2
    import face_recognition
    from streamlit_webrtc import webrtc_streamer
    import av
    from database.db_queries import get_students_in_subject, mark_attendance, get_session_by_id
    from enrollment.enroll_face import load_face_encodings
    from datetime import datetime
    import streamlit as st

    session_info = get_session_by_id(session_id)
    if not session_info:
        st.error("Session not found.")
        return None

    subject_students = get_students_in_subject(session_info['subject_id'])
    if not subject_students:
        st.warning("No students enrolled in this subject.")
        return None

    # Load encodings for enrolled students
    student_encodings = {}
    student_info = {}
    for s in subject_students:
        enc = load_face_encodings(s['id'])
        if enc is not None:
            student_encodings[s['id']] = enc
            student_info[s['id']] = {
                'reg_no': s['reg_no'],
                'first_name': s['first_name'],
                'last_name': s['last_name']
            }

    if not student_encodings:
        st.warning("No face encodings found for enrolled students. Please enroll faces first.")
        return None

    marked_students = set()
    frame_counter = 0
    FRAME_SKIP = 5
    SCALE_FACTOR = 0.5
    UPSAMPLE = 0
    TOLERANCE = 0.4

    # --- SESSION STATE TO CONTROL CAMERA ---
    if 'camera_running' not in st.session_state:
        st.session_state.camera_running = True

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        nonlocal frame_counter, marked_students
        frame_counter += 1

        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)

        if frame_counter % FRAME_SKIP == 0:
            small = cv2.resize(img, (0, 0), fx=SCALE_FACTOR, fy=SCALE_FACTOR)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb, number_of_times_to_upsample=UPSAMPLE)
            encodings = face_recognition.face_encodings(rgb, locations)

            for (top, right, bottom, left), face_encoding in zip(locations, encodings):
                top, right, bottom, left = [int(v / SCALE_FACTOR) for v in (top, right, bottom, left)]

                recognized = False
                student_name = "Unknown"
                student_reg = ""
                best_match_id = None
                best_match_distance = 1.0

                for student_id, known_encoding in student_encodings.items():
                    if student_id in marked_students:
                        continue
                    matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=TOLERANCE)
                    if True in matches:
                        distance = face_recognition.face_distance([known_encoding], face_encoding)[0]
                        if distance < best_match_distance:
                            best_match_distance = distance
                            best_match_id = student_id

                if best_match_id is not None:
                    now = datetime.now()
                    status = determine_status(session_start_time)
                    mark_attendance(session_id, best_match_id, status, marked_by='face')
                    marked_students.add(best_match_id)
                    info = student_info[best_match_id]
                    student_name = f"{info['first_name']} {info['last_name']}"
                    student_reg = info['reg_no']
                    recognized = True
                    st.success(f"Marked present: {student_name} ({student_reg})")

                cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

                if recognized:
                    label = f"Hi, {student_name}"
                else:
                    label = "Unknown"
                    for student_id, known_encoding in student_encodings.items():
                        matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=TOLERANCE)
                        if True in matches:
                            info = student_info[student_id]
                            label = f"Hi, {info['first_name']} {info['last_name']}"
                            break

                cv2.putText(img, label, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.putText(img, f"Faces: {len(locations)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    # --- SMALL CAMERA BOX ---
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <style>
            .stVideo video {
                width: 350px !important;
                height: 280px !important;
                max-width: 350px !important;
                max-height: 280px !important;
                border-radius: 12px !important;
                border: 2px solid rgba(212, 175, 55, 0.4) !important;
                object-fit: cover !important;
            }
            .stVideo {
                width: 350px !important;
                height: 280px !important;
                max-width: 350px !important;
                max-height: 280px !important;
            }
            .stVideo > div {
                width: 350px !important;
                height: 280px !important;
                max-width: 350px !important;
                max-height: 280px !important;
            }
        </style>
        """, unsafe_allow_html=True)

        webrtc_streamer(
            key="attendance-scanner-final-v4",
            video_frame_callback=video_frame_callback,
            media_stream_constraints={
                "video": {"width": {"ideal": 320}, "height": {"ideal": 240}},
                "audio": False
            },
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            }
        )

    return True


# ─────────────────────────────────────────────
# MANUAL ATTENDANCE OVERRIDE
# ─────────────────────────────────────────────
def manually_mark_student(session_id: int, student_id: int, status: str):
    """Allows manual admin override to adjust student status."""
    mark_attendance(session_id, student_id, status, marked_by='manual')


def get_session_attendance(session_id: int):
    """Retrieves current attendance log for a session."""
    return get_attendance_for_session(session_id)