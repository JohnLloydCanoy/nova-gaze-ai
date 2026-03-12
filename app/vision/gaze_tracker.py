import time 
import math 
import cv2
import mediapipe as mp
import numpy as np

class GazeAnalyzer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.current_state = "center"
        self.state_start_time = time.time()
        
        self.gaze_threshold = 0.12
        
        # Normalized gaze thresholds (percentage of eye height/width)
        self.UP_THRESHOLD = -0.15
        self.DOWN_THRESHOLD = 0.18
        self.RIGHT_THRESHOLD = 0.15
        
    def _calculate_distance(self, point1, point2):
        """"Helper function to calculate the 2D distance between two facial landmarks."""
        return math.hypot(point1.x - point2.x, point1.y - point2.y)
        
    def process_frame(self, frame):
        """
        Takes an RGB frame, analyzes the Eye Aspect Ratio, tracks time, 
        and returns any triggered events based on the user's gaze.
        """
        
        # 
        img_h, img_w = frame.shape[:2]
        results = self.face_mesh.process(frame)
        
        new_state = "CENTER"
        event_to_emit = None
        progress = 0.0
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            # Extract Left Eye Landmarks
            iris = landmarks[473]
            eye_top = landmarks[159]
            eye_bottom = landmarks[145]
            eye_inner = landmarks[133]
            eye_outer = landmarks[33]
            
            # Calculate Eye Aspect Ratio (EAR) for inclusive blink detection
            eye_height = self._calculate_distance(eye_top, eye_bottom)
            eye_width = self._calculate_distance(eye_inner, eye_outer)
            
            if eye_width == 0:
                eye_width = 0.0001
                
            ear = eye_height / eye_width
            
            eye_center_y = (eye_top.y + eye_bottom.y) / 2
            eye_center_x = (eye_inner.x + eye_outer.x) / 2
            
            vertical_ratio = (iris.y - eye_center_y) / eye_height
            horizontal_ratio = (iris.x - eye_center_x) / eye_width
            
            if ear < self.EAR_BLINK_TRESHOLD:
                new_state = "CLOSED"
            else:
                if vertical_ratio < self.UP_THRESHOLD:
                    new_state = "UP"
                elif vertical_ratio > self.DOWN_THRESHOLD:
                    new_state = "DOWN"
                elif horizontal_ratio > self.RIGHT_THRESHOLD:
                    new_state = "RIGHT"
            
            cx, cy = int(iris.x * img_w), int(iris.y * img_h)
            cv2.circle(frame, (cx, cy), 3, (0, 229, 255), -1)
            
            if new_state != self.current_state:
                # If user looked somewhere else; reset the timer immediately
                self.current_state = new_state
                self.state_start_time = time.time()
            else:
                elapsed = time.time() - self.state_start_time
                #Process the specific timers you requested
                if new_state == "CLOSED":
                    progress = min(elapsed / 5.0, 1.0) # 5 seconds to trigger SCAN
                    if elapsed >= 5.0:
                        event_to_emit = "SCAN"
                        self.state_start_time = time.time() # Reset timer after emitting event
                elif new_state == "UP":
                    progress = min(elapsed / 3.0, 1.0) # 3 seconds to SELECT UP
                    if elapsed >= 3.0:
                        event_to_emit = "SELECT_UP"
                        self.state_start_time = time.time()