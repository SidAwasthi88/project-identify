import cv2
import face_recognition

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    landmarks = face_recognition.face_landmarks(rgb) 
    # Takes the RGB image, detects all faces in it, and for each face returns a dictionary of facial features

    # landmarks is a list (one element for each detected face)
    for face in landmarks: # Loops through each detected face
        for feature, points in face.items():
            for point in points:
                cv2.circle(frame, point, 2, (0, 255, 0), -1)
    # If there are two people in the frame, this loop runs twice.

    cv2.imshow("Landmark Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()