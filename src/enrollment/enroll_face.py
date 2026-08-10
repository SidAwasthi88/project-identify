import cv2
import face_recognition
import os
import pickle
import numpy as np
from database.db_queries import mark_face_enrolled

# ─────────────────────────────────────────────
# CONFIGURATION & CONSTANTS
# ─────────────────────────────────────────────
ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/encodings')
os.makedirs(ENCODINGS_DIR, exist_ok=True)

TARGET_SAMPLES = 30
RESIZE_SCALE = 0.25  # Downscaling factor for faster facial feature detection


def _open_camera():
    """Attempts to initialize webcam using common device indices and backends."""
    for index in (0, 1):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            return cap
        cap.release()
        
        # Explicit V4L2 fallback (often needed for Linux/Raspberry Pi environments)
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if cap.isOpened():
            return cap
        cap.release()
    return None


def _draw_landmarks(frame, landmarks, scale):
    """Renders facial landmark feature vectors as blue points on the main frame."""
    for feature_points in landmarks.values():
        for (x, y) in feature_points:
            pt_x, pt_y = int(x / scale), int(y / scale)
            cv2.circle(frame, (pt_x, pt_y), 2, (255, 200, 0), -1)


def enroll_face_for_student(student_id: int):
    """
    Launches webcam capture feed, detects faces, draws landmark markers,
    and captures TARGET_SAMPLES unique face encodings for a student.

    Averages encodings into a single array and saves as a .pkl file in data/encodings/.
    Updates database status upon successful completion.
    
    Returns:
        (bool, str): Success status and descriptive response message.
    """
    video_capture = _open_camera()
    if video_capture is None:
        return False, "Could not open webcam. Ensure camera is connected and not in use."

    collected_encodings = []
    window_name = "Face Enrollment - Press Q to Cancel"

    try:
        while len(collected_encodings) < TARGET_SAMPLES:
            ret, frame = video_capture.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)  # Mirror frame for intuitive user interaction
            small_frame = cv2.resize(frame, (0, 0), fx=RESIZE_SCALE, fy=RESIZE_SCALE)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            status_text = ""
            status_color = (0, 180, 0)  # Green by default

            if len(face_locations) == 0:
                status_text = "No face detected - Position yourself in front of camera"
                status_color = (0, 0, 200)

            elif len(face_locations) > 1:
                status_text = "Multiple faces detected - Please ensure only one person is in frame"
                status_color = (0, 0, 200)
                
                # Outline every detected face in red to indicate error state
                for (top, right, bottom, left) in face_locations:
                    top, right, bottom, left = [int(v / RESIZE_SCALE) for v in (top, right, bottom, left)]
                    cv2.rectangle(frame, (left, top), (right, bottom), status_color, 2)

            else:
                # Valid capture step: Exactly one face found
                landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                top, right, bottom, left = face_locations[0]
                top, right, bottom, left = [int(v / RESIZE_SCALE) for v in (top, right, bottom, left)]
                
                # Draw main target box and feature points
                cv2.rectangle(frame, (left, top), (right, bottom), status_color, 2)

                if landmarks_list:
                    _draw_landmarks(frame, landmarks_list[0], RESIZE_SCALE)

                if face_encodings:
                    collected_encodings.append(face_encodings[0])

                status_text = f"Capturing Face Data: {len(collected_encodings)}/{TARGET_SAMPLES}"

            # ─────────────────────────────────────────────
            # OVERLAY HUD & PROGRESS BAR
            # ─────────────────────────────────────────────
            frame_height, frame_width = frame.shape[:2]
            
            # Top Status Banner
            cv2.rectangle(frame, (0, 0), (frame_width, 40), status_color, cv2.FILLED)
            cv2.putText(frame, status_text, (15, 26), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1)

            # Bottom Progress Indicator
            progress_pct = len(collected_encodings) / TARGET_SAMPLES
            progress_width = int(frame_width * progress_pct)
            cv2.rectangle(frame, (0, frame_height - 10), (progress_width, frame_height), (0, 255, 0), cv2.FILLED)

            cv2.imshow(window_name, frame)

            # Keyboard interrupt check (Q key)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                return False, "Enrollment cancelled by user."

    finally:
        # Guarantee resources are cleaned up regardless of loop termination
        video_capture.release()
        cv2.destroyAllWindows()

    # ─────────────────────────────────────────────
    # ENCODING PROCESSING & PERSISTENCE
    # ─────────────────────────────────────────────
    if len(collected_encodings) == TARGET_SAMPLES:
        # Calculate mean feature vector across all collected samples
        averaged_encoding = np.mean(collected_encodings, axis=0)
        filepath = os.path.join(ENCODINGS_DIR, f"{student_id}.pkl")
        
        with open(filepath, 'wb') as f:
            pickle.dump(averaged_encoding, f)

        # Record enrollment flag in database
        mark_face_enrolled(student_id)
        return True, f"Enrollment successful! {TARGET_SAMPLES} face vectors collected and compiled."

    return False, "Enrollment incomplete."


# ─────────────────────────────────────────────
# LOAD ENCODINGS FUNCTION (For Attendance)
# ─────────────────────────────────────────────
def load_face_encodings(student_id: int):
    """
    Load face encodings for a specific student from the data/encodings/ folder.
    Returns a list of encodings, or None if not found.
    """
    filepath = os.path.join(ENCODINGS_DIR, f"{student_id}.pkl")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'rb') as f:
        encodings = pickle.load(f)
    return encodings


if __name__ == "__main__":
    # Standard standalone test runner
    test_student_id = 1
    print(f"Testing Face Enrollment module for Student ID: {test_student_id}")
    success, message = enroll_face_for_student(test_student_id)
    print(f"Result: {message}")