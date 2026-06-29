"""
enroll_face.py — Capture multiple face samples, average them, and save.
The camera stays open until 30 samples are collected or the user presses Q.
"""

# --- 1. Importing the Toolboxes ---
import cv2          # For the webcam and drawing on screen
import face_recognition  # For finding faces and turning them into numbers
import pickle       # For saving the face-numbers to a file
import os           # For creating folders and file paths
import sys          # For changing where Python looks for files
import numpy as np  # For doing math (averaging) on the face numbers

# Makes Python look in the parent folder so we can use the database file
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_queries import mark_face_enrolled, get_student_by_id

# Where we will save the final face data (a folder called 'embeddings')
ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), '../../data/embeddings')

# How many face pictures to take before we stop. 30 is good for accuracy.
SAMPLE_COUNT = 30


# --- 2. The Camera & Capture Function ---
def capture_face_encoding(student_name: str = ""):
    """
    Opens webcam, shows mirrored feed with face box, and collects 30 face samples.
    The window stays open until enough samples are captured or the user presses Q.
    Returns the averaged encoding, or None if cancelled.
    """
    # Turn on the webcam (0 means the default camera)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access webcam.")
        return None

    # Set up a window with the student's name in the title
    window_name = f"Enrolling: {student_name} — Press Q to cancel"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    print(f"📷 Collecting {SAMPLE_COUNT} face samples. Please stay still...")
    encodings = []  # This list will hold the 30 sets of face-numbers

    # Keep looping until we have collected 30 samples
    while len(encodings) < SAMPLE_COUNT:
        # Grab a single picture from the webcam
        ret, frame = cap.read()
        if not ret:
            continue

        # Flip left-right (mirror) so it looks like a selfie
        frame = cv2.flip(frame, 1)
        # Convert colors: OpenCV uses BGR, face_recognition needs RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 3. Find any faces in this current picture
        face_locations = face_recognition.face_locations(rgb)

        # Draw a green box around every face found (so the user can see it)
        for top, right, bottom, left in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Show how many samples we have taken so far
        if len(encodings) > 0:
            progress_text = f"Captured: {len(encodings)}/{SAMPLE_COUNT}"
            cv2.putText(frame, progress_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # 4. RULES for taking a sample:
        if len(face_locations) == 1:
            # GOOD! Exactly 1 face found. Let's grab its numbers.
            new_encodings = face_recognition.face_encodings(rgb, face_locations)
            if new_encodings:
                encodings.append(new_encodings[0])  # Save the numbers
                print(f"   Sample {len(encodings)}/{SAMPLE_COUNT} captured.")
        elif len(face_locations) == 0:
            # WARNING: No face found. Tell user to look at camera.
            cv2.putText(frame, "No face detected", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # WARNING: Too many faces. Only one person allowed at a time.
            cv2.putText(frame, "Multiple faces – only one please", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 255), 2)

        # Show the webcam feed on the screen
        cv2.imshow(window_name, frame)

        # If the user presses the 'Q' key, stop everything
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("❌ Enrollment cancelled by user.")
            cap.release()
            cv2.destroyAllWindows()
            return None

    # 5. Turn off the camera and close the window
    cap.release()
    cv2.destroyAllWindows()

    # 6. AVERAGE all 30 samples together to make 1 super-accurate set of numbers
    final_encoding = np.mean(encodings, axis=0)
    print(f"✅ {SAMPLE_COUNT} samples collected and averaged.")
    return final_encoding


# --- 7. The "Save to Database" Function ---
def enroll_face_for_student(student_id: int):
    """Full flow: capture, average, save .pkl file, mark DB."""
    # Look up the student's name in the database using their ID
    student = get_student_by_id(student_id)
    if not student:
        print(f"❌ Student ID {student_id} not found.")
        return False

    # Start the camera and collect 30 samples
    print(f"📋 Enrolling face for: {student['last_name']} {student['first_name']}")
    encoding = capture_face_encoding(f"{student['last_name']} {student['first_name']}")
    if encoding is None:
        return False  # User pressed Q or camera failed

    # Make sure the "embeddings" folder exists
    os.makedirs(ENCODINGS_DIR, exist_ok=True)
    
    # Save the final averaged face-numbers to a file named 'student_id.pkl'
    filepath = os.path.join(ENCODINGS_DIR, f"{student_id}.pkl")
    with open(filepath, 'wb') as f:
        pickle.dump(encoding, f)  # 'pickle' saves Python data to disk

    # Update the database to say "This student now has a face saved"
    mark_face_enrolled(student_id)
    print(f"✅ Face enrollment complete for student ID {student_id}")
    return True