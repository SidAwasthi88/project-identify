import cv2
import face_recognition
import os
import pickle
import numpy as np
from database.db_queries import mark_face_enrolled

ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/encodings')
os.makedirs(ENCODINGS_DIR, exist_ok=True)

TARGET_SAMPLES = 30
RESIZE_SCALE = 0.25  # process a shrunk frame for speed, then scale coordinates back up


def _open_camera():
    """Tries a couple of backends/indices so it's more likely to actually open on Linux/Windows."""
    for index in (0, 1):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            return cap
        cap.release()
        # Try the explicit V4L2 backend, common fix on Linux
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if cap.isOpened():
            return cap
        cap.release()
    return None


def _draw_landmarks(frame, landmarks, scale):
    """Draws every facial landmark point as a small blue dot — the 'vector mapping' visualization."""
    for feature_points in landmarks.values():
        for (x, y) in feature_points:
            x, y = int(x / scale), int(y / scale)
            cv2.circle(frame, (x, y), 2, (255, 200, 0), -1)


def enroll_face_for_student(student_id: int):
    """
    Opens a live webcam window, shows face box + landmark points + a running
    sample counter, and collects TARGET_SAMPLES encodings of a single face.
    Rejects frames with zero or multiple faces (shows a warning instead).
    Averages all collected encodings into one vector and saves it.

    Returns (success: bool, message: str).
    Press Q at any time to cancel early.
    """
    video_capture = _open_camera()
    if video_capture is None:
        return False, "Could not open any webcam. Check that it's not in use by another app, and that you have camera permissions."

    collected_encodings = []
    window_name = "Face Enrollment - Press Q to cancel"

    while len(collected_encodings) < TARGET_SAMPLES:
        ret, frame = video_capture.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)  # mirror, feels natural
        small_frame = cv2.resize(frame, (0, 0), fx=RESIZE_SCALE, fy=RESIZE_SCALE)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        status_text = ""
        status_color = (0, 200, 0)

        if len(face_locations) == 0:
            status_text = "No face detected"
            status_color = (0, 0, 200)

        elif len(face_locations) > 1:
            status_text = "Multiple faces detected - only one person at a time"
            status_color = (0, 0, 200)
            # Draw a box around every face found so the student can see the problem
            for (top, right, bottom, left) in face_locations:
                top, right, bottom, left = [int(v / RESIZE_SCALE) for v in (top, right, bottom, left)]
                cv2.rectangle(frame, (left, top), (right, bottom), status_color, 2)

        else:
            # Exactly one face - this is the good case
            landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            top, right, bottom, left = face_locations[0]
            top, right, bottom, left = [int(v / RESIZE_SCALE) for v in (top, right, bottom, left)]
            cv2.rectangle(frame, (left, top), (right, bottom), status_color, 2)

            if landmarks_list:
                _draw_landmarks(frame, landmarks_list[0], RESIZE_SCALE)

            if face_encodings:
                collected_encodings.append(face_encodings[0])

            status_text = f"Captured {len(collected_encodings)}/{TARGET_SAMPLES}"

        # Status banner at the top of the frame
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), status_color, cv2.FILLED)
        cv2.putText(frame, status_text, (10, 27), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            video_capture.release()
            cv2.destroyAllWindows()
            return False, "Enrollment cancelled."

    video_capture.release()
    cv2.destroyAllWindows()

    # Average all 30 samples into a single, more robust encoding
    averaged_encoding = np.mean(collected_encodings, axis=0)
    filepath = os.path.join(ENCODINGS_DIR, f"{student_id}.pkl")
    with open(filepath, 'wb') as f:
        pickle.dump(averaged_encoding, f)

    mark_face_enrolled(student_id)
    return True, f"Enrollment complete - {TARGET_SAMPLES} samples captured and averaged."