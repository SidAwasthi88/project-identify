import streamlit as st, sys, os, pandas as pd
sys.path.append(os.path.dirname(__file__))
from database.db import init_db
from database.db_queries import login_admin, add_student, get_all_students
from enrollment.enroll_face import enroll_face_for_student

init_db()
st.set_page_config(page_title="Project Identify", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.admin = None

def login_page():
    st.title("Login")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            a = login_admin(u, p)
            if a:
                st.session_state.logged_in = True
                st.session_state.admin = a
                st.rerun()
            else:
                st.error("Invalid")

def show_students():
    st.title("Students")
    t1, t2, t3 = st.tabs(["All", "Add", "Face Enrollment"])
    with t1:
        students = get_all_students()
        if students:
            st.dataframe(pd.DataFrame(students))
        else:
            st.info("No students.")
    with t2:
        with st.form("add"):
            last = st.text_input("Last Name*")
            first = st.text_input("First Name*")
            middle = st.text_input("Middle Name")
            reg = st.text_input("Reg No.*")
            gender = st.selectbox("Gender", ["Male","Female","Prefer not to say"])
            prog = st.selectbox("Program", ["BBA","BBIS","Transfer"])
            year = st.selectbox("Year", ["First","Second","Third","Fourth"])
            sem = st.selectbox("Semester", ["First","Second"])
            if st.form_submit_button("Add"):
                if not last or not first or not reg:
                    st.error("Required fields missing.")
                else:
                    ok = add_student(reg, last, first, middle, gender, prog, year, sem)
                    if ok:
                        st.success("Student added.")
                        st.rerun()
                    else:
                        st.error("Reg No. already exists.")
    with t3:
        students = get_all_students()
        pending = [s for s in students if not s['face_enrolled']]
        st.write(f"Pending: {len(pending)}")
        if pending:
            opts = {f"{s['reg_no']} - {s['last_name']} {s['first_name']}": s['id'] for s in pending}
            sel = st.selectbox("Student", list(opts.keys()))
            if st.button("Start Face Enrollment"):
                with st.spinner("Camera opening..."):
                    ok = enroll_face_for_student(opts[sel])
                if ok:
                    st.success("Face enrolled!")
                    st.rerun()
                else:
                    st.error("Failed. Try again.")

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        st.sidebar.write(f"**{st.session_state.admin['full_name']}**")
        page = st.sidebar.radio("Menu", ["Dashboard","Students"])
        if page == "Dashboard":
            st.title("Welcome")
        elif page == "Students":
            show_students()
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()