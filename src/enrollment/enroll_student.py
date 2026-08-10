import mysql.connector
from database.db_queries import add_student

# ─────────────────────────────────────────────
# UTILITY & FORMATTING HELPERS
# ─────────────────────────────────────────────

def get_group_label(program: str, year: str, semester: str) -> str:
    """Formats student cohort grouping into a clean readable string."""
    return f"{program} — {year} Year, {semester} Semester"


def sanitize_input(value: str) -> str:
    """Strips leading/trailing whitespace and normalizes empty inputs."""
    if value is None:
        return ""
    return str(value).strip()


# ─────────────────────────────────────────────
# STUDENT ENROLLMENT LOGIC
# ─────────────────────────────────────────────

def enroll_new_student(
    reg_no: str,
    last_name: str,
    first_name: str,
    middle_name: str,
    gender: str,
    program: str,
    year: str,
    semester: str,
    roll_no: int = None
):
    """
    Validates, sanitizes, and registers a new student entry in the database.

    Args:
        reg_no (str): Unique Registration / Identification Number.
        last_name (str): Student's surname.
        first_name (str): Student's primary given name.
        middle_name (str): Optional middle name.
        gender (str): Male, Female, or Prefer not to say.
        program (str): Academic Program (e.g., 'BBA', 'BBIS').
        year (str): Academic Year ('First', 'Second', 'Third', 'Fourth').
        semester (str): Academic Semester ('First', 'Second').
        roll_no (int, optional): Specific numeric roll number if available.

    Returns:
        (bool, str, int): (Success status, Message, Student ID if created or None)
    """
    # 1. Sanitize string inputs
    reg_no = sanitize_input(reg_no).upper()
    last_name = sanitize_input(last_name).title()
    first_name = sanitize_input(first_name).title()
    middle_name = sanitize_input(middle_name).title() if middle_name else None

    # 2. Basic Validation Rules
    if not reg_no:
        return False, "Registration Number is required.", None
    if not first_name or not last_name:
        return False, "First Name and Last Name are required.", None
    if not program or not year or not semester:
        return False, "Program, Year, and Semester must be selected.", None

    # 3. Database Insertion Execution
    try:
        student_id = add_student(
            reg_no=reg_no,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            gender=gender,
            program=program,
            year=year,
            semester=semester,
            roll_no=roll_no
        )
        group_tag = get_group_label(program, year, semester)
        return True, f"Student '{first_name} {last_name}' ({reg_no}) enrolled successfully in {group_tag}!", student_id

    except mysql.connector.Error as err:
        # Handle Duplicate Entry Error (ER_DUP_ENTRY = 1062)
        if err.errno == 1062:
            return False, f"A student with Registration No. '{reg_no}' already exists.", None
        return False, f"Database Error: {err}", None

    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}", None


if __name__ == "__main__":
    # Test execution example
    success, msg, sid = enroll_new_student(
        reg_no="REG-2026-001",
        last_name="Doe",
        first_name="Jane",
        middle_name="",
        gender="Female",
        program="BBIS",
        year="First",
        semester="First"
    )
    print(f"Status: {success} | ID: {sid} | Message: {msg}")