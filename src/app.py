import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from database.db import init_db
from database.db_queries import (
    login_admin, add_admin, get_all_admins,
    add_subject, remove_subject, get_subjects_by_admin, get_all_subjects,
    add_student, remove_student, get_all_students, get_students_by_group,
    enroll_student_in_subject, remove_student_from_subject, get_students_in_subject,
    get_attendance_by_subject, get_attendance_for_session
)
from dashboard.session import begin_session, close_session, process_student_scan, manually_mark_student
from dashboard.export import export_subject_attendance_csv, export_session_attendance_csv
from recognition.camera_test import run_camera_test
from enrollment.enroll_student import enroll_new_student, get_group_label
from enrollment.enroll_face import enroll_face_for_student

# Initialize DB structure cleanly on boot
init_db()

st.set_page_config(
    page_title="Project Identify",
    page_icon="🎓",
    layout="wide"
)

# Initialize global Session State attributes
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'admin' not in st.session_state:
    st.session_state.admin = None
if 'active_session_id' not in st.session_state:
    st.session_state.active_session_id = None
if 'active_session_start' not in st.session_state:
    st.session_state.active_session_start = None
if 'active_subject_id' not in st.session_state:
    st.session_state.active_subject_id = None

def show_login():
    st.title("🎓 Project Identify")
    st.subheader("Admin Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        admin = login_admin(username, password)
        if admin:
            st.session_state.logged_in = True
            st.session_state.admin = admin
            st.success(f"Welcome, {admin['full_name']}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.divider()
    st.caption("First time? Ask your system admin to create an account for you.")

def show_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.admin['full_name']}")
        st.caption(f"@{st.session_state.admin['username']}")
        st.divider()

        page = st.radio("Navigate", [
            "🏠 Dashboard",
            "📚 My Subjects",
            "👥 Students",
            "📷 Attendance Session",
            "🎥 Camera Test",  
            "📊 View Attendance",
            "⚙️ Admin Settings"
        ])

        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.admin = None
            st.session_state.active_session_id = None
            st.rerun()
    return page

def show_dashboard():
    admin = st.session_state.admin
    st.title(f"Welcome, {admin['full_name']} 👋")

    subjects = get_subjects_by_admin(admin['id'])
    students = get_all_students()

    col1, col2, col3 = st.columns(3)
    col1.metric("My Subjects", len(subjects))
    col2.metric("Total Students", len(students))
    col3.metric("Active Session", "Yes" if st.session_state.active_session_id else "No")

    if subjects:
        st.subheader("My Subjects Summary")
        for s in subjects:
            st.write(f"**{s['course_code']}** — {s['course_title']} | {s['program']} {s['year']} Year {s['semester']} Sem")

def show_subjects():
    admin = st.session_state.admin
    st.title("📚 My Subjects Management")

    with st.expander("➕ Add New Subject"):
        with st.form("add_subject_form"):
            code = st.text_input("Course Code")
            title = st.text_input("Course Title")
            program = st.selectbox("Program", ["BBA", "BBIS"])
            year = st.selectbox("Year", ["First", "Second", "Third", "Fourth"])
            semester = st.selectbox("Semester", ["First", "Second"])
            submitted = st.form_submit_button("Add Subject")

        if submitted:
            add_subject(code, title, program, year, semester, admin['id'])
            st.success(f"Subject {code} added successfully!")
            st.rerun()

    st.divider()
    subjects = get_subjects_by_admin(admin['id'])
    if not subjects:
        st.info("No subjects created yet. Add one above.")
        return

    for s in subjects:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{s['course_code']}** — {s['course_title']} | {s['program']} {s['year']} Year {s['semester']} Sem")
        if col2.button("Remove", key=f"remove_subject_{s['id']}"):
            remove_subject(s['id'])
            st.success("Subject removed.")
            st.rerun()

    st.divider()
    st.subheader("Manage Course Enrollment Roster")

    subject_options = {f"{s['course_code']} — {s['course_title']}": s['id'] for s in subjects}
    selected_label = st.selectbox("Select Target Subject Context", list(subject_options.keys()))
    selected_subject_id = subject_options[selected_label]

    enrolled = get_students_in_subject(selected_subject_id)
    enrolled_ids = {s['id'] for s in enrolled}
    all_students = get_all_students()
    not_enrolled = [s for s in all_students if s['id'] not in enrolled_ids]

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Enrolled Class List**")
        for s in enrolled:
            c1, c2 = st.columns([3, 1])
            c1.write(f"{s['reg_no']} — {s['last_name']} {s['first_name']}")
            if c2.button("Remove", key=f"unenroll_{selected_subject_id}_{s['id']}"):
                remove_student_from_subject(selected_subject_id, s['id'])
                st.rerun()

    with col2:
        st.write("**Available Accounts List**")
        for s in not_enrolled:
            c1, c2 = st.columns([3, 1])
            c1.write(f"{s['reg_no']} — {s['last_name']} {s['first_name']}")
            if c2.button("Add", key=f"enroll_{selected_subject_id}_{s['id']}"):
                enroll_student_in_subject(selected_subject_id, s['id'])
                st.rerun()

def show_students():
    st.title("👥 Student Database Operations")
    tabs = st.tabs(["All Students Registry", "Enroll New Student Meta", "Biometric Face Registration"])

    with tabs[0]:
        students = get_all_students()
        if students:
            groups = {}
            for s in students:
                key = get_group_label(s['program'], s['year'] or '', s['semester'] or '')
                groups.setdefault(key, []).append(s)

            for group_label, group_students in groups.items():
                st.subheader(group_label)
                df = pd.DataFrame([{
                    'Reg No.': s['reg_no'],
                    'Roll No.': s['roll_no'],
                    'Name': f"{s['last_name']} {s['first_name']} {s['middle_name'] or ''}".strip(),
                    'Gender': s['gender'],
                    'Face Enrolled': '✅' if s['face_enrolled'] else '❌'
                } for s in group_students])
                st.dataframe(df, use_container_width=True)

                reg_to_remove = st.text_input("Remove student by Reg No.", key=f"remove_{group_label}")
                if st.button("Delete Profile Record", key=f"btn_remove_{group_label}"):
                    match = next((s for s in group_students if s['reg_no'] == reg_to_remove), None)
                    if match:
                        remove_student(match['id'])
                        st.success(f"Removed profile record: {reg_to_remove}")
                        st.rerun()
                    else:
                        st.error("Registration ID match failure.")
        else:
            st.info("No registered records found.")

    with tabs[1]:
        st.subheader("Enroll New Student Profile")
        with st.form("enroll_student_form"):
            col1, col2, col3 = st.columns(3)
            last_name = col1.text_input("Last Name")
            first_name = col2.text_input("First Name")
            middle_name = col3.text_input("Middle Name (optional)")

            reg_no = st.text_input("Registration ID Number")
            gender = st.selectbox("Gender Identification", ["Male", "Female", "Prefer not to say"])
            program = st.selectbox("Academic Program Branch", ["BBA", "BBIS", "Transfer"])

            col4, col5 = st.columns(2)
            year = col4.selectbox("Year Bracket", ["First", "Second", "Third", "Fourth"])
            semester = col5.selectbox("Active Term Semester", ["First", "Second"])
            submitted = st.form_submit_button("Save Student Metadata Profile")

        if submitted:
            success = enroll_new_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester)
            if success:
                st.success(f"Profile saved: {last_name}, {first_name}")
            else:
                st.error(f"Duplicate structural reference exception for: {reg_no}")

    with tabs[2]:
        st.subheader("Facial Signature Matrix Builder")
        students = get_all_students()
        not_enrolled = [s for s in students if not s['face_enrolled']]
        already_enrolled = [s for s in students if s['face_enrolled']]

        st.write(f"**Pending Calibration:** {len(not_enrolled)} entries")
        if not_enrolled:
            options = {f"{s['reg_no']} — {s['last_name']} {s['first_name']}": s['id'] for s in not_enrolled}
            selected = st.selectbox("Select Target Registry Matrix", list(options.keys()))
            student_id = options[selected]

            if st.button("📷 Capture Webcam Facial Target"):
                with st.spinner("Engaging high-definition camera array modules..."):
                    success, message = enroll_face_for_student(student_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        if already_enrolled:
            st.divider()
            st.write(f"**Calibrated Enrolled Base:** {len(already_enrolled)} profiles")

def show_session():
    admin = st.session_state.admin
    st.title("📷 Live Attendance Tracker Hub")
    subjects = get_subjects_by_admin(admin['id'])
    if not subjects:
        st.warning("No subjects bound to your admin credentials.")
        return

    if not st.session_state.active_session_id:
        st.subheader("Launch Real-Time Tracking Windows")
        subject_options = {f"{s['course_code']} — {s['course_title']} ({s['program']} {s['year']} Yr)": s['id'] for s in subjects}
        selected_label = st.selectbox("Target Subject Track", list(subject_options.keys()))
        selected_subject_id = subject_options[selected_label]

        # FIXED: Wrapped inside an st.form block to guarantee text processing synchronization
        with st.form("start_session_form"):
            password = st.text_input("Confirm Account Passphrase Code", type="password")
            submitted_start = st.form_submit_button("▶️ Initialize Tracking Session")

        if submitted_start:
            session_id = begin_session(selected_subject_id, admin['id'], admin['username'], password)
            if session_id:
                st.session_state.active_session_id = session_id
                st.session_state.active_session_start = datetime.now().strftime("%H:%M:%S")
                st.session_state.active_subject_id = selected_subject_id
                st.success("Live operational tracking window initialized!")
                st.rerun()
            else:
                st.error("Credential confirmation failed. Make sure you entered your exact login password.")
    else:
        session_id = st.session_state.active_session_id
        session_start = st.session_state.active_session_start

        st.success(f"🟢 Tracking Active — Windows Open From {session_start}")
        st.caption("Instruct targets to interface with biometric hardware scanning zones.")
        st.divider()

        st.subheader("Biometric Verification Zone")
        if st.button("📸 Capture & Parse Real-Time Match"):
            with st.spinner("Analyzing camera frames..."):
                student_id = process_student_scan(session_id, session_start)
            if student_id:
                st.success(f"✅ Biometric target resolved securely for structural database reference ID: {student_id}")
                st.rerun()
            else:
                st.warning("Match lookup mismatch. Please fall back to manual override options below.")

        st.divider()
        st.subheader("Manual Override Console")
        enrolled_students = get_students_in_subject(st.session_state.active_subject_id)
        student_options = {f"{s['reg_no']} — {s['last_name']} {s['first_name']}": s['id'] for s in enrolled_students}

        if student_options:
            col1, col2, col3 = st.columns(3)
            selected_student = col1.selectbox("Target Target Vector", list(student_options.keys()))
            manual_status = col2.selectbox("Override Operational Flag", ["Present", "Absent", "Late"])
            if col3.button("Force Apply Flags"):
                manually_mark_student(session_id, student_options[selected_student], manual_status)
                st.success(f"Applied manual override flag: {manual_status}")
                st.rerun()

        st.divider()
        st.subheader("Live Class Status Monitor")
        records = get_attendance_for_session(session_id)
        if records:
            st.dataframe(pd.DataFrame(records), use_container_width=True)

        st.divider()
        st.subheader("Session Closure Protocol")
        
        # FIXED: Wrapped inside an st.form block to guarantee text processing synchronization
        with st.form("end_session_form"):
            end_password = st.text_input("Enter account password to commit data", type="password")
            submitted_end = st.form_submit_button("⏹️ Conclude Track Windows")

        if submitted_end:
            if close_session(session_id, admin['username'], end_password):
                st.session_state.active_session_id = None
                st.session_state.active_session_start = None
                st.session_state.active_subject_id = None
                st.success("Session closed and saved successfully.")
                st.rerun()
            else:
                st.error("Credential confirmation failure.")

def show_attendance():
    admin = st.session_state.admin
    st.title("📊 Compiled Log Viewers")
    subjects = get_subjects_by_admin(admin['id'])
    if not subjects:
        st.info("No active registry tracks found.")
        return

    subject_options = {f"{s['course_code']} — {s['course_title']}": s['id'] for s in subjects}
    selected_label = st.selectbox("Filter Subject Track Historical View", list(subject_options.keys()))
    selected_id = subject_options[selected_label]

    records = get_attendance_by_subject(selected_id)
    if not records:
        st.info("No operational logs historical data compiled yet.")
        return

    st.dataframe(pd.DataFrame(records), use_container_width=True)

    if st.button("⬇️ Package & Extract Logs via CSV"):
        filepath = export_subject_attendance_csv(selected_id)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                st.download_button(
                    label="Download CSV Report File",
                    data=f,
                    file_name=os.path.basename(filepath),
                    mime='text/csv'
                )

def show_admin_settings():
    st.title("⚙️ Global Configuration Settings")
    admin = st.session_state.admin
    tabs = st.tabs(["Administrators Directory", "Provision New Administrative Role"])

    with tabs[0]:
        admins = get_all_admins()
        for a in admins:
            st.write(f"**{a['full_name']}** (@{a['username']}) — Role Created: {a['created_at']}")

    with tabs[1]:
        st.subheader("Provision Administrative Account Access Permissions")
        with st.form("add_admin_form"):
            new_username = st.text_input("Account Identifier Handle (Username)")
            new_fullname = st.text_input("Legal Full Name Identity")
            new_password = st.text_input("Secret Security Passphrase", type="password")
            submitted = st.form_submit_button("Grant System Admin Access Permissions")

        if submitted:
            if add_admin(new_username, new_password, new_fullname, created_by=admin['id']):
                st.success(f"System profile established for account handle: @{new_username}")
            else:
                st.error("Identifier namespace collides with a pre-existing asset.")

def show_camera_test():
    st.title("🎥 Camera Test")
    st.write("Opens a live window that names and boxes every recognized face. Press **Q** in that window to close it.")
    if st.button("▶️ Launch Recognition Test"):
        with st.spinner("Camera window is open — press Q in it when you're done..."):
            success = run_camera_test()
        if not success:
            st.error("No enrolled faces found, or the webcam couldn't be opened.")

def main():
    if not st.session_state.logged_in:
        show_login()
        return

    page = show_sidebar()
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📚 My Subjects":
        show_subjects()
    elif page == "👥 Students":
        show_students()
    elif page == "📷 Attendance Session":
        show_session()
    elif page == "🎥 Camera Test":
        show_camera_test()
    elif page == "📊 View Attendance":
        show_attendance()
    elif page == "⚙️ Admin Settings":
        show_admin_settings()

if __name__ == "__main__":
    main()