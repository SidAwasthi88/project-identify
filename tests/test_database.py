import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from database.db_queries import *

def test_admin():
    assert add_admin('test', 'pass', 'Tester') == True
    assert login_admin('test', 'pass') is not None
    assert login_admin('test', 'wrong') is None
    print("✅ Admin tests passed")

def test_student():
    assert add_student('T001', 'Doe', 'John', '', 'Male', 'BBA', 'First', 'First') == True
    assert add_student('T001', 'Doe', 'Jane', '', 'Female', 'BBA', 'First', 'First') == False
    assert len(get_all_students()) > 0
    print("✅ Student tests passed")

def test_subject():
    admin = login_admin('test', 'pass')
    add_subject('T101', 'Test Subject', 'BBA', 'First', 'First', admin['id'])
    assert len(get_subjects_by_admin(admin['id'])) > 0
    print("✅ Subject tests passed")

def test_session():
    admin = login_admin('test', 'pass')
    sub = get_subjects_by_admin(admin['id'])[0]
    sid = start_session(sub['id'], admin['id'], '2026-07-01', '09:00:00')
    assert sid is not None
    stu = get_all_students()[0]
    mark_attendance(sid, stu['id'], 'Present', 'face')
    recs = get_attendance_for_session(sid)
    assert len(recs) > 0
    end_session(sid, '10:00:00')
    print("✅ Session tests passed")

if __name__ == "__main__":
    test_admin()
    test_student()
    test_subject()
    test_session()
    print("\n🎉 All tests passed!")