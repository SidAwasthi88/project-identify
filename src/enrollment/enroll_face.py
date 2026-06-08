import cv2
import face_recognition
import pickle #save python objects
import os
import sys

# Add parent directory to path so we can import database functions
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_queries import mark_face_enrolled, get_student_by_id

# Folder where face encodings will be saved
ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/embeddings')


def capture_face_encoding(student_name=""):
    # Open webcam, mirror feed, show green box, capture face encoding
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None

    window_name = f"Enrolling: {student_name} — Q to cancel"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    encoding = None
    while True:
        ret, frame = cap.read() # read one frame from webcam
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)

        for top, right, bottom, left in locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

         # Show on screen if a face is detected
        status = "Face found" if locations else "No face"
        cv2.putText(frame, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 0) if locations else (0, 0, 255), 2)
        cv2.imshow(window_name, frame)

        # If we see at least one face, try to get its encoding
        if locations:
            encodings = face_recognition.face_encodings(rgb, locations)
            if encodings:
                encoding = encodings[0]
                break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return encoding # returns None if cancelled, otherwise the face encoding


def enroll_face_for_student(student_id):
    """Full flow: capture face, save .pkl, mark DB."""
    student = get_student_by_id(student_id)
    if not student:
        print("Student not found")
        return False

     # Show webcam and wait for a face
    encoding = capture_face_encoding(f"{student['last_name']} {student['first_name']}")
    if encoding is None:
        return False

    # Create folder if it doesn't exist
    os.makedirs(ENCODINGS_DIR, exist_ok=True)
    # Save the encoding as a file named student_id.pkl
    filepath = os.path.join(ENCODINGS_DIR, f"{student_id}.pkl")
    with open(filepath, 'wb') as f:
        pickle.dump(encoding, f)

    # Update database: face_enrolled = True
    mark_face_enrolled(student_id)
    return True