import os
import sys

# Ensure 'src' is in sys.path before importing local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import cv2
import pickle
import numpy as np
import face_recognition

from database.db_queries import get_session_by_id, get_students_in_subject, mark_attendance
from dashboard.session import determine_status

def run_live_attendance(session_id: int, start_time: str) -> int:
    session_info = get_session_by_id(session_id)
    if not session_info:
        raise ValueError("Session not found.")

    subject_students = get_students_in_subject(session_info["subject_id"])
    if not subject_students:
        return 0

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    encodings_dir = os.path.join(project_root, "data", "encodings")
    
    student_encodings, student_info = {}, {}
    for s in subject_students:
        fp = os.path.join(encodings_dir, f"{s['id']}.pkl")
        if os.path.exists(fp):
            with open(fp, "rb") as fh:
                student_encodings[s["id"]] = np.array(pickle.load(fh))
                student_info[s["id"]] = {
                    "reg_no": s["reg_no"],
                    "first_name": s["first_name"],
                    "last_name": s["last_name"],
                }

    if not student_encodings:
        return 0

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera hardware unavailable.")

    marked = set()
    counter = 0
    FRAME_SKIP, SCALE, TOL = 2, 0.5, 0.4
    win = "Attendance Scanner — Press 'q' to stop"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 720, 540)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            counter += 1

            if counter % FRAME_SKIP == 0:
                small = cv2.resize(frame, (0, 0), fx=SCALE, fy=SCALE)
                rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                locs = face_recognition.face_locations(rgb, number_of_times_to_upsample=0)
                encs = face_recognition.face_encodings(rgb, locs)

                for (top, right, bottom, left), enc in zip(locs, encs):
                    top, right, bottom, left = [int(v / SCALE) for v in (top, right, bottom, left)]
                    best_id, best_dist = None, 1.0
                    for sid, known in student_encodings.items():
                        if True in face_recognition.compare_faces([known], enc, tolerance=TOL):
                            d = face_recognition.face_distance([known], enc)[0]
                            if d < best_dist:
                                best_dist, best_id = d, sid

                    if best_id is not None:
                        info = student_info[best_id]
                        label = f"{info['first_name']} {info['last_name']}"
                        if best_id not in marked:
                            status = determine_status(start_time)
                            mark_attendance(session_id, best_id, status, marked_by="face")
                            marked.add(best_id)
                    else:
                        label = "Unknown"

                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, label, (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.putText(frame, f"Faces: {len(locs)} | Marked: {len(marked)}/{len(student_encodings)}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow(win, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return len(marked)