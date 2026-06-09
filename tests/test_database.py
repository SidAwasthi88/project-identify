import sys
import os

# For Python to find the src folder
sys.path.insert(0, os.path.join(os.path.dirname(_file_), '..', 'src'))

from database.db_queries import get_all_students, login_admin

def test_fetch_students():
    """Check that we can fetch the student list (even if it's empty)."""
    students = get_all_students()
    print(f"✅ Student query works. Found {len(students)} student(s).")
    for s in students:
        print(f"   - {s['reg_no']}: {s['last_name']} {s['first_name']} (face_enrolled={s['face_enrolled']})")

def test_admin_login():
    """Try to log in with the default admin (must exist)."""
    admin = login_admin("admin1", "password")
    if admin:
        print(f"✅ Admin login works. Welcome, {admin['Administrator 1']}!")
    else:
        print("⚠️ Admin login failed. Make sure you have created the admin account.")

if _name_ == "_main_":
    print("Running database tests…\n")
    test_fetch_students()
    test_admin_login()
    print("\nAll tests completed.")
