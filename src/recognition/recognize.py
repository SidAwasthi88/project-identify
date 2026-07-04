import cv2
import face_recognition
import os
import pickle
import numpy as np

ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/encodings')

def recognize_student(attempt: int = 1):
    """Compares current real-time frames against serialized local facial mappings."""
    if not os.path.exists(ENCODINGS_DIR):
        return None
        
    known_encodings = []
    known_student_ids = []
    
    # Build run-time dictionary buffers from localized data files
    for filename in os.listdir(ENCODINGS_DIR):
        if filename.endswith('.pkl'):
            student_id = int(filename.split('.')[0])
            filepath = os.path.join(ENCODINGS_DIR, filename)
            with open(filepath, 'rb') as f:
                encoding = pickle.load(f)
                known_encodings.append(encoding)
                known_student_ids.append(student_id)
                
    if not known_encodings:
        return None

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        return None

    matched_student_id = None
    
    for _ in range(25):
        ret, frame = video_capture.read()
        if not ret:
            continue
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    matched_student_id = known_student_ids[best_match_index]
                    break
        if matched_student_id:
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return matched_student_id