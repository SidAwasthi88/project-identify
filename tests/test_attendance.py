import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dashboard.session import begin_session, close_session, manually_mark_student
from database.db_queries import *

def test_full_flow():
    add_admin('flowtest', 'pass', 'Flow Tester')
    admin = login_admin('flowtest', 'pass')
    add_subject('F101', 'Flow Subject', 'BBA', 'First', 'First', admin['id'])
    sub = get_subjects_by_admin(admin['id'])[0]
    add_student('F001', 'Test', 'Student', '', 'Male', 'BBA', 'First', 'First')
    stu = get_all_students()[0]
    enroll_student_in_subject(sub['id'], stu['id'])

    sid = begin_session(sub['id'], admin['id'], 'flowtest', 'pass')
    assert sid is not None

    manually_mark_student(sid, stu['id'], 'Present')
    recs = get_attendance_for_session(sid)
    assert any(r['status'] == 'Present' for r in recs)

    close_session(sid, 'flowtest', 'pass')
    print("✅ Full attendance flow test passed!")

if __name__ == "__main__":
    test_full_flow()