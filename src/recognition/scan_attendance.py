import sys
import os

# Ensure project root is in Python path for absolute/relative module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.recognition.recognize import recognize_student


def main():
    # Parse attempt argument passed from GUI / subprocess wrapper if present
    attempt = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    # Run face recognition loop
    student_id = recognize_student(attempt=attempt)

    # Print raw output to stdout for parent processes (e.g. Node/Electron, Tkinter subprocesses)
    if student_id is not None:
        print(str(student_id))
    else:
        print("NONE")


if __name__ == '__main__':
    main()