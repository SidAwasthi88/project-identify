import cv2
import face_recognition

# Open webcam
cap = cv2.VideoCapture(0)
window_name = "Face Detection Test - Mirrored"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 800, 600)

print("Press Q to quit.")

while True:
    ret, frame = cap.read()   # get one image from webcam
    if not ret:
        continue

    # Mirror flip
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Converting to RGB because face_recognition expects that
    locations = face_recognition.face_locations(rgb) # Find all face positions in the image

    # Draws green rectangle around each face
    for top, right, bottom, left in locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

    # Shows how many faces were found
    cv2.putText(frame, f"Faces: {len(locations)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Display the image with boxes
    cv2.imshow(window_name, frame)

    # Exit when q is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()