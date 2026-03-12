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