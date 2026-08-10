"""
camera_test.py

A live recognition test tool. Opens a webcam window, detects every face
in view, compares it against all saved encodings in data/encodings/, and
draws a box + the student's full name and roll number above their face.

Also draws facial landmark points (the "vector mapping" visualization)
and clearly labels each face independently, so multiple people in frame
are each handled on their own rather than causing an error.

This does NOT touch the attendance database at all — it's purely a
visual test tool.

Press 'q' in the camera window to close it.
"""

import cv2
import face_recognition
import os
import pickle
import numpy as np
import sys

# Ensure proper path loading for database imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_queries import get_student_by_id

ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/encodings')
TOLERANCE = 0.5
RESIZE_SCALE = 0.25


def _open_camera():
    """Tries a couple of backends/indices so it's more likely to open on Linux/Windows."""
    for index in (0, 1):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            return cap
        cap.release()
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if cap.isOpened():
            return cap
        cap.release()
    return None


def _load_known_faces():
    """Loads every saved encoding + builds a 'Name (Roll No.)' label for each student."""
    known_encodings = []
    known_labels = []

    if not os.path.exists(ENCODINGS_DIR):
        return known_encodings, known_labels

    for filename in os.listdir(ENCODINGS_DIR):
        if not filename.endswith('.pkl'):
            continue

        student_id = int(filename.split('.')[0])
        filepath = os.path.join(ENCODINGS_DIR, filename)

        try:
            with open(filepath, 'rb') as f:
                encoding = pickle.load(f)

            student = get_student_by_id(student_id)
            if student:
                full_name = f"{student['first_name']} {student['last_name']}"
                roll_no = student.get('roll_no')
                label = f"{full_name} (Roll {roll_no})" if roll_no else full_name
            else:
                label = f"Student #{student_id}"

            known_encodings.append(encoding)
            known_labels.append(label)
        except Exception as e:
            print(f"⚠️ Failed loading encoding file {filename}: {e}")

    return known_encodings, known_labels


def _draw_landmarks(frame, landmarks, scale):
    """Draws every facial landmark point as a small dot — the 'vector mapping' visualization."""
    for feature_points in landmarks.values():
        for (x, y) in feature_points:
            pt_x, pt_y = int(x / scale), int(y / scale)
            cv2.circle(frame, (pt_x, pt_y), 2, (255, 200, 0), -1)


def run_camera_test():
    """
    Opens a live window and labels recognized faces (name + roll no.) until
    'q' is pressed. Every face in frame is matched independently.

    Returns True if execution ran, False if the camera or encodings couldn't load.
    """
    known_encodings, known_labels = _load_known_faces()

    if not known_encodings:
        print("⚠️ No enrolled faces found. Enroll at least one student first.")
        return False

    video_capture = _open_camera()
    if video_capture is None:
        print("❌ Could not open any webcam.")
        return False

    window_name = "Camera Test - Press Q to close"

    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            small_frame = cv2.resize(frame, (0, 0), fx=RESIZE_SCALE, fy=RESIZE_SCALE)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding, landmarks in zip(face_locations, face_encodings, landmarks_list):
                top, right, bottom, left = [int(v / RESIZE_SCALE) for v in (top, right, bottom, left)]

                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=TOLERANCE)
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)

                label = "Unknown"
                confidence_str = ""

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        label = known_labels[best_match_index]
                        dist = face_distances[best_match_index]
                        confidence_str = f" [Dist: {dist:.2f}]"

                display_label = f"{label}{confidence_str}"
                box_color = (0, 200, 0) if label != "Unknown" else (0, 0, 200)

                # Draw bounding box and facial feature landmarks
                cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                _draw_landmarks(frame, landmarks, RESIZE_SCALE)

                # Label banner above bounding box
                label_width = max(right - left, 9 * len(display_label))
                cv2.rectangle(frame, (left, top - 30), (left + label_width, top), box_color, cv2.FILLED)
                cv2.putText(
                    frame, display_label, (left + 6, top - 8),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1
                )

            # Bottom status banner
            frame_height = frame.shape[0]
            cv2.rectangle(frame, (0, frame_height - 30), (250, frame_height), (0, 0, 0), cv2.FILLED)
            cv2.putText(
                frame, f"Faces in view: {len(face_locations)}", (10, frame_height - 10),
                cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1
            )

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        video_capture.release()
        cv2.destroyAllWindows()

    return True


if __name__ == "__main__":
    run_camera_test()