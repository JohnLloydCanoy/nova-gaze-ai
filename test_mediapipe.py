"""
Phase 1: Test MediaPipe FaceMesh
Goal: See face landmarks on screen to confirm everything works.

Run this with: python test_mediapipe.py
Press 'q' to quit.
"""

import cv2
import mediapipe as mp

# Initialize MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Create the face mesh detector
# refine_landmarks=True gives us iris landmarks (468-477)
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,  # Important! This enables iris tracking
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Open the webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam!")
    exit()

print("Camera opened successfully!")
print("You should see a window with your face and landmarks drawn on it.")
print("Press 'q' to quit.")

while True:
    # Read a frame from the webcam
    ret, frame = cap.read()
    
    if not ret:
        print("ERROR: Could not read frame from webcam!")
        break
    
    # Flip the frame horizontally (mirror effect - more natural)
    frame = cv2.flip(frame, 1)
    
    # Convert BGR (OpenCV format) to RGB (MediaPipe format)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame with MediaPipe
    results = face_mesh.process(rgb_frame)
    
    # If a face was detected, draw the landmarks
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Draw all the face mesh landmarks
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,  # The mesh lines
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
            )
            
            # Draw the eye contours (more visible)
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_LEFT_EYE,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
            )
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_RIGHT_EYE,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
            )
            
            # Draw iris landmarks (the colored part of your eye)
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_IRISES,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_iris_connections_style()
            )
            
            # Print how many landmarks we detected (should be 478)
            num_landmarks = len(face_landmarks.landmark)
            cv2.putText(frame, f"Landmarks: {num_landmarks}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Show "Face Detected" text
            cv2.putText(frame, "Face Detected!", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        # No face detected
        cv2.putText(frame, "No face detected", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Show the frame
    cv2.imshow('MediaPipe Face Mesh Test', frame)
    
    # Check if user pressed 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
face_mesh.close()

print("Done!")
