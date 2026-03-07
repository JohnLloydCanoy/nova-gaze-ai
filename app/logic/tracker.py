import cv2
import numpy as np
from scipy.spatial import distance as dist
from app.logic.blink_detector import BlinkDetector

# Support for MediaPipe
try:
    from mediapipe.python.solutions import face_mesh as mp_face_mesh
    from mediapipe.python.solutions.face_mesh import FaceMesh
except ImportError:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    FaceMesh = mp_face_mesh.FaceMesh

class GazeTracker:
    def __init__(self):
        self.blink_engine = BlinkDetector()
        self.face_mesh = FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Landmark indices from Design Doc
        self.R_EYE = [33, 159, 158, 133, 153, 145]
        self.L_EYE = [362, 380, 374, 263, 386, 385]
        self.R_IRIS = 468
        self.L_IRIS = 473
        self.EAR_THRESHOLD = 0.20

    def calculate_ear(self, eye_indices, landmarks):
        coords = np.array([(landmarks[i].x, landmarks[i].y) for i in eye_indices])
        v1 = dist.euclidean(coords[1], coords[5])
        v2 = dist.euclidean(coords[2], coords[4])
        h = dist.euclidean(coords[0], coords[3])
        return (v1 + v2) / (2.0 * h)

    def get_gaze_ratio(self, landmarks, eye_indices, iris_index):
        inner_x = landmarks[eye_indices[3]].x
        outer_x = landmarks[eye_indices[0]].x
        iris_x = landmarks[iris_index].x
        if outer_x == inner_x: return 0.5
        return (iris_x - inner_x) / (outer_x - inner_x)

    def get_vertical_ratio(self, landmarks):
        # Using eyelids to calculate vertical position
        r_top, r_bottom = landmarks[159].y, landmarks[145].y
        l_top, l_bottom = landmarks[386].y, landmarks[374].y
        r_iris, l_iris = landmarks[468].y, landmarks[473].y
        
        r_ratio = (r_iris - r_top) / (r_bottom - r_top) if (r_bottom - r_top) != 0 else 0.5
        l_ratio = (l_iris - l_top) / (l_bottom - l_top) if (l_bottom - l_top) != 0 else 0.5
        return (r_ratio + l_ratio) / 2.0

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None, False, "center", 0.5

        landmarks = results.multi_face_landmarks[0].landmark
        
        # 1. Blink Detection
        left_ear = self.calculate_ear(self.L_EYE, landmarks)
        right_ear = self.calculate_ear(self.R_EYE, landmarks)
        avg_ear = (left_ear + right_ear) / 2.0
        event = self.blink_engine.update(avg_ear)
        
        # 2. Gaze Direction
        h_ratio = (self.get_gaze_ratio(landmarks, self.R_EYE, self.R_IRIS) + 
                   self.get_gaze_ratio(landmarks, self.L_EYE, self.L_IRIS)) / 2.0
        v_ratio = self.get_vertical_ratio(landmarks)
        
        direction = "center"
        if h_ratio < 0.35: direction = "left"
        elif h_ratio > 0.65: direction = "right"
        elif v_ratio < 0.35: direction = "up"
        elif v_ratio > 0.65: direction = "down"

        return event, avg_ear < self.EAR_THRESHOLD, direction, h_ratio
    