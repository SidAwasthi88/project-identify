# admin 1 password 1
import streamlit as st
import sys
import os
import pandas as pd
import base64

sys.path.append(os.path.dirname(__file__))

from database.db import init_db
from database.db_queries import login_admin, add_student, get_all_students
from enrollment.enroll_face import enroll_face_for_student


BACKGROUND_URL = "images/KU.jpg"

LOGO_URL = "images/logo.png"

# ============================================================

# Initialize database
init_db()

# Page setup
st.set_page_config(page_title="Project Identify", layout="wide")

# Session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.admin = None


def set_background():
   
    """Set background image with dim overlay for better text visibility"""
    
    # Check if it's a URL or local file
    if BACKGROUND_URL.startswith("http"):
        # It's a web URL
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: 
                    linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
                    url("{BACKGROUND_URL}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            .stApp > header {{
                background-color: transparent !important;
            }}
            .stApp, .stMarkdown, .stTextInput, .stSelectbox, .stButton, .stDataFrame, .stTabs {{
                color: white !important;
            }}
            .stTextInput > div > div > input {{
                background-color: rgba(255, 255, 255, 0.15) !important;
                color: white !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
            }}
            .stSelectbox > div > div {{
                background-color: rgba(255, 255, 255, 0.15) !important;
                color: white !important;
            }}
            .stButton > button {{
                background-color: rgba(255, 255, 255, 0.2) !important;
                color: white !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
            }}
            .stButton > button:hover {{
                background-color: rgba(255, 255, 255, 0.35) !important;
            }}
            .stDataFrame {{
                background-color: rgba(0, 0, 0, 0.5) !important;
                border-radius: 10px;
                padding: 10px;
            }}
            .stTabs [data-baseweb="tab"] {{
                color: white !important;
            }}
            .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
            }}
            .stAlert {{
                background-color: rgba(0, 0, 0, 0.6) !important;
                color: white !important;
            }}
            .stSidebar {{
                background-color: rgba(0, 0, 0, 0.8) !important;
            }}
            .stSidebar .stMarkdown, .stSidebar .stTextInput {{
                color: white !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        # It's a local file
        try:
            with open(BACKGROUND_URL, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: 
                        linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
                        url("data:image/jpeg;base64,{img_base64}");
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
                .stApp > header {{
                    background-color: transparent !important;
                }}
                .stApp, .stMarkdown, .stTextInput, .stSelectbox, .stButton, .stDataFrame, .stTabs {{
                    color: white !important;
                }}
                .stTextInput > div > div > input {{
                    background-color: rgba(255, 255, 255, 0.15) !important;
                    color: white !important;
                    border: 1px solid rgba(255, 255, 255, 0.3) !important;
                }}
                .stSelectbox > div > div {{
                    background-color: rgba(255, 255, 255, 0.15) !important;
                    color: white !important;
                }}
                .stButton > button {{
                    background-color: rgba(255, 255, 255, 0.2) !important;
                    color: white !important;
                    border: 1px solid rgba(255, 255, 255, 0.3) !important;
                }}
                .stButton > button:hover {{
                    background-color: rgba(255, 255, 255, 0.35) !important;
                }}
                .stDataFrame {{
                    background-color: rgba(0, 0, 0, 0.5) !important;
                    border-radius: 10px;
                    padding: 10px;
                }}
                .stTabs [data-baseweb="tab"] {{
                    color: white !important;
                }}
                .stTabs [data-baseweb="tab-list"] {{
                    gap: 8px;
                }}
                .stAlert {{
                    background-color: rgba(0, 0, 0, 0.6) !important;
                    color: white !important;
                }}
                .stSidebar {{
                    background-color: rgba(0, 0, 0, 0.8) !important;
                }}
                .stSidebar .stMarkdown, .stSidebar .stTextInput {{
                    color: white !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
        except FileNotFoundError:
            pass


def login_page():
    """Show login form"""
    set_background()
    
    # Display logo on login page
    st.image(LOGO_URL, width=150)
    
    st.title("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            admin = login_admin(username, password)
            if admin:
                st.session_state.logged_in = True
                st.session_state.admin = admin
                st.rerun()
            else:
                st.error("Invalid username or password")


def show_students():
    """Student management page"""
    st.title("Students")
    
    tab_all, tab_add, tab_face = st.tabs(["All Students", "Add Student", "Face Enrollment"])
    
    # Tab 1: View all students
    with tab_all:
        students = get_all_students()
        if students:
            st.dataframe(pd.DataFrame(students), use_container_width=True)
        else:
            st.info("No students found. Add one using the 'Add Student' tab.")
    
    # Tab 2: Add new student
    with tab_add:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name *")
                last_name = st.text_input("Last Name *")
                middle_name = st.text_input("Middle Name")
                reg_no = st.text_input("Registration Number *")
            
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])
                program = st.selectbox("Program", ["BBA", "BBIS", "Transfer"])
                year = st.selectbox("Year", ["First", "Second", "Third", "Fourth"])
                semester = st.selectbox("Semester", ["First", "Second"])
            
            submitted = st.form_submit_button("Add Student")
            
            if submitted:
                if not first_name or not last_name or not reg_no:
                    st.error("Please fill all required fields (*).")
                else:
                    success = add_student(
                        reg_no, last_name, first_name, middle_name,
                        gender, program, year, semester
                    )
                    if success:
                        st.success(f"Student {first_name} {last_name} added successfully!")
                        st.rerun()
                    else:
                        st.error("Registration number already exists. Please use a unique Reg No.")
    
    # Tab 3: Face enrollment
    with tab_face:
        students = get_all_students()
        pending = [s for s in students if not s.get('face_enrolled')]
        
        st.write(f"**Pending enrollment:** {len(pending)} students")
        
        if pending:
            student_options = {
                f"{s['reg_no']} - {s['last_name']}, {s['first_name']}": s['id']
                for s in pending
            }
            
            selected = st.selectbox("Select student for face enrollment", list(student_options.keys()))
            
            if st.button("Start Face Enrollment"):
                with st.spinner("Opening camera... Please look at the camera."):
                    success = enroll_face_for_student(student_options[selected])
                
                if success:
                    st.success("Face enrolled successfully!")
                    st.rerun()
                else:
                    st.error("Face enrollment failed. Please try again.")
        else:
            st.success("All students have face enrollment completed.")


def main():
    """Main app controller"""
    if not st.session_state.logged_in:
        login_page()
        return
    
    set_background()
    
    # Sidebar
    st.sidebar.image(LOGO_URL, use_container_width=True)
    st.sidebar.title("Project Identify")
    st.sidebar.write(f"**Logged in as:** {st.session_state.admin['full_name']}")
    
    menu = st.sidebar.radio("Menu", ["Dashboard", "Students"])
    
    if menu == "Dashboard":
        st.title("Dashboard")
        
        # Simple stats
        students = get_all_students()
        total = len(students)
        enrolled = len([s for s in students if s.get('face_enrolled')])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", total)
        col2.metric("Face Enrolled", enrolled)
        col3.metric("Pending", total - enrolled)
        
        st.info("Use the 'Students' section to manage students and enroll faces.")
    
    else:
        show_students()
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.admin = None
        st.rerun()


if __name__ == "__main__":
    main()
