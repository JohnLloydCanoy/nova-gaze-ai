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
        """_summary_

        Args:
            frame (_type_): _description_
        """