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
            
            
            eye_height = self._calculate_distance(eye_top, eye_bottom)
            eye_width = self._calculate_distance(eye_inner, eye_outer)