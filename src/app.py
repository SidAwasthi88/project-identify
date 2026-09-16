import os
import sys
import base64
import pandas as pd
from datetime import datetime

import streamlit as st

# PATH SETUP
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))


# PAGE ICON
def _find_page_icon():
    candidates = [
        os.path.join(PROJECT_ROOT, "images", "favicon_logo.ico"),
        os.path.join(PROJECT_ROOT, "images", "logo.png"),
        os.path.join(CURRENT_DIR, "..", "images", "favicon_logo.ico"),
        os.path.join(CURRENT_DIR, "..", "images", "logo.png"),
        os.path.join("images", "favicon_logo.ico"),
        os.path.join("images", "logo.png"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return "🛡️"


# BACKEND IMPORTS
from database.db import init_db
from database.db_queries import (
    login_admin, add_admin, get_all_admins,
    add_subject, remove_subject, get_subjects_by_admin,
    remove_student, get_all_students,
    enroll_student_in_subject, remove_student_from_subject,
    get_students_in_subject, get_attendance_for_session,
)
from dashboard.session import begin_session, close_session, manually_mark_student
from enrollment.enroll_student import enroll_new_student
from enrollment.enroll_face import enroll_face_for_student
from recognition.scan_attendance import run_live_attendance
from recognition.camera_test import run_camera_test

init_db()

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Project IDentify",
    page_icon=_find_page_icon(),
    layout="wide",
)

st.markdown("""
    <style>
    div[data-testid="stSidebar"] [data-testid="stElementContainer"],
    div[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        width: 100% !important;
    }
    div[data-testid="stSidebar"] [data-testid="stButton"],
    div[data-testid="stSidebar"] [data-testid="stButton"] > button {
        width: 100% !important;
        display: block !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stSidebar"] .stMarkdown a,
    div[data-testid="stSidebar"] .stMarkdown div {
        width: 100% !important;
        box-sizing: border-box !important;
        display: block !important;
    }
    </style>
""", unsafe_allow_html=True)

# SESSION STATE
defaults = {
    "logged_in": False,
    "admin": None,
    "active_session_id": None,
    "active_session_start": None,
    "active_subject_id": None,
    "menu_open": True,
    "last_page": "Dashboard",
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

PAGES = [
    "Dashboard", "My Subjects", "Student Directory",
    "Live Attendance", "Camera Check", "Reports & Downloads", "Admin Settings",
]

# HELPERS
def find_image(name: str):
    for p in (
        os.path.join(PROJECT_ROOT, "images", name),
        os.path.join(CURRENT_DIR, "..", "images", name),
        os.path.join("images", name),
    ):
        if os.path.exists(p):
            return p
    return None


def full_name(s: dict) -> str:
    first = (s.get("first_name") or "").strip()
    middle = (s.get("middle_name") or "").strip()
    last = (s.get("last_name") or "").strip()
    return f"{first} {middle} {last}".replace("  ", " ").strip()


def initials(name: str) -> str:
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()


# THEME CSS
def inject_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    .stApp {
        background: #FDFBF7 !important;
        color: #2B1810 !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
    }

    header[data-testid="stHeader"] { background: transparent !important; }
    .stAppDeployButton, [data-testid="stToolbar"], #MainMenu, footer { display: none !important; }

    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] button {
        display: none !important;
    }

    h1, h2, h3, h4 {
        color: #7B1E1E !important;
        font-family: 'Playfair Display', Georgia, serif !important;
        font-weight: 600 !important;
    }
    p, span, label, li { color: #2B1810; }
    hr { border: none !important; border-top: 1px solid #EDE4D3 !important; margin: 20px 0 !important; }

    .section-label {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 1.4px !important;
        color: #A89A85 !important;
        text-transform: uppercase !important;
        margin-bottom: 4px !important;
    }

    .live-badge {
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        background: #0F4C3A !important;
        color: #E8F5EC !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.4px !important;
    }

    .top-bar {
        background: #FFFFFF !important;
        border: 1px solid #EDE4D3 !important;
        border-radius: 12px !important;
        padding: 14px 22px !important;
        margin-bottom: 22px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
        min-height: 60px !important;
    }

    .dash-card {
        background: #FFFFFF !important;
        border: 1px solid #EDE4D3 !important;
        border-radius: 12px !important;
        padding: 20px 22px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .dash-card:hover {
        box-shadow: 0 4px 12px rgba(123,30,30,0.08) !important;
    }

    /* ── DEFAULT / PRIMARY BUTTONS (main content area) ── */
    .stButton > button,
    [data-testid="stFormSubmitButton"] > button,
    .stDownloadButton > button {
        background: #7B1E1E !important;
        color: #FAF6F0 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.2rem !important;
        min-width: auto !important;
        height: auto !important;
        white-space: nowrap !important;
        box-shadow: 0 2px 6px rgba(123,30,30,0.18) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button *,
    [data-testid="stFormSubmitButton"] > button *,
    .stDownloadButton > button * {
        color: #FAF6F0 !important;
        white-space: nowrap !important;
    }
    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover,
    .stDownloadButton > button:hover {
        background: #5C1212 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(123,30,30,0.28) !important;
    }

    .toggle-btn-wrap div[data-testid="stButton"] button {
        min-width: 42px !important;
        min-height: 42px !important;
        width: 42px !important;
        height: 42px !important;
        padding: 0 !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        background: #FFFFFF !important;
        color: #7B1E1E !important;
        border: 1px solid #EDE4D3 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    .toggle-btn-wrap div[data-testid="stButton"] button * { color: #7B1E1E !important; }
    .toggle-btn-wrap div[data-testid="stButton"] button:hover { background: #7B1E1E !important; }
    .toggle-btn-wrap div[data-testid="stButton"] button:hover * { color: #FAF6F0 !important; }

    section[data-testid="stSidebar"] {
        background-color: #FAF6F0 !important;
        border-right: 1px solid #EDE4D3 !important;
    }
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div {
        background-color: #FAF6F0 !important;
    }

    /* kill every default gap in the sidebar */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div,
    section[data-testid="stSidebar"] [data-testid="stElementContainer"] {
        gap: 0 !important;
        row-gap: 0 !important;
        column-gap: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stButton"],
    section[data-testid="stSidebar"] [data-testid="stButton"] > button {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        min-height: 40px !important;
        height: auto !important;
        box-sizing: border-box !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        transform: none !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        margin: 0 0 2px 0 !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] > button > div,
    section[data-testid="stSidebar"] [data-testid="stButton"] > button p {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        margin: 0 !important;
    }

    /* Inactive nav buttons (secondary) */
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"] {
        background: transparent !important;
        color: #2B1810 !important;
        border: 1px solid transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"] p {
        color: #2B1810 !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"]:hover {
        background: rgba(123,30,30,0.08) !important;
        border-color: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"]:hover p {
        color: #7B1E1E !important;
    }

    /* Active nav button (primary) */
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {
        background: #7B1E1E !important;
        color: #FAF6F0 !important;
        border: 1px solid #7B1E1E !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] p {
        color: #FAF6F0 !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"]:hover {
        background: #5C1212 !important;
        border-color: #5C1212 !important;
    }

    /* Sign-out button (targeted by key) */
    section[data-testid="stSidebar"] [data-testid="stButton"]:has(button[class*="signout"]) button,
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[class*="signout"] {
        background: transparent !important;
        border: 1px solid #7B1E1E !important;
        color: #7B1E1E !important;
        justify-content: center !important;
        text-align: center !important;
        font-weight: 600 !important;
        margin-top: 8px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"]:has(button[class*="signout"]) button p,
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[class*="signout"] p {
        color: #7B1E1E !important;
        text-align: center !important;
        justify-content: center !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"]:has(button[class*="signout"]) button:hover,
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[class*="signout"]:hover {
        background: #7B1E1E !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"]:has(button[class*="signout"]) button:hover p,
    section[data-testid="stSidebar"] [data-testid="stButton"] > button[class*="signout"]:hover p {
        color: #FAF6F0 !important;
    }

    input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] > div {
        background-color: #FFFFFF !important;
        color: #2B1810 !important;
        border: 1px solid #E0D5C0 !important;
        border-radius: 8px !important;
    }

    .block-container {
        max-width: 1280px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)


# LOGIN
def page_login():
    inject_theme()
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        logo = find_image("logo.png")
        if logo:
            b64 = base64.b64encode(open(logo, "rb").read()).decode()
            st.markdown(
                f'<div style="display:flex;justify-content:center;margin-bottom:12px;">'
                f'<img src="data:image/png;base64,{b64}" style="width:120px;"></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            "<h2 style='text-align:center;margin-bottom:0;color:#7B1E1E;'>"
            "Project <span style='color:#B8860B;'>IDentify</span></h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center;color:#7B6A55;margin-bottom:22px;font-size:0.95rem;'>"
            "Biometric Attendance Management System</p>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            u = st.text_input("Administrator Handle", placeholder="Enter username")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("AUTHENTICATE SYSTEM ACCESS", use_container_width=True):
                admin = login_admin(u.strip(), p.strip())
                if admin:
                    st.session_state.logged_in = True
                    st.session_state.admin = admin
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid username or password.")

# HEADER + SIDEBAR
def top_bar_and_sidebar():
    admin = st.session_state.admin

    st.markdown("""
    <style>
    [data-testid="stSidebarHeader"] {
        display: none !important;
        height: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
    }
    [data-testid="stSidebarContent"] { padding-top: 0.5rem !important; }
    [data-testid="stSidebarUserContent"] { padding-top: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.menu_open:
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 280px !important;
            min-width: 280px !important;
            display: flex !important;
            visibility: visible !important;
            z-index: 99999 !important;
            transform: translateX(0) !important;
        }
        [data-testid="stAppViewContainer"] { margin-left: 280px !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
        }
        [data-testid="stAppViewContainer"] { margin-left: 0 !important; }
        </style>
        """, unsafe_allow_html=True)

    with st.sidebar:
        logo = find_image("logo.png")
        sb_col1, sb_col2 = st.columns([5, 1], vertical_alignment="center")
        with sb_col1:
            if logo:
                b64_logo = base64.b64encode(open(logo, "rb").read()).decode()
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <img src="data:image/png;base64,{b64_logo}" style="width: 42px; height: 42px; object-fit: contain;">
                        <div style="line-height: 1.15;">
                            <span style="font-family: 'Playfair Display', Georgia, serif; font-weight: 700; font-size: 0.95rem; color: #7B1E1E; display: block;">Kathmandu</span>
                            <span style="font-family: 'Playfair Display', Georgia, serif; font-weight: 600; font-size: 0.85rem; color: #2B1810; display: block;">University</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        with sb_col2:
            if st.button("«", key="sb_close", help="Collapse sidebar"):
                st.session_state.menu_open = False

        profile_html = (
            f'<div style="background:#FFFFFF;border:1px solid #EDE4D3;border-radius:10px;'
            f'padding:10px 12px;margin:12px 0 16px 0;display:flex;align-items:center;gap:10px;">'
            f'<div style="width:36px;height:36px;border-radius:50%;background:#7B1E1E;color:#FAF6F0;'
            f'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.8rem;">'
            f'{initials(admin["full_name"])}</div>'
            f'<div style="line-height:1.2;">'
            f'<div style="color:#2B1810;font-weight:600;font-size:0.85rem;">{admin["full_name"]}</div>'
            f'<div style="color:#A89A85;font-size:0.7rem;">Faculty Administrator</div>'
            f'</div></div>'
        )
        st.markdown(profile_html, unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # ── Button-based navigation ──
        if st.session_state.get("last_page") not in PAGES:
            st.session_state["last_page"] = "Dashboard"

        current = st.session_state["last_page"]
        for p in PAGES:
            is_active = (p == current)
            if st.button(
                p,
                key=f"nav_{p}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["last_page"] = p
                st.rerun()

        if st.button("↪  Sign out", key="signout_btn", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.admin = None
            st.session_state.active_session_id = None
            st.rerun()

    badge = "<span class='live-badge'>● LIVE TRACKING</span>" if st.session_state.active_session_id else ""
    header_box = (
        f'<div class="top-bar">'
        f'<div style="display:flex;align-items:center;gap:14px;">'
        f'<span style="font-size:1.15rem;font-weight:700;color:#7B1E1E;'
        f'font-family:\'Playfair Display\',serif;">'
        f'Project <span style="color:#B8860B;">Identify</span></span>{badge}'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<span style="color:#A89A85;font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;">'
        f'Authorized Admin</span><br>'
        f'<span style="color:#2B1810;font-weight:600;font-size:0.9rem;">{admin["full_name"]}</span>'
        f'</div></div>'
    )

    if not st.session_state.menu_open:
        toggle_col, header_col = st.columns([0.5, 20], gap="small")
        with toggle_col:
            st.markdown("<div class='toggle-btn-wrap'>", unsafe_allow_html=True)
            if st.button("»", key="sb_open", help="Expand sidebar"):
                st.session_state.menu_open = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with header_col:
            st.markdown(header_box, unsafe_allow_html=True)
    else:
        st.markdown(header_box, unsafe_allow_html=True)

    # Return the currently selected page (from state, not a local variable)
    return st.session_state.get("last_page", "Dashboard")


# PAGE: DASHBOARD
def page_dashboard():
    admin = st.session_state.admin
    st.markdown("<p class='section-label'>Faculty Overview · Even Semester 2082</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='margin:0;'>Welcome back, {admin['full_name']}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#7B6A55;margin-top:6px;'>Here's what's happening across your subjects today.</p>",
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    subjects = get_subjects_by_admin(admin["id"])
    students = get_all_students()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="dash-card">'
            f'<p class="section-label" style="margin:0;">My Subjects</p>'
            f'<h3 style="margin:6px 0 0;font-size:2.2rem;">{len(subjects)}</h3>'
            f'<p style="color:#A89A85;margin:2px 0 0;font-size:0.85rem;">courses</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="dash-card">'
            f'<p class="section-label" style="margin:0;">Total Students</p>'
            f'<h3 style="margin:6px 0 0;font-size:2.2rem;">{len(students)}</h3>'
            f'<p style="color:#A89A85;margin:2px 0 0;font-size:0.85rem;">enrolled</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        active = bool(st.session_state.active_session_id)
        color = "#2D7A4F" if active else "#7B1E1E"
        note = "● Tracking" if active else "● Ready to start"
        note_color = "#2D7A4F" if active else "#A89A85"
        st.markdown(
            f'<div class="dash-card">'
            f'<p class="section-label" style="margin:0;">Active Session</p>'
            f'<h3 style="color:{color};margin:6px 0 0;font-size:1.9rem;">{"Yes" if active else "No"}</h3>'
            f'<p style="color:{note_color};margin:2px 0 0;font-size:0.85rem;">{note}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if subjects:
        st.markdown("<br><h3 style='margin-bottom:12px;'>My Subjects</h3>", unsafe_allow_html=True)
        for s in subjects:
            code_tail = s["course_code"][-3:] if len(s["course_code"]) >= 3 else s["course_code"]
            st.markdown(
                f'<div class="dash-card" style="margin-bottom:14px;">'
                f'<div style="display:flex;align-items:center;gap:14px;">'
                f'<div style="width:52px;height:52px;border-radius:10px;background:#F5EEE2;'
                f'display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;">'
                f'<span style="font-size:0.6rem;color:#8B6B14;font-weight:700;letter-spacing:0.5px;">SUB</span>'
                f'<span style="font-size:1rem;color:#7B1E1E;font-weight:700;">{code_tail}</span>'
                f'</div>'
                f'<div>'
                f'<p style="margin:0;color:#2B1810;font-size:1.05rem;font-weight:600;">{s["course_title"]}</p>'
                f'<p style="margin:4px 0 0 0;color:#A89A85;font-size:0.82rem;">'
                f'{s["program"]} · {s["year"]} Year, {s["semester"]} Semester</p>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )


# PAGE: SUBJECTS
def page_subjects():
    admin = st.session_state.admin
    st.markdown("<h1>Course Modules</h1>", unsafe_allow_html=True)

    with st.expander("REGISTER NEW COURSE MODULE"):
        with st.form("add_subject", clear_on_submit=True):
            c1, c2 = st.columns(2)
            code = c1.text_input("Course Code (e.g. GEM501)").strip()
            title = c2.text_input("Course Title").strip()
            c3, c4, c5 = st.columns(3)
            program = c3.selectbox("Program", ["BBA", "BBIS", "MBA"])
            year = c4.selectbox("Year", ["First", "Second", "Third", "Fourth"])
            semester = c5.selectbox("Semester", ["First", "Second"])
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("DEPLOY MODULE TO DATABASE"):
                if code and title:
                    add_subject(code, title, program, year, semester, admin["id"])
                    st.success(f"Module {code} initialized.")
                    st.rerun()
                else:
                    st.error("Please provide both Course Code and Title.")

    subjects = get_subjects_by_admin(admin["id"])
    if not subjects:
        st.info("No course modules currently assigned.")
        return

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0;'>Manage Active Modules</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#7B6A55;font-size:0.85rem;margin-bottom:16px;'>Active courses under your instruction.</p>", unsafe_allow_html=True)

        for s in subjects:
            c1, c2 = st.columns([5, 1], vertical_alignment="center")
            c1.markdown(
                f"<div style='line-height:1.3;'>"
                f"<strong style='color:#2B1810;font-size:1rem;'>{s['course_code']} — {s['course_title']}</strong><br>"
                f"<span style='color:#7B6A55;font-size:0.85rem;'>"
                f"{s['program']} · {s['year']} Year, {s['semester']} Sem</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if c2.button("Delete", key=f"del_subj_{s['id']}", use_container_width=True):
                remove_subject(s["id"])
                st.rerun()
            st.markdown("<hr style='margin:12px 0;opacity:0.5;'>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0;'>Student Roster</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#7B6A55;font-size:0.85rem;margin-bottom:12px;'>Manage student enrollment per course.</p>", unsafe_allow_html=True)

        opts = {f"{s['course_code']} - {s['course_title']}": s["id"] for s in subjects}
        sel = st.selectbox("Select Target Course", list(opts.keys()), key="roster_course_select")
        sid = opts[sel]

        enrolled = get_students_in_subject(sid)
        enrolled_ids = {x["id"] for x in enrolled}
        not_enrolled = [x for x in get_all_students() if x["id"] not in enrolled_ids]

        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Enrolled Students", "Available Students"])

        with t1:
            if enrolled:
                for x in enrolled:
                    c1, c2 = st.columns([5, 1], vertical_alignment="center")
                    c1.markdown(f"**{full_name(x)}** <span style='color:#7B6A55;font-size:0.85rem;'>({x['reg_no']})</span>", unsafe_allow_html=True)
                    if c2.button("Remove", key=f"un_{sid}_{x['id']}", use_container_width=True):
                        remove_student_from_subject(sid, x["id"])
                        st.rerun()
                    st.markdown("<hr style='margin:10px 0;opacity:0.4;'>", unsafe_allow_html=True)
            else:
                st.info("No students currently enrolled in this module.")

        with t2:
            if not_enrolled:
                for x in not_enrolled:
                    c1, c2 = st.columns([5, 1], vertical_alignment="center")
                    c1.markdown(f"**{full_name(x)}** <span style='color:#7B6A55;font-size:0.85rem;'>({x['reg_no']})</span>", unsafe_allow_html=True)
                    if c2.button("Enroll", key=f"en_{sid}_{x['id']}", use_container_width=True):
                        enroll_student_in_subject(sid, x["id"])
                        st.rerun()
                    st.markdown("<hr style='margin:10px 0;opacity:0.4;'>", unsafe_allow_html=True)
            else:
                st.info("All students are currently enrolled.")


# PAGE: STUDENTS
def page_students():
    st.markdown("<h1>Student Matrix</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["Active Directory", "Create Student Profile", "Biometric Facial Setup"])

    with t1:
        students = get_all_students()
        if not students:
            st.info("No students found.")
        else:
            df = pd.DataFrame([{
                "Registration No": s.get("reg_no", ""),
                "Full Name": full_name(s),
                "Gender": s.get("gender", ""),
                "Program": s.get("program", ""),
                "Year": s.get("year", ""),
                "Semester": s.get("semester", ""),
                "Face Status": "Verified" if s.get("face_enrolled") else "Pending",
            } for s in students])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total Students: {len(students)}")

            st.markdown("---")
            st.subheader("Delete Student")
            opts = {f"{s['reg_no']} - {full_name(s)}": s["id"] for s in students}
            pick = st.selectbox("Select Student to Delete", list(opts.keys()))
            if st.button("Delete Student", use_container_width=True):
                sid = opts[pick]
                enc = os.path.join(PROJECT_ROOT, "data", "encodings", f"{sid}.pkl")
                if os.path.exists(enc):
                    os.remove(enc)
                if remove_student(sid):
                    st.success("Student deleted.")
                    st.rerun()
                else:
                    st.error("Failed to delete.")

    with t2:
        with st.form("add_student"):
            c1, c2, c3 = st.columns(3)
            last = c1.text_input("Surname / Last Name *").strip()
            first = c2.text_input("First Name *").strip()
            middle = c3.text_input("Middle Name (Optional)").strip()
            c4, c5 = st.columns(2)
            reg = c4.text_input("Registration ID *").strip()
            gender = c5.selectbox("Gender", ["Male", "Female", "Other"])
            c6, c7, c8 = st.columns(3)
            program = c6.selectbox("Program", ["BBA", "BBIS", "MBA"])
            year = c7.selectbox("Year", ["First", "Second", "Third", "Fourth"])
            semester = c8.selectbox("Semester", ["First", "Second"])
            submitted = st.form_submit_button("Create Student Profile", use_container_width=True)

        if submitted:
            if not (reg and first and last):
                st.error("Please complete all required fields.")
            else:
                result = enroll_new_student(reg, last, first, middle, gender, program, year, semester)
                success = result[0] if isinstance(result, tuple) else bool(result)
                msg = result[1] if isinstance(result, tuple) and len(result) > 1 else (
                    "Student created." if success else "Registration ID already exists."
                )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with t3:
        st.markdown("### Biometric Facial Setup")
        students = get_all_students()
        pending = [s for s in students if not s.get("face_enrolled")]

        if not pending:
            st.success("All students have completed facial enrollment.")
            return

        opts = {f"{full_name(s)} ({s['reg_no']})": s["id"] for s in pending}
        pick = st.selectbox("Select Student for Face Enrollment", list(opts.keys()))
        st.info("Camera will open in a separate window. Press 'q' to cancel.")
        if st.button("Run Camera for Biometric Setup", use_container_width=True):
            with st.spinner("Opening camera feed..."):
                try:
                    result = enroll_face_for_student(opts[pick])
                    success = result[0] if isinstance(result, tuple) else bool(result)
                    msg = result[1] if isinstance(result, tuple) and len(result) > 1 else (
                        "Face enrolled." if success else "Face enrollment failed."
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"Error: {e}")


# PAGE: LIVE ATTENDANCE
def page_live():
    admin = st.session_state.admin
    st.markdown("<h1>Live Tracking</h1>", unsafe_allow_html=True)
    subjects = get_subjects_by_admin(admin["id"])

    if not st.session_state.active_session_id:
        if not subjects:
            st.warning("No course modules assigned to your account.")
            return

        st.markdown(
            '<div class="dash-card">'
            '<h3 style="margin:0;">Initiate Tracking Session</h3>'
            '<p style="color:#7B6A55;margin-top:6px;">'
            'Select the course module and enter your passphrase to activate the biometric scanner bridge.'
            '</p>'
            '</div><br>',
            unsafe_allow_html=True,
        )

        opts = {f"{s['course_code']} - {s['course_title']}": s["id"] for s in subjects}
        pick = st.selectbox("Select Target Course Module", list(opts.keys()))
        with st.form("start_session"):
            pw = st.text_input("Admin Passphrase", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("ENGAGE TRACKING SESSION"):
                sid = begin_session(opts[pick], admin["id"], admin["username"], pw)
                if sid:
                    st.session_state.active_session_id = sid
                    st.session_state.active_session_start = datetime.now().strftime("%H:%M:%S")
                    st.session_state.active_subject_id = opts[pick]
                    st.rerun()
                else:
                    st.error("Authentication rejected. Passphrase incorrect.")
        return

    session_id = st.session_state.active_session_id
    start_time = st.session_state.active_session_start

    st.markdown(
        '<div style="background:#FDF2F2;border:1px solid #7B1E1E;padding:18px 20px;border-radius:12px;'
        'text-align:center;margin-bottom:20px;">'
        '<h3 style="color:#7B1E1E;margin:0;">SCANNER ARMED</h3>'
        '<p style="color:#2B1810;margin:0;padding-top:4px;">'
        'Camera is active — faces will be detected automatically. Press \'q\' to stop.'
        '</p></div>',
        unsafe_allow_html=True,
    )

    if st.button("Start Attendance", use_container_width=True):
        st.info("Camera window opening... Press 'q' in the window to stop.")
        with st.spinner("Running recognition engine..."):
            try:
                marked_count = run_live_attendance(session_id, start_time)
                st.success(f"✅ Attendance scanner session finished. Marked {marked_count} student(s).")
            except Exception as e:
                st.error(f"Scanner runtime error: {e}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Manual Attendance Override")
    c1, c2 = st.columns(2)

    with c1:
        enrolled = get_students_in_subject(st.session_state.active_subject_id)
        if enrolled:
            opts = {f"{full_name(s)} ({s['reg_no']})": s["id"] for s in enrolled}
            pick = st.selectbox("Target Student", list(opts.keys()))
            status = st.selectbox("Status", ["Present", "Absent", "Late"])
            if st.button("FORCE RECORD UPDATE", use_container_width=True):
                manually_mark_student(session_id, opts[pick], status)
                st.success("Status updated.")
                st.rerun()

    with c2:
        st.markdown("### Live Session Logs")
        records = get_attendance_for_session(session_id)
        if records:
            rows = []
            for r in records:
                d = dict(r)
                d["Student Name"] = f"{d.get('first_name','')} {d.get('last_name','')}".strip()
                rows.append(d)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("end_session"):
        pw = st.text_input("Sign-off Passphrase", type="password")
        if st.form_submit_button("TERMINATE TRACKING SESSION"):
            if close_session(session_id, admin["username"], pw):
                st.session_state.active_session_id = None
                st.session_state.active_session_start = None
                st.session_state.active_subject_id = None
                st.rerun()
            else:
                st.error("Passphrase incorrect.")


# ─────────────────────────────────────────────────────────────
# PAGE: REPORTS
# ─────────────────────────────────────────────────────────────
def page_reports():
    st.markdown("<h1>Reports and Downloads</h1>", unsafe_allow_html=True)
    admin = st.session_state.admin
    subjects = get_subjects_by_admin(admin["id"])
    if not subjects:
        st.info("No course modules available.")
        return

    opts = {f"{s['course_code']} - {s['course_title']}": s["id"] for s in subjects}
    label = st.selectbox("Select Course Module", list(opts.keys()))
    sid = opts[label]

    from database.db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, date, start_time, end_time FROM sessions
        WHERE subject_id = %s ORDER BY id DESC LIMIT 1
    """, (sid,))
    row = cur.fetchone()
    conn.close()

    if not row:
        st.info("No attendance sessions found for this course.")
        return

    session_id, s_date, s_start, s_end = row
    start_disp = s_start.strftime("%I:%M %p") if hasattr(s_start, "strftime") else str(s_start)
    start_file = s_start.strftime("%H-%M") if hasattr(s_start, "strftime") else str(s_start).replace(":", "-")
    end_disp = s_end.strftime("%I:%M %p") if s_end and hasattr(s_end, "strftime") else "In Progress"

    st.markdown(
        f'<div style="background:#FFFFFF;padding:20px 25px;border-radius:12px;border:1px solid #EDE4D3;'
        f'margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,0.03);">'
        f'<div style="display:flex;justify-content:space-between;flex-wrap:wrap;">'
        f'<div>'
        f'<h3 style="margin:0;">Attendance Report</h3>'
        f'<p style="margin:5px 0 0 0;color:#7B6A55;font-size:0.95rem;">'
        f'<span style="color:#2B1810;">Course:</span> {label}</p></div>'
        f'<div style="text-align:right;">'
        f'<p style="margin:0;color:#7B6A55;font-size:0.85rem;">'
        f'<span style="color:#2B1810;">Date:</span> {s_date}<br>'
        f'<span style="color:#2B1810;">Time:</span> {start_disp} - {end_disp}</p>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    records = get_attendance_for_session(session_id)
    if not records:
        st.info("No attendance records found for this session.")
        return

    rows = []
    for r in records:
        d = dict(r)
        d["Student Name"] = f"{d.get('first_name','')} {d.get('last_name','')}".strip()
        status = d.get("status", "")
        d["Status"] = {"Present": "✅ Present", "Absent": "❌ Absent", "Late": "⏰ Late"}.get(status, status)
        rows.append(d)

    df = pd.DataFrame(rows)
    cols = [c for c in ["Student Name", "reg_no", "Status"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    present = len(df[df["status"] == "Present"]) if "status" in df.columns else 0
    absent = len(df[df["status"] == "Absent"]) if "status" in df.columns else 0
    late = len(df[df["status"] == "Late"]) if "status" in df.columns else 0
    total = len(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", total)
    c2.metric("Present", present, delta=f"{present/total*100:.0f}%" if total else "0%")
    c3.metric("Absent", absent)
    c4.metric("Late", late)

    st.markdown("---")
    csv_rows = [{
        "Registration No": r.get("reg_no", ""),
        "Student Name": f"{r.get('first_name','')} {r.get('last_name','')}".strip(),
        "Status": r.get("status", ""),
        "Date": s_date,
        "Time": start_disp,
    } for r in records]
    csv = pd.DataFrame(csv_rows).to_csv(index=False)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.download_button(
            "Download Attendance Report (CSV)",
            data=csv,
            file_name=f"attendance_{label.replace(' ', '_')}_{s_date}_{start_file}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ─────────────────────────────────────────────────────────────
# PAGE: CAMERA TEST
# ─────────────────────────────────────────────────────────────
def page_camera_test():
    st.markdown("<h1>Camera Check</h1>", unsafe_allow_html=True)
    st.markdown(
        '<div class="dash-card">'
        '<h3 style="margin:0;">Multi-Face Recognition Test</h3>'
        '<p style="color:#7B6A55;margin-top:6px;">'
        'Detects multiple faces and shows names. Press \'q\' in the camera window to close.'
        '</p></div><br>',
        unsafe_allow_html=True,
    )

    if st.button("Open Camera Test", use_container_width=True):
        with st.spinner("Opening diagnostic window..."):
            try:
                run_camera_test()
                st.success("✅ Diagnostic camera test ended.")
            except Exception as e:
                st.error(f"Error executing camera check: {e}")


# PAGE: ADMIN SETTINGS
def page_admin():
    st.markdown("<h1>Admin Settings</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["Active Administrators", "Authorize New Admin"])

    with t1:
        for a in get_all_admins():
            st.markdown(
                f"**{a['full_name']}**<br>"
                f"<span style='color:#B8860B;font-size:0.85rem;'>Username: {a['username']}</span>",
                unsafe_allow_html=True,
            )
            st.markdown("<hr style='opacity:0.4;'>", unsafe_allow_html=True)

    with t2:
        with st.form("add_admin"):
            user = st.text_input("Handle / Username").strip()
            name = st.text_input("Full Name").strip()
            pw = st.text_input("Initial Security Passphrase", type="password").strip()
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("AUTHORIZE NEW ADMIN"):
                if user and name and pw:
                    if add_admin(user, pw, name, created_by=st.session_state.admin["id"]):
                        st.success(f"Administrator '{user}' authorized.")
                    else:
                        st.error("Username already exists.")
                else:
                    st.error("All fields required.")


# MAIN ROUTER
def main():
    if not st.session_state.logged_in:
        page_login()
        return

    inject_theme()
    page = top_bar_and_sidebar()

    routes = {
        "Dashboard": page_dashboard,
        "My Subjects": page_subjects,
        "Student Directory": page_students,
        "Live Attendance": page_live,
        "Camera Check": page_camera_test,
        "Reports & Downloads": page_reports,
        "Admin Settings": page_admin,
    }
    routes.get(page, page_dashboard)()


if __name__ == "__main__":
    main()