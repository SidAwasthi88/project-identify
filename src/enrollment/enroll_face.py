"""
enroll_face.py — Capture multiple face samples, average them, and save.
The camera stays open until 30 samples are collected or the user presses Q.
"""

import cv2
import face_recognition
import pickle
import os
import sys
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_queries import mark_face_enrolled, get_student_by_id

ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/embeddings')

# How many face samples to collect (the higher, the better the encoding)
SAMPLE_COUNT = 30


def capture_face_encoding(student_name: str = ""):
    """
    Opens webcam, shows mirrored feed with face box, and collects SAMPLE_COUNT face samples.
    The window stays open until enough samples are captured or the user presses Q.
    Returns the averaged encoding, or None if cancelled.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access webcam.")
        return None

    window_name = f"Enrolling: {student_name} — Press Q to cancel"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    print(f"📷 Collecting {SAMPLE_COUNT} face samples. Please stay still...")
    encodings = []           # collected face encodings

    while len(encodings) < SAMPLE_COUNT:
        ret, frame = cap.read()
        if not ret:
            continue

        # Mirror flip for natural selfie view
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)

        # Draw green boxes and landmarks (optional)
        for top, right, bottom, left in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Show progress
        if len(encodings) > 0:
            progress_text = f"Captured: {len(encodings)}/{SAMPLE_COUNT}"
            cv2.putText(frame, progress_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # If exactly one face is visible, capture its encoding
        if len(face_locations) == 1:
            new_encodings = face_recognition.face_encodings(rgb, face_locations)
            if new_encodings:
                encodings.append(new_encodings[0])
                print(f"   Sample {len(encodings)}/{SAMPLE_COUNT} captured.")
        elif len(face_locations) == 0:
            cv2.putText(frame, "No face detected", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Multiple faces – only one please", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 255), 2)

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("❌ Enrollment cancelled by user.")
            cap.release()
            cv2.destroyAllWindows()
            return None

    cap.release()
    cv2.destroyAllWindows()

    # Average all collected encodings into one robust encoding
    final_encoding = np.mean(encodings, axis=0)
    print(f"✅ {SAMPLE_COUNT} samples collected and averaged.")
    return final_encoding


def enroll_face_for_student(student_id: int):
    """Full flow: capture, average, save .pkl, mark DB."""
    student = get_student_by_id(student_id)
    if not student:
        print(f"❌ Student ID {student_id} not found.")
        return False

    print(f"📋 Enrolling face for: {student['last_name']} {student['first_name']}")
    encoding = capture_face_encoding(f"{student['last_name']} {student['first_name']}")
    if encoding is None:
        return False

    os.makedirs(ENCODINGS_DIR, exist_ok=True)
    filepath = os.path.join(ENCODINGS_DIR, f"{student_id}.pkl")
    with open(filepath, 'wb') as f:
        pickle.dump(encoding, f)

    mark_face_enrolled(student_id)
    print(f"✅ Face enrollment complete for student ID {student_id}")
    return True