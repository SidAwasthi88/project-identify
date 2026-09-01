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


# --- RECOGNITION IMPORTS MOVED INSIDE FUNCTIONS ---
# (run_camera_test, enroll_new_student, get_group_label, enroll_face_for_student)


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
    from database.db_queries import get_all_students, remove_student
    
    st.markdown("<h1>Student Matrix</h1>", unsafe_allow_html=True)
    
    # --- 3 TABS ---
    tab1, tab2, tab3 = st.tabs(["Active Directory", "Create Student Profile", "Biometric Facial Setup"])
    
    # --- TAB 1: ACTIVE DIRECTORY ---
    with tab1:
        students = get_all_students()
        if students:
            data = []
            for s in students:
                data.append({
                    'ID': s['id'],
                    'Registration No': s.get('reg_no', ''),
                    'Full Name': format_student_name(s),
                    'Gender': s.get('gender', ''),
                    'Program': s.get('program', ''),
                    'Year': s.get('year', ''),
                    'Semester': s.get('semester', ''),
                    'Face Status': 'Verified' if s.get('face_enrolled') else 'Pending'
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total Students: {len(students)}")
            
            # Delete student section
            st.markdown("---")
            st.subheader("Delete Student")
            delete_options = {f"{s['reg_no']} - {format_student_name(s)}": s['id'] for s in students}
            selected_to_delete = st.selectbox("Select Student to Delete", list(delete_options.keys()))
            student_id_to_delete = delete_options[selected_to_delete]
            if st.button("Delete Student", use_container_width=True):
                import os
                enc_file = os.path.join('data', 'encodings', f"{student_id_to_delete}.pkl")
                if os.path.exists(enc_file):
                    os.remove(enc_file)
                result = remove_student(student_id_to_delete)
                if result:
                    st.success("Student deleted successfully.")
                    st.rerun()
                else:
                    st.error("Failed to delete student.")
        else:
            st.info("No students found.")
    
    # --- TAB 2: CREATE STUDENT PROFILE (PASTE YOUR CODE HERE) ---
    with tab2:
        with st.form("enroll_student_form"):
            col1, col2, col3 = st.columns(3)
            last_name = col1.text_input("Surname / Last Name *").strip()
            first_name = col2.text_input("First Name *").strip()
            middle_name = col3.text_input("Middle Name (Optional)").strip()

            col4, col5 = st.columns(2)
            reg_no = col4.text_input("Registration ID *").strip()
            gender = col5.selectbox("Gender", ["Male", "Female", "Other"])
            
            col6, col7, col8 = st.columns(3)
            program = col6.selectbox("Program", ["BBA", "BBIS", "MBA"])
            year = col7.selectbox("Year", ["First", "Second", "Third", "Fourth"])
            semester = col8.selectbox("Semester", ["First", "Second"])
            
            submitted = st.form_submit_button("Create Student Profile", use_container_width=True)

        if submitted:
            if not reg_no or not first_name or not last_name:
                st.error("Please complete all required fields.")
            else:
                from enrollment.enroll_student import enroll_new_student
                result = enroll_new_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester)
                if result and result[0]:
                    st.success(f"Student profile created for {first_name} {last_name}.")
                    st.rerun()
                else:
                    st.error(result[1] if result and len(result) > 1 else "Registration ID already exists.")
    
    # --- TAB 3: BIOMETRIC FACIAL SETUP ---
    with tab3:
        st.markdown("### Biometric Facial Setup")
        students = get_all_students()
        not_enrolled = [s for s in students if not s.get('face_enrolled')]

        if not_enrolled:
            options = {f"{format_student_name(s)} ({s['reg_no']})": s['id'] for s in not_enrolled}
            selected = st.selectbox("Select Student for Face Enrollment", list(options.keys()))
            st.info("Camera will open in a separate window. Press 'q' to cancel.")
            if st.button("Run Camera for Biometric Setup", use_container_width=True):
                import sys
                import os
                src_path = os.path.join(os.path.dirname(__file__), '..')
                if src_path not in sys.path:
                    sys.path.append(src_path)
                from enrollment.enroll_face import enroll_face_for_student
                with st.spinner("Opening camera..."):
                    try:
                        success, message = enroll_face_for_student(options[selected])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.success("All students have completed facial enrollment.")

# --- PAGE: ATTENDANCE SESSION ---
def show_session():
    from database.db_queries import get_students_in_subject, get_attendance_for_session, get_session_by_id, mark_attendance
    from datetime import datetime
    from dashboard.session import determine_status
    
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

        st.markdown("""
        <div style="background: rgba(255, 59, 48, 0.1); border: 1px solid #FF3B30; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
            <h3 style="color:#FF3B30; margin:0;">SCANNER ARMED</h3>
            <p style="color:white; margin:0; padding-top:4px;">Camera is active — faces will be detected automatically. Press 'q' to stop.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- START ATTENDANCE ---
        if st.button("Start Attendance", use_container_width=True):
            import cv2
            import face_recognition
            import numpy as np
            import os
            import pickle
            from enrollment.enroll_face import load_face_encodings
            
            st.info("Camera window opening... Press 'q' to stop.")
            
            session_info = get_session_by_id(session_id)
            if not session_info:
                st.error("Session not found.")
                return
            
            subject_students = get_students_in_subject(session_info['subject_id'])
            if not subject_students:
                st.warning("No students enrolled in this subject.")
                return
            
            # Load encodings for enrolled students
            student_encodings = {}
            student_info = {}
            for s in subject_students:
                enc = load_face_encodings(s['id'])
                if enc is not None:
                    student_encodings[s['id']] = np.array(enc)
                    student_info[s['id']] = {
                        'reg_no': s['reg_no'],
                        'first_name': s['first_name'],
                        'last_name': s['last_name']
                    }
            
            if not student_encodings:
                st.warning("No face encodings found for enrolled students. Please enroll faces first.")
                return
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("Camera could not be opened.")
                return
            
            marked_students = set()
            frame_counter = 0
            FRAME_SKIP = 2
            SCALE_FACTOR = 0.5
            UPSAMPLE = 0
            TOLERANCE = 0.4
            
            window_name = "Attendance Scanner - Press 'q' to stop"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 640, 480)
            
            st.info(f"Students enrolled: {len(student_encodings)}. Starting attendance...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame = cv2.flip(frame, 1)
                frame_counter += 1
                
                if frame_counter % FRAME_SKIP == 0:
                    small = cv2.resize(frame, (0, 0), fx=SCALE_FACTOR, fy=SCALE_FACTOR)
                    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                    
                    locations = face_recognition.face_locations(rgb, number_of_times_to_upsample=UPSAMPLE)
                    encodings = face_recognition.face_encodings(rgb, locations)
                    
                    for (top, right, bottom, left), face_encoding in zip(locations, encodings):
                        top, right, bottom, left = [int(v / SCALE_FACTOR) for v in (top, right, bottom, left)]
                        
                        best_match_id = None
                        best_distance = 1.0
                        
                        # Check against ALL students (even if already marked)
                        for student_id, known_encoding in student_encodings.items():
                            matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=TOLERANCE)
                            if True in matches:
                                distance = face_recognition.face_distance([known_encoding], face_encoding)[0]
                                if distance < best_distance:
                                    best_distance = distance
                                    best_match_id = student_id
                        
                        # Show name ALWAYS (whether marked or not)
                        if best_match_id is not None:
                            info = student_info[best_match_id]
                            label = f"{info['first_name']} {info['last_name']}"
                            
                            # Mark attendance only if not already marked
                            if best_match_id not in marked_students:
                                now = datetime.now()
                                status = determine_status(start_time)
                                mark_attendance(session_id, best_match_id, status, marked_by='face')
                                marked_students.add(best_match_id)
                                st.success(f"✅ Marked present: {info['first_name']} {info['last_name']} ({info['reg_no']})")
                        else:
                            label = "Unknown"
                        
                        # Draw rectangle
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        
                        # Show name ALWAYS
                        cv2.putText(frame, label, (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    cv2.putText(frame, f"Faces: {len(locations)} | Marked: {len(marked_students)}/{len(student_encodings)}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow(window_name, frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            st.success(f"✅ Attendance completed! Marked {len(marked_students)} students present.")

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
                        r_copy['Student Name'] = f"{r_copy['first_name']} {r_copy['last_name']}"
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
    st.markdown("<h1>Reports and Downloads</h1>", unsafe_allow_html=True)
    
    admin = st.session_state.admin
    subjects = get_subjects_by_admin(admin['id'])
    
    if not subjects:
        st.info("No course modules available.")
        return

    # --- SUBJECT SELECTOR ---
    subject_options = {f"{s['course_code']} - {s['course_title']}": s['id'] for s in subjects}
    selected_label = st.selectbox("Select Course Module", list(subject_options.keys()))
    selected_subject_id = subject_options[selected_label]

    # --- GET LATEST SESSION ---
    from database.db import get_connection as get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, start_time, end_time 
        FROM sessions 
        WHERE subject_id = %s 
        ORDER BY id DESC 
        LIMIT 1
    """, (selected_subject_id,))
    
    latest_session = cursor.fetchone()
    conn.close()

    if not latest_session:
        st.info("No attendance sessions found for this course.")
        return

    session_id = latest_session[0]
    session_date = latest_session[1]
    start_time = latest_session[2]
    end_time = latest_session[3]

    # --- FORMAT TIME ---
    if hasattr(start_time, 'strftime'):
        start_time_display = start_time.strftime('%I:%M %p')
        start_time_file = start_time.strftime('%H-%M')
    else:
        start_time_display = str(start_time)
        start_time_file = str(start_time).replace(':', '-')

    if end_time and hasattr(end_time, 'strftime'):
        end_time_display = end_time.strftime('%I:%M %p')
    else:
        end_time_display = 'In Progress'

    # --- DISPLAY SESSION INFO ---
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 20px 25px; border-radius: 12px; border: 1px solid rgba(212, 175, 55, 0.3); margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h3 style="margin: 0; color: #D4AF37; font-weight: 600;">Attendance Report</h3>
                <p style="margin: 5px 0 0 0; color: #A0AAB5; font-size: 0.95rem;">
                    <span style="color: #FFFFFF;">Course:</span> {selected_label}
                </p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; color: #A0AAB5; font-size: 0.85rem;">
                    <span style="color: #FFFFFF;">Date:</span> {session_date}<br>
                    <span style="color: #FFFFFF;">Time:</span> {start_time_display} - {end_time_display}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- FETCH ATTENDANCE ---
    from database.db_queries import get_attendance_for_session
    records = get_attendance_for_session(session_id)

    if not records:
        st.info("No attendance records found for this session.")
        return

    # --- FORMAT DATA ---
    formatted_records = []
    for r in records:
        r_copy = dict(r)
        if 'first_name' in r_copy and 'last_name' in r_copy:
            r_copy['Student Name'] = f"{r_copy['first_name']} {r_copy['last_name']}"
        status = r_copy.get('status', '')
        if status == 'Present':
            r_copy['Status'] = '✅ Present'
        elif status == 'Absent':
            r_copy['Status'] = '❌ Absent'
        elif status == 'Late':
            r_copy['Status'] = '⏰ Late'
        else:
            r_copy['Status'] = status
        formatted_records.append(r_copy)

    df = pd.DataFrame(formatted_records)
    
    display_columns = ['Student Name', 'reg_no', 'Status']
    available_columns = [col for col in display_columns if col in df.columns]
    
    st.dataframe(
        df[available_columns], 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Student Name": st.column_config.TextColumn("Student Name", width="large"),
            "reg_no": st.column_config.TextColumn("Registration No", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        }
    )

    # --- SUMMARY STATS ---
    present_count = len(df[df['status'] == 'Present']) if 'status' in df.columns else 0
    absent_count = len(df[df['status'] == 'Absent']) if 'status' in df.columns else 0
    late_count = len(df[df['status'] == 'Late']) if 'status' in df.columns else 0
    total_count = len(df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Students", total_count)
    with col2:
        st.metric("Present", present_count, delta=f"{present_count/total_count*100:.0f}%" if total_count > 0 else "0%")
    with col3:
        st.metric("Absent", absent_count)
    with col4:
        st.metric("Late", late_count)

    # --- DOWNLOAD BUTTON ---
    st.markdown("---")
    
    csv_data = []
    for r in records:
        name = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
        csv_data.append({
            'Registration No': r.get('reg_no', ''),
            'Student Name': name,
            'Status': r.get('status', ''),
            'Date': session_date,
            'Time': start_time_display
        })
    
    df_csv = pd.DataFrame(csv_data)
    csv = df_csv.to_csv(index=False)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="Download Attendance Report (CSV)",
            data=csv,
            file_name=f"attendance_{selected_label.replace(' ', '_')}_{session_date}_{start_time_file}.csv",
            mime="text/csv",
            use_container_width=True
        )

# --- PAGE: CAMERA TEST ---
def show_camera_test():
    st.markdown("<h1>Camera Check</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="dash-card" style="border-left-color: #007AFF;">
        <h3 style="margin:0;">Multi-Face Recognition Test</h3>
        <p style="color:#A0AAB5;">This will detect multiple faces and show names. Press 'q' to close.</p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    if st.button("Open Camera Test", use_container_width=True):
        import cv2
        import face_recognition
        import numpy as np
        import os
        import pickle
        from database.db_queries import get_all_students
        
        # --- LOAD ALL STUDENT ENCODINGS ---
        encodings_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'encodings')
        students = get_all_students()
        
        known_encodings = []
        known_names = []
        known_regs = []
        known_ids = []
        
        for s in students:
            filepath = os.path.join(encodings_dir, f"{s['id']}.pkl")
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    enc = pickle.load(f)
                    known_encodings.append(enc)
                    known_names.append(f"{s['first_name']} {s['last_name']}")
                    known_regs.append(s['reg_no'])
                    known_ids.append(s['id'])
        
        st.info(f"Loaded {len(known_encodings)} face encodings. Press 'q' to quit.")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("❌ Camera could not be opened.")
        else:
            st.success("✅ Camera opened! Look for a separate window.")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Flip for selfie view
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect all faces
                face_locations = face_recognition.face_locations(rgb)
                face_encodings = face_recognition.face_encodings(rgb, face_locations)
                
                # Process each face found
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    name = "Unknown"
                    reg_no = ""
                    
                    # Compare with known faces
                    if known_encodings:
                        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                        
                        if True in matches:
                            # Get the first match
                            match_index = matches.index(True)
                            name = known_names[match_index]
                            reg_no = known_regs[match_index]
                    
                    # Draw green rectangle
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    
                    # Draw name and roll number
                    if reg_no:
                        label = f"{name} ({reg_no})"
                        cv2.putText(frame, label, (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, "Unknown", (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Show face count
                cv2.putText(frame, f"Faces Detected: {len(face_locations)}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                cv2.imshow("Face Recognition - Press q to quit", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            st.success("✅ Camera test complete.")
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