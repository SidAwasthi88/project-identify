import cv2
import face_recognition
import os
import pickle
from database.db_queries import mark_face_enrolled

ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/encodings')
os.makedirs(ENCODINGS_DIR, exist_ok=True)

def enroll_face_for_student(student_id: int):
    """Webcam wrapper capturing 128D mathematical structural array profiles."""
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        return False

    captured_encoding = None
    
    # Read frames sequentially to find a clear frontal profile layout
    for _ in range(30):
        ret, frame = video_capture.read()
        if not ret:
            continue
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if len(face_encodings) > 0:
            captured_encoding = face_encodings[0]
            break

    video_capture.release()
    cv2.destroyAllWindows()

    if captured_encoding is not None:
        filepath = os.path.join(ENCODINGS_DIR, f"{student_id}.pkl")
        with open(filepath, 'wb') as f:
            pickle.dump(captured_encoding, f)
            
        mark_face_enrolled(student_id)
        return True
        
    return False