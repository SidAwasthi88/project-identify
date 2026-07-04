from database.db_queries import add_student

def get_group_label(program, year, semester):
    return f"{program} — {year} Year, {semester} Semester"

def enroll_new_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester):
    return add_student(reg_no, last_name, first_name, middle_name, gender, program, year, semester)