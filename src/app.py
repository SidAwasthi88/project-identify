import streamlit as st
import sys
import os
import pandas as pd
import base64
from datetime import datetime

# --- PATH RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

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

# Initialize Database Schema
init_db()

st.set_page_config(
    page_title="KUSOM Portal | Project Identify", 
    page_icon="🛡️",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- HELPER FUNCTIONS ---
def get_image_path(filename: str) -> str | None:
    paths_to_check = [
        os.path.join(PROJECT_ROOT, "images", filename),
        os.path.join(CURRENT_DIR, "..", "images", filename),
        os.path.join("images", filename)
    ]
    for p in paths_to_check:
        if os.path.exists(p):
            return p
    return None

def format_student_name(student_dict: dict) -> str:
    first = (student_dict.get('first_name') or '').strip()
    middle = (student_dict.get('middle_name') or '').strip()
    last = (student_dict.get('last_name') or '').strip()
    if middle:
        return f"{first} {middle} {last}"
    return f"{first} {last}"

# --- SESSION STATE INITIALIZATION ---
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

# --- INJECT CSS CONDITIONALLY ---
def inject_custom_css():
    # Base CSS (always applied)
    base_css = """
    <style>
    /* 1. HEADER TRANSPARENT */
    header[data-testid="stHeader"], 
    .stAppHeader, 
    [data-testid="stHeader"] {
        background: transparent !important;
        z-index: 99999 !important;
    }

    /* 2. HIDE DEPLOY BUTTON, TOOLBAR, MENU, FOOTER */
    .stAppDeployButton, 
    [data-testid="stAppDeployButton"], 
    [data-testid="stToolbar"], 
    #MainMenu, 
    footer {
        display: none !important;
    }

    /* 3. HIDE STREAMLIT'S DEFAULT TOGGLE BUTTON */
    button[kind="header"] {
        display: none !important;
    }

    /* 4. HIDE STREAMLIT'S DEFAULT COLLAPSE CONTROL */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* 5. SMOOTH PAGE LOAD ANIMATION */
    @keyframes fadeInSlide {
        0% { opacity: 0; transform: translateY(12px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    .stApp {
        background: radial-gradient(circle at top right, #3A0000 0%, #1A0000 60%, #0A0000 100%) !important;
        color: #F8F9FA !important;
        animation: fadeInSlide 0.5s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
    }

    /* 6. FLOATING ANIMATION FOR LOGO */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-7px); }
        100% { transform: translateY(0px); }
    }
    .animated-logo img {
        animation: float 4s ease-in-out infinite;
        filter: drop-shadow(0px 10px 18px rgba(0,0,0,0.6));
    }

    /* 7. PULSING LIVE BADGE */
    @keyframes pulseAlert {
        0% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
    }
    .live-badge {
        display: inline-block;
        background: linear-gradient(135deg, #FF3B30, #C91C11);
        color: white;
        padding: 5px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        animation: pulseAlert 2s infinite;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(255, 59, 48, 0.4);
    }

    /* 8. INPUTS & FORM ELEMENTS */
    input, select, textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    input:focus, select:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.3) !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
    }

    /* 9. BUTTONS */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #8B0000 0%, #520000 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
        text-transform: uppercase;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }

    .stButton>button:hover, div[data-testid="stFormSubmitButton"]>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #A00000 0%, #660000 100%) !important;
        border-color: #D4AF37 !important;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.35) !important;
        transform: translateY(-2px) scale(1.01) !important;
    }

    /* 10. DASHBOARD CARDS */
    .dash-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #D4AF37;
        border-radius: 12px;
        padding: 22px;
        min-height: 120px; 
        display: flex;     
        flex-direction: column; 
        justify-content: center;
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
    }

    .dash-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
        border-color: rgba(212, 175, 55, 0.5);
    }

    /* 11. PREMIUM TOP BAR */
    .premium-top-bar {
        background: rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-bottom: 1px solid rgba(212, 175, 55, 0.35);
        padding: 14px 28px;
        border-radius: 14px;
        margin-bottom: 25px;
    }

    /* 12. STYLED TABS */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(0,0,0,0.35) !important;
        padding: 6px !important;
        border-radius: 12px !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8B0000, #520000) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
    }

    /* 13. TYPOGRAPHY */
    h1 {
        background: linear-gradient(45deg, #FFFFFF 30%, #D4AF37 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    hr { border-top: 1px solid rgba(212, 175, 55, 0.2) !important; }

    /* 14. FORCE CENTERING FOR IMAGES */
    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
    }

    [data-testid="stImage"] img {
        margin: 0 auto !important;
        display: block !important;
    }
    </style>
    """

    # Sidebar CSS (only applied when logged in)
    sidebar_css = """
    <style>
    /* SIDEBAR - ONLY WHEN LOGGED IN */
    section[data-testid="stSidebar"] {
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        height: 100vh !important;
        width: 300px !important;
        min-width: 300px !important;
        background-color: #0F0000 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.4) !important;
        padding-top: 60px !important;
        z-index: 9999 !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: translateX(0) !important;
        transition: all 0.3s ease !important;
    }

    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div,
    [data-testid="stSidebarUserContent"],
    [data-testid="stSidebarHeader"] {
        background-color: #0F0000 !important;
    }

    /* MAIN CONTENT - PUSH TO THE RIGHT TO AVOID OVERLAP */
    [data-testid="stAppViewContainer"] {
        margin-left: 300px !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    </style>
    """

    # Apply base CSS always, sidebar CSS only when logged in
    if st.session_state.get('logged_in', False):
        st.markdown(base_css + sidebar_css, unsafe_allow_html=True)
    else:
        st.markdown(base_css, unsafe_allow_html=True)

# --- PAGE: LOGIN ---
def show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        logo_path = get_image_path("logo.png")
        if logo_path:
            with open(logo_path, "rb") as image_file:
                encoded_logo = base64.b64encode(image_file.read()).decode("utf-8")
            
            logo_html = '<div class="animated-logo" style="display: flex; justify-content: center; align-items: center; width: 100%; margin-bottom: 15px;"><img src="data:image/png;base64,' + encoded_logo + '" style="width: 125px; height: auto; display: block; margin: 0 auto;"></div>'
            st.markdown(logo_html, unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; margin-bottom: 0px;'>KUSOM <span style='color: #D4AF37;'>Identify</span></h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #A0AAB5; font-size: 0.95rem; margin-bottom: 20px;'>Biometric Attendance Management System</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Administrator Handle", placeholder="Enter username").strip()
            password = st.text_input("Security Passphrase", type="password", placeholder="••••••••").strip()
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("AUTHENTICATE SYSTEM ACCESS", use_container_width=True)
            
            if submitted:
                admin = login_admin(username, password)
                if admin:
                    st.session_state.logged_in = True
                    st.session_state.admin = admin
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid username or passphrase.")

# --- NAVIGATION & HEADER ---
def show_header_and_sidebar():
    admin = st.session_state.admin
    session_status = "<span class='live-badge'>● LIVE TRACKING</span>" if st.session_state.active_session_id else ""

    html_header = '<div class="premium-top-bar" style="display: flex; justify-content: space-between; align-items: center;"><div style="display: flex; align-items: center; gap: 15px;"><span style="font-size: 1.3rem; font-weight: 700; color: #FFFFFF;">Project <span style="color: #D4AF37;">Identify</span></span>' + session_status + '</div><div style="text-align: right; min-width: 150px;"><span style="color: #A0AAB5; font-size: 0.8rem;">Authorized Admin</span><br><span style="color: #FFFFFF; font-weight: 600; font-size: 0.95rem;">' + admin['full_name'] + '</span></div></div>'
    
    st.markdown(html_header, unsafe_allow_html=True)

    with st.sidebar:
        logo_path = get_image_path("logo.png")
        if logo_path:
            st.image(logo_path, width=75)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### Menu")
        page = st.radio("Menu", [
            "Dashboard",
            "My Subjects",
            "Student Directory",
            "Live Attendance",
            "Camera Check",
            "Reports & Downloads",
            "Admin Settings"
        ], label_visibility="collapsed")

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("TERMINATE SESSION", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.admin = None
            st.session_state.active_session_id = None
            st.rerun()

    return page

# --- PAGE: DASHBOARD ---
def show_dashboard():
    admin = st.session_state.admin
    st.markdown("<h1>Command Center</h1>", unsafe_allow_html=True)
    st.write("Real-time telemetry and active course overview.")
    st.markdown("<br>", unsafe_allow_html=True)

    subjects = get_subjects_by_admin(admin['id'])
    students = get_all_students()

    c1, c2, c3 = st.columns(3)
    
    with c1:
        c1_html = '<div class="dash-card"><h3 style="color: #D4AF37; margin:0; font-size: 2.4rem;">' + str(len(subjects)) + '</h3><p style="color: #A0AAB5; margin:0; font-weight: 500; text-transform: uppercase; font-size: 0.78rem;">Allocated Modules</p></div>'
        st.markdown(c1_html, unsafe_allow_html=True)
    
    with c2:
        c2_html = '<div class="dash-card"><h3 style="color: #D4AF37; margin:0; font-size: 2.4rem;">' + str(len(students)) + '</h3><p style="color: #A0AAB5; margin:0; font-weight: 500; text-transform: uppercase; font-size: 0.78rem;">Registered Biometrics</p></div>'
        st.markdown(c2_html, unsafe_allow_html=True)
    
    with c3:
        status_color = "#FF3B30" if st.session_state.active_session_id else "#A0AAB5"
        status_text = "Tracking Active" if st.session_state.active_session_id else "System Standby"
        c3_html = '<div class="dash-card" style="border-left-color: ' + status_color + ';"><h3 style="color: ' + status_color + '; margin:0; font-size: 1.4rem; padding-top:8px;">' + status_text + '</h3><p style="color: #A0AAB5; margin:0; font-weight: 500; text-transform: uppercase; font-size: 0.78rem; padding-top: 8px;">Camera Array Status</p></div>'
        st.markdown(c3_html, unsafe_allow_html=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    if subjects:
        st.subheader("Assigned Course Modules")
        grid_cols = st.columns(2)
        for idx, s in enumerate(subjects):
            with grid_cols[idx % 2]:
                card_html = '<div class="dash-card" style="border-left: 2px solid rgba(212, 175, 55, 0.4); margin-bottom: 15px;"><div style="display: flex; justify-content: space-between;"><h4 style="margin: 0; color: #FFFFFF;">' + s['course_code'] + '</h4><span style="background: rgba(212, 175, 55, 0.2); color: #D4AF37; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem;">' + s['program'] + '</span></div><p style="margin: 5px 0 0 0; color: #E2E8F0; font-size: 1.05rem;">' + s['course_title'] + '</p><p style="margin: 8px 0 0 0; color: #94A3B8; font-size: 0.85rem;">Year ' + s['year'] + ' • Semester ' + s['semester'] + '</p></div>'
                st.markdown(card_html, unsafe_allow_html=True)

# --- PAGE: SUBJECTS ---
def show_subjects():
    admin = st.session_state.admin
    st.markdown("<h1>Course Modules</h1>", unsafe_allow_html=True)
    
    with st.expander("REGISTER NEW COURSE MODULE"):
        with st.form("add_subject_form"):
            c1, c2 = st.columns(2)
            code = c1.text_input("Course Code (e.g. GEM501)").strip()
            title = c2.text_input("Course Title").strip()
            
            c3, c4, c5 = st.columns(3)
            program = c3.selectbox("Program", ["BBA", "BBIS", "MBA"])
            year = c4.selectbox("Year", ["First", "Second", "Third", "Fourth"])
            semester = c5.selectbox("Semester", ["First", "Second"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("DEPLOY MODULE TO DATABASE")

            if submitted:
                if code and title:
                    add_subject(code, title, program, year, semester, admin['id'])
                    st.success(f"Module {code} initialized.")
                    st.rerun()
                else:
                    st.error("Please provide both Course Code and Title.")

    subjects = get_subjects_by_admin(admin['id'])
    if not subjects:
        st.info("No course modules currently assigned.")
        return

    st.markdown("<hr>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Manage Active Modules")
        for s in subjects:
            with st.container():
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{s['course_code']}** - {s['course_title']}<br><span style='color:gray; font-size:0.8rem;'>{s['program']} {s['year']}</span>", unsafe_allow_html=True)
                if c2.button("DELETE", key=f"del_subj_{s['id']}", help="Irreversible action"):
                    remove_subject(s['id'])
                    st.rerun()
                st.markdown("<div style='height: 1px; background: rgba(255,255,255,0.1); margin: 10px 0;'></div>", unsafe_allow_html=True)

    with col2:
        st.subheader("Student Roster Matrix")
        subject_options = {f"{s['course_code']} - {s['course_title']}": s['id'] for s in subjects}
        selected_label = st.selectbox("Select Target Course", list(subject_options.keys()))
        selected_subject_id = subject_options[selected_label]

        enrolled = get_students_in_subject(selected_subject_id)
        enrolled_ids = {s['id'] for s in enrolled}
        all_students = get_all_students()
        not_enrolled = [s for s in all_students if s['id'] not in enrolled_ids]

        t1, t2 = st.tabs(["Enrolled Students", "Available for Import"])
        with t1:
            if enrolled:
                for s in enrolled:
                    ec1, ec2 = st.columns([3, 1])
                    ec1.write(f"**{format_student_name(s)}** ({s['reg_no']})")
                    if ec2.button("Eject", key=f"unenroll_{s['id']}"):
                        remove_student_from_subject(selected_subject_id, s['id'])
                        st.rerun()
            else:
                st.info("No students enrolled in this course.")

        with t2:
            if not_enrolled:
                for s in not_enrolled:
                    ac1, ac2 = st.columns([3, 1])
                    ac1.write(f"**{format_student_name(s)}** ({s['reg_no']})")
                    if ac2.button("Add", key=f"enroll_{s['id']}"):
                        enroll_student_in_subject(selected_subject_id, s['id'])
                        st.rerun()
            else:
                st.info("All registered students are already in this course.")

# --- PAGE: STUDENTS ---
def show_students():
    st.markdown("<h1>Student Matrix</h1>", unsafe_allow_html=True)
    tabs = st.tabs(["Active Directory", "Create Student Profile", "Biometric Facial Setup"])

    with tabs[0]:
        students = get_all_students()
        if students:
            groups = {}
            for s in students:
                key = get_group_label(s['program'], s['year'] or '', s['semester'] or '')
                groups.setdefault(key, []).append(s)

            for group_label, group_students in groups.items():
                st.markdown(f"### {group_label}")
                df = pd.DataFrame([{
                    'Registration ID': s['reg_no'],
                    'Full Name': format_student_name(s),
                    'Gender': s['gender'],
                    'Biometric Status': 'Verified' if s['face_enrolled'] else 'Pending'
                } for s in group_students])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("Registry empty. Use 'Create Student Profile' tab to enroll students.")

    with tabs[1]:
        with st.form("enroll_student_form"):
            c1, c2, c3 = st.columns(3)
            last_name = c1.text_input("Surname / Last Name").strip()
            first_name = c2.text_input("First Name").strip()
            middle_name = c3.text_input("Middle Name (Optional)").strip()

            c4, c5 = st.columns(2)
            reg_no = c4.text_input("Registration ID").strip()
            gender = c5.selectbox("Gender", ["Male", "Female", "Other"])
            
            c6, c7, c8 = st.columns(3)
            program = c6.selectbox("Program", ["BBA", "BBIS", "MBA"])
            year = c7.selectbox("Year", ["First", "Second", "Third", "Fourth"])
            semester = c8.selectbox("Semester", ["First", "Second"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("SAVE PROFILE RECORD")

        if submitted:
            if not reg_no or not first_name or not last_name:
                st.error("Please complete First Name, Surname, and Registration ID.")
            else:
                if enroll_new_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester):
                    st.success(f"Profile created for {first_name} {last_name}.")
                    st.rerun()
                else:
                    st.error("Registration ID already exists in system database.")

    with tabs[2]:
        st.markdown("### Facial Topology Calibration")
        students = get_all_students()
        not_enrolled = [s for s in students if not s['face_enrolled']]

        if not_enrolled:
            options = {f"{format_student_name(s)} ({s['reg_no']})": s['id'] for s in not_enrolled}
            selected = st.selectbox("Select Target Student", list(options.keys()))
            
            st.info("Ensure subject is well-lit and directly faces the visual camera array.")
            if st.button("INITIALIZE CAMERA BIOMETRIC CAPTURE"):
                with st.spinner("Locking facial vector geometry..."):
                    success, message = enroll_face_for_student(options[selected])
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.success("All registered student profiles have calibrated facial encodings.")

# --- PAGE: ATTENDANCE SESSION ---
def show_session():
    admin = st.session_state.admin
    st.markdown("<h1>Live Tracking</h1>", unsafe_allow_html=True)
    subjects = get_subjects_by_admin(admin['id'])
    
    if not st.session_state.active_session_id:
        if not subjects:
            st.warning("No course modules assigned to your account.")
            return

        box_html = '<div class="dash-card"><h3>Initiate Tracking Session</h3><p style="color:gray;">Select the course module and enter your password to activate the biometric scanner bridge.</p></div><br>'
        st.markdown(box_html, unsafe_allow_html=True)

        subject_options = {f"{s['course_code']} - {s['course_title']}": s['id'] for s in subjects}
        selected_subject_id = subject_options[st.selectbox("Select Target Course Module", list(subject_options.keys()))]

        with st.form("start_session"):
            password = st.text_input("Admin Passphrase", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("ENGAGE TRACKING SESSION"):
                session_id = begin_session(selected_subject_id, admin['id'], admin['username'], password)
                if session_id:
                    st.session_state.active_session_id = session_id
                    st.session_state.active_session_start = datetime.now().strftime("%H:%M:%S")
                    st.session_state.active_subject_id = selected_subject_id
                    st.rerun()
                else:
                    st.error("Authentication rejected. Passphrase incorrect.")
    else:
        session_id = st.session_state.active_session_id
        start_time = st.session_state.active_session_start

        # --- CAMERA INSIDE STREAMLIT ---
        st.markdown("""
        <div style="background: rgba(255, 59, 48, 0.1); border: 1px solid #FF3B30; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
            <h3 style="color:#FF3B30; margin:0;">SCANNER ARMED</h3>
            <p style="color:white; margin:0; padding-top:4px;">Camera is active — faces will be detected automatically</p>
        </div>
        """, unsafe_allow_html=True)

        # --- START THE CAMERA INSIDE STREAMLIT ---
        process_student_scan(session_id, start_time)

        # --- MANUAL ATTENDANCE OVERRIDE ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("Manual Attendance Override")
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            enrolled_students = get_students_in_subject(st.session_state.active_subject_id)
            if enrolled_students:
                opts = {f"{format_student_name(s)} ({s['reg_no']})": s['id'] for s in enrolled_students}
                sel = st.selectbox("Target Student", list(opts.keys()))
                stat = st.selectbox("Status", ["Present", "Absent", "Late"])
                if st.button("FORCE RECORD UPDATE", use_container_width=True):
                    manually_mark_student(session_id, opts[sel], stat)
                    st.success("Attendance status manually updated.")
                    st.rerun()

        with c2:
            st.markdown("### Live Session Logs")
            records = get_attendance_for_session(session_id)
            if records:
                formatted_records = []
                for r in records:
                    r_copy = dict(r)
                    if 'first_name' in r_copy and 'last_name' in r_copy:
                        r_copy['Student Name'] = format_student_name(r_copy)
                    formatted_records.append(r_copy)
                st.dataframe(pd.DataFrame(formatted_records), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("end_session"):
            pw = st.text_input("Sign-off Passphrase", type="password")
            if st.form_submit_button("TERMINATE TRACKING SESSION"):
                if close_session(session_id, admin['username'], pw):
                    st.session_state.active_session_id = None
                    st.rerun()
                else:
                    st.error("Key rejected. Passphrase incorrect.")

# --- PAGE: VIEW ATTENDANCE ---
def show_attendance():
    st.markdown("<h1>Reports & Downloads</h1>", unsafe_allow_html=True)
    subjects = get_subjects_by_admin(st.session_state.admin['id'])
    
    if not subjects:
        st.info("No course modules available.")
        return

    subject_options = {f"{s['course_code']} - {s['course_title']}": s['id'] for s in subjects}
    selected_id = subject_options[st.selectbox("Data Source Module", list(subject_options.keys()))]

    records = get_attendance_by_subject(selected_id)
    if not records:
        st.info("No attendance records logged for this course yet.")
        return

    formatted_records = []
    for r in records:
        r_copy = dict(r)
        if 'first_name' in r_copy and 'last_name' in r_copy:
            r_copy['Name'] = format_student_name(r_copy)
        formatted_records.append(r_copy)

    st.dataframe(pd.DataFrame(formatted_records), use_container_width=True, hide_index=True)

    if st.button("GENERATE CSV REPORT"):
        filepath = export_subject_attendance_csv(selected_id)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                st.download_button("CONFIRM DOWNLOAD CSV", data=f, file_name=os.path.basename(filepath), mime='text/csv')

# --- PAGE: CAMERA TEST ---
def show_camera_test():
    st.markdown("<h1>Camera Check</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="dash-card" style="border-left-color: #007AFF;">
        <h3 style="margin:0;">Camera Feed Test</h3>
        <p style="color:#A0AAB5;">Click "Start" to begin face detection.</p>
    </div>
    <br>
    """, unsafe_allow_html=True)

    from streamlit_webrtc import webrtc_streamer
    import av
    import cv2
    import face_recognition
    from database.db_queries import get_all_students
    from enrollment.enroll_face import load_face_encodings

    # --- LOAD ALL STUDENT ENCODINGS ONCE ---
    @st.cache_data
    def load_all_student_encodings():
        students = get_all_students()
        student_data = []
        for s in students:
            enc = load_face_encodings(s['id'])
            if enc is not None:
                student_data.append({
                    'id': s['id'],
                    'reg_no': s['reg_no'],
                    'first_name': s['first_name'],
                    'last_name': s['last_name'],
                    'encoding': enc
                })
        return student_data

    student_data = load_all_student_encodings()

    # --- CONFIG ---
    FRAME_SKIP = 3
    SCALE_FACTOR = 0.5
    UPSAMPLE = 0
    frame_counter = 0

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        nonlocal frame_counter
        frame_counter += 1

        img = frame.to_ndarray(format="bgr24")

        # --- MIRROR ---
        img = cv2.flip(img, 1)

        # Process every few frames
        if frame_counter % FRAME_SKIP == 0:
            # Downscale for speed
            small = cv2.resize(img, (0, 0), fx=SCALE_FACTOR, fy=SCALE_FACTOR)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            # Detect faces
            locations = face_recognition.face_locations(rgb, number_of_times_to_upsample=UPSAMPLE)
            encodings = face_recognition.face_encodings(rgb, locations)

            # Draw rectangles and display names
            for (top, right, bottom, left), face_encoding in zip(locations, encodings):
                # Scale back to original size
                top, right, bottom, left = [int(v / SCALE_FACTOR) for v in (top, right, bottom, left)]

                # Default: Unknown
                name = "Unknown"
                reg_no = ""

                # Compare with all enrolled students
                for student in student_data:
                    matches = face_recognition.compare_faces([student['encoding']], face_encoding, tolerance=0.5)
                    if True in matches:
                        name = f"{student['first_name']} {student['last_name']}"
                        reg_no = student['reg_no']
                        break

                # Draw green rectangle
                cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

                # Draw name and roll number above the face
                if reg_no:
                    label = f"{name} ({reg_no})"
                    cv2.putText(img, label, (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    cv2.putText(img, "Unknown", (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Show face count
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
            key="camera-test-final-mirror",
            video_frame_callback=video_frame_callback,
            media_stream_constraints={
                "video": {"width": {"ideal": 320}, "height": {"ideal": 240}},
                "audio": False
            },
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            }
        )

# --- PAGE: ADMIN SETTINGS ---
def show_admin_settings():
    st.markdown("<h1>Admin Settings</h1>", unsafe_allow_html=True)
    tabs = st.tabs(["Active Administrators", "Authorize New Admin"])

    with tabs[0]:
        admins = get_all_admins()
        for a in admins:
            st.markdown(f"**{a['full_name']}** <br><span style='color:#D4AF37;font-size:0.85rem;'>Username: {a['username']}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='opacity:0.2;'>", unsafe_allow_html=True)

    with tabs[1]:
        with st.form("add_admin"):
            user = st.text_input("Handle / Username").strip()
            name = st.text_input("Full Name").strip()
            pw = st.text_input("Initial Security Passphrase", type="password").strip()
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("AUTHORIZE NEW ADMIN"):
                if user and name and pw:
                    if add_admin(user, pw, name, created_by=st.session_state.admin['id']):
                        st.success(f"Administrator '{user}' authorized successfully.")
                    else:
                        st.error("Username already exists in system.")
                else:
                    st.error("All input fields are required.")

# --- ROUTER ENTRYPOINT ---
def main():
    # Inject CSS based on login status
    inject_custom_css()
    
    if not st.session_state.logged_in:
        show_login()
        return

    page = show_header_and_sidebar()
    
    if page == "Dashboard": show_dashboard()
    elif page == "My Subjects": show_subjects()
    elif page == "Student Directory": show_students()
    elif page == "Live Attendance": show_session()
    elif page == "Camera Check": show_camera_test()
    elif page == "Reports & Downloads": show_attendance()
    elif page == "Admin Settings": show_admin_settings()

if __name__ == "__main__":
    main()