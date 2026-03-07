"""
Phase 3: Blink Detection State Machine
Goal: Count actual blinks (not just "eyes closed" frames).

A blink = eyes close for 2+ frames, then reopen.
This prevents false positives from noise or single-frame glitches.

Run this with: .\venv\Scripts\python.exe test_mediapipe.py
Press 'q' to quit.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os
import math
import time

# Download the face landmarker model if it doesn't exist
MODEL_PATH = "face_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

if not os.path.exists(MODEL_PATH):
    print(f"Downloading face landmarker model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Download complete!")

# Create the face landmarker
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.FaceLandmarker.create_from_options(options)

# Landmark indices for eyes
# Order: [outer_corner, upper_outer, upper_inner, inner_corner, lower_inner, lower_outer]
RIGHT_EYE = [33, 159, 158, 133, 153, 145]
LEFT_EYE = [362, 380, 374, 263, 386, 385]
RIGHT_IRIS = [468, 469, 470, 471, 472]
LEFT_IRIS = [473, 474, 475, 476, 477]

# ===== BLINK DETECTION CONFIG =====
EAR_THRESHOLD = 0.20          # Below this = eyes closed
BLINK_CONSEC_FRAMES = 2       # Must be closed for 2+ frames to count
LONG_BLINK_FRAMES = 15        # 15+ frames = intentional long blink (like a "hold click")

# ===== BLINK STATE TRACKING =====
blink_counter = 0             # Total blinks detected
long_blink_counter = 0        # Total long blinks detected
frames_eyes_closed = 0        # Consecutive frames with eyes closed
blink_in_progress = False     # Are we currently in a blink?
last_blink_time = 0           # Timestamp of last blink (for double-blink detection)
double_blink_window = 0.4     # Seconds - two blinks within this = double blink
double_blink_counter = 0      # Total double blinks detected


def euclidean_distance(p1, p2):
    """Calculate distance between two points"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def calculate_ear(eye_landmarks):
    """
    Calculate Eye Aspect Ratio (EAR)
    
    EAR = (|v1| + |v2|) / (2 * |h|)
    
    Where:
    - v1 = vertical distance between upper outer and lower outer eyelid
    - v2 = vertical distance between upper inner and lower inner eyelid  
    - h = horizontal distance between eye corners
    
    High EAR (~0.25-0.30) = eye open
    Low EAR (~0.15 or less) = eye closed
    """
    # Vertical distances
    v1 = euclidean_distance(eye_landmarks[1], eye_landmarks[5])  # upper_outer to lower_outer
    v2 = euclidean_distance(eye_landmarks[2], eye_landmarks[4])  # upper_inner to lower_inner
    
    # Horizontal distance
    h = euclidean_distance(eye_landmarks[0], eye_landmarks[3])   # outer_corner to inner_corner
    
    # Avoid division by zero
    if h == 0:
        return 0.0
    
    ear = (v1 + v2) / (2.0 * h)
    return ear


def get_eye_landmarks(face_landmarks, eye_indices, frame_width, frame_height):
    """Extract eye landmark coordinates as (x, y) tuples"""
    points = []
    for idx in eye_indices:
        lm = face_landmarks[idx]
        x = lm.x * frame_width
        y = lm.y * frame_height
        points.append((x, y))
    return points


def draw_landmarks_on_image(frame, detection_result):
    """Draw face landmarks on the image and calculate EAR"""
    if not detection_result.face_landmarks:
        return frame, None, None
    
    h, w, _ = frame.shape
    left_ear = None
    right_ear = None
    
    for face_landmarks in detection_result.face_landmarks:
        # Get eye landmarks for EAR calculation
        right_eye_points = get_eye_landmarks(face_landmarks, RIGHT_EYE, w, h)
        left_eye_points = get_eye_landmarks(face_landmarks, LEFT_EYE, w, h)
        
        # Calculate EAR for each eye
        right_ear = calculate_ear(right_eye_points)
        left_ear = calculate_ear(left_eye_points)
        
        # Draw all landmarks as small dots
        for idx, landmark in enumerate(face_landmarks):
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            
            # Color code different parts
            if idx in RIGHT_EYE or idx in LEFT_EYE:
                color = (0, 255, 0)  # Green for eye contour
                size = 2
            elif idx in RIGHT_IRIS or idx in LEFT_IRIS:
                color = (255, 0, 255)  # Magenta for iris
                size = 3
            else:
                color = (200, 200, 200)  # Gray for other landmarks
                size = 1
            
            cv2.circle(frame, (x, y), size, color, -1)
        
        # Draw eye contours with lines
        for eye_indices in [RIGHT_EYE, LEFT_EYE]:
            points = []
            for idx in eye_indices:
                lm = face_landmarks[idx]
                points.append((int(lm.x * w), int(lm.y * h)))
            for i in range(len(points)):
                cv2.line(frame, points[i], points[(i+1) % len(points)], (0, 255, 0), 1)
        
        # Draw iris circles
        for iris_indices in [RIGHT_IRIS, LEFT_IRIS]:
            center_lm = face_landmarks[iris_indices[0]]
            cx, cy = int(center_lm.x * w), int(center_lm.y * h)
            edge_lm = face_landmarks[iris_indices[1]]
            ex, ey = int(edge_lm.x * w), int(edge_lm.y * h)
            radius = int(((cx - ex)**2 + (cy - ey)**2)**0.5)
            cv2.circle(frame, (cx, cy), radius, (255, 0, 255), 1)
            cv2.circle(frame, (cx, cy), 2, (0, 0, 255), -1)
    
    return frame, left_ear, right_ear


# Open the webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam!")
    exit()

print("=" * 50)
print("Phase 3: Blink Detection State Machine")
print("=" * 50)
print("This detects ACTUAL blinks, not just closed eyes!")
print("")
print("Gesture types:")
print("  - Single Blink: quick close-open (like a click)")
print("  - Double Blink: two blinks within 0.4s (like double-click)")
print("  - Long Blink:   hold eyes closed 0.5s+ (like a drag/hold)")
print("")
print("TRY IT: Blink naturally and watch the counters!")
print("Press 'q' to quit.")
print("=" * 50)

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("ERROR: Could not read frame from webcam!")
        break
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    detection_result = detector.detect(mp_image)
    
    if detection_result.face_landmarks:
        frame, left_ear, right_ear = draw_landmarks_on_image(frame, detection_result)
        
        # Calculate average EAR
        avg_ear = (left_ear + right_ear) / 2.0
        
        # ===== BLINK STATE MACHINE =====
        if avg_ear < EAR_THRESHOLD:
            # Eyes are closed this frame
            frames_eyes_closed += 1
            
            if frames_eyes_closed >= BLINK_CONSEC_FRAMES and not blink_in_progress:
                # We've confirmed a blink has started (not just noise)
                blink_in_progress = True
            
            # Check for long blink
            if frames_eyes_closed == LONG_BLINK_FRAMES:
                long_blink_counter += 1
                print(f">>> LONG BLINK #{long_blink_counter} detected! (held for {LONG_BLINK_FRAMES} frames)")
            
            status = f"EYES CLOSED ({frames_eyes_closed} frames)"
            status_color = (0, 0, 255)  # Red
            
        else:
            # Eyes are open this frame
            if blink_in_progress:
                # Blink just ended! Count it.
                blink_in_progress = False
                current_time = time.time()
                
                # Was it a long blink? (already counted above)
                if frames_eyes_closed >= LONG_BLINK_FRAMES:
                    pass  # Already counted as long blink
                else:
                    # Normal blink - check for double blink
                    blink_counter += 1
                    
                    if current_time - last_blink_time < double_blink_window:
                        double_blink_counter += 1
                        print(f">>> DOUBLE BLINK #{double_blink_counter} detected!")
                    else:
                        print(f">>> Blink #{blink_counter} detected!")
                    
                    last_blink_time = current_time
            
            frames_eyes_closed = 0
            status = "Eyes Open"
            status_color = (0, 255, 0)  # Green
        
        # Display EAR values
        cv2.putText(frame, f"Left EAR:  {left_ear:.3f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Right EAR: {right_ear:.3f}", (10, 55), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Avg EAR:   {avg_ear:.3f}", (10, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Display blink counters
        cv2.putText(frame, f"Blinks: {blink_counter}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Double Blinks: {double_blink_counter}", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
        cv2.putText(frame, f"Long Blinks: {long_blink_counter}", (10, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        
        # Status indicator
        cv2.putText(frame, status, (10, 220), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Draw a visual EAR bar
        bar_width = int(avg_ear * 400)
        bar_color = status_color
        cv2.rectangle(frame, (10, 240), (10 + bar_width, 260), bar_color, -1)
        cv2.rectangle(frame, (10, 240), (10 + int(EAR_THRESHOLD * 400), 260), (100, 100, 100), 2)
        
    else:
        cv2.putText(frame, "No face detected", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow('Blink Detection - Phase 3', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("")
print("=" * 50)
print("SESSION SUMMARY")
print("=" * 50)
print(f"Total Blinks:        {blink_counter}")
print(f"Double Blinks:       {double_blink_counter}")
print(f"Long Blinks:         {long_blink_counter}")
print("=" * 50)
print("Done!")
