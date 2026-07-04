import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from recognition.recognize import recognize_student

if __name__ == '__main__':
    attempt = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    student_id = recognize_student(attempt=attempt)
    if student_id is not None:
        print(str(student_id))
    else:
        print("NONE")
