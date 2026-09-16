import cv2
import face_recognition
import os
import pickle
import numpy as np

# Relative path resolving from src/recognition/ to data/encodings/
ENCODINGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/encodings'))
TOLERANCE = 0.5        # Distance threshold for face verification
RESIZE_SCALE = 0.25    # Frame downscaling factor for real-time performance


def _open_camera():
    """Attempts to initialize webcam using common indices and platform backends."""
    for index in (0, 1):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            return cap
        cap.release()
        
        # Explicit V4L2 fallback (Linux / Raspberry Pi)
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if cap.isOpened():
            return cap
        cap.release()
    return None


def _load_known_encodings():
    known_encodings = []
    known_student_ids = []

    if not os.path.exists(ENCODINGS_DIR):
        return known_encodings, known_student_ids

    for filename in os.listdir(ENCODINGS_DIR):
        if not filename.endswith('.pkl'):
            continue

        try:
            student_id = int(filename.split('.')[0])
            filepath = os.path.join(ENCODINGS_DIR, filename)
            
            with open(filepath, 'rb') as f:
                encoding = pickle.load(f)
                known_encodings.append(encoding)
                known_student_ids.append(student_id)
        except Exception as e:
            print(f"⚠️ Error loading encoding file '{filename}': {e}")

    return known_encodings, known_student_ids


def recognize_student(attempt: int = 1, max_frames: int = 25, show_window: bool = True) -> int | None:

    known_encodings, known_student_ids = _load_known_encodings()

    if not known_encodings:
        print("⚠️ No student encodings found in storage. Enroll students first.")
        return None

    video_capture = _open_camera()
    if video_capture is None:
        print("❌ Failed to access camera device.")
        return None

    matched_student_id = None
    window_name = "Attendance Scanning"

    try:
        for frame_idx in range(max_frames):
            ret, frame = video_capture.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)  # Mirror frame for natural alignment
            
            # Downscale frame for fast facial vector extraction
            small_frame = cv2.resize(frame, (0, 0), fx=RESIZE_SCALE, fy=RESIZE_SCALE)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=TOLERANCE)
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        matched_student_id = known_student_ids[best_match_index]

                        # Draw bounding overlay if rendering feed window
                        if show_window:
                            top, right, bottom, left = [int(v / RESIZE_SCALE) for v in (top, right, bottom, left)]
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                            cv2.putText(
                                frame, f"ID #{matched_student_id}", (left, top - 10),
                                cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0), 1
                            )
                        break

            if show_window:
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 35), (30, 30, 30), cv2.FILLED)
                cv2.putText(
                    frame, f"Scanning face... Frame {frame_idx + 1}/{max_frames} (Press 'Q' to exit)",
                    (12, 23), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1
                )
                cv2.imshow(window_name, frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Scan aborted by user.")
                    break

            if matched_student_id is not None:
                print(f"✅ Matched Student ID: {matched_student_id}")
                break

    finally:
        video_capture.release()
        if show_window:
            cv2.destroyAllWindows()

    return matched_student_id


if __name__ == "__main__":
    print("Executing standalone test for recognize.py...")
    matched_id = recognize_student(attempt=1, max_frames=30, show_window=True)
    if matched_id:
        print(f"Recognition Success: Student ID = {matched_id}")
    else:
        print("Recognition Result: No match found.")