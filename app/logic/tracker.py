import cv2
import numpy as np
from scipy.spatial import distance as dist

# Support for different MediaPipe installation structures
try:
    from mediapipe.python.solutions import face_mesh as mp_face_mesh
    from mediapipe.python.solutions.face_mesh import FaceMesh
except ImportError:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    FaceMesh = mp_face_mesh.FaceMesh

class GazeTracker:
    def __init__(self):
        self.face_mesh = FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # Landmark indices for EAR and Iris tracking
        self.R_EYE = [33, 159, 158, 133, 153, 145]
        self.L_EYE = [362, 380, 374, 263, 386, 385]
        self.R_IRIS = 468
        self.L_IRIS = 473
        self.EAR_THRESHOLD = 0.23
        self.SELECT_BLINK_THRESHOLD = 90   # ~3 seconds at 30fps
        self.CLOSE_BLINK_THRESHOLD = 180   # ~6 seconds at 30fps

    def calculate_ear(self, eye_indices, landmarks):
        """Calculates EAR with explicit float conversion for C++ compatibility."""
        coords = []
        for i in eye_indices:
            coords.append((float(landmarks[i].x), float(landmarks[i].y)))
        
        coords = np.array(coords)
        v1 = dist.euclidean(coords[1], coords[5])
        v2 = dist.euclidean(coords[2], coords[4])
        h = dist.euclidean(coords[0], coords[3])
        return (v1 + v2) / (2.0 * h)

    def get_gaze_ratio(self, landmarks, eye_indices, iris_index):
        inner_x = float(landmarks[eye_indices[3]].x)
        outer_x = float(landmarks[eye_indices[0]].x)
        iris_x = float(landmarks[iris_index].x)
        if outer_x == inner_x: return 0.5
        return (iris_x - inner_x) / (outer_x - inner_x)

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None, False, None, 0

        landmarks = results.multi_face_landmarks[0].landmark
        
        # Blink Detection (EAR)
        left_ear = self.calculate_ear(self.L_EYE, landmarks)
        right_ear = self.calculate_ear(self.R_EYE, landmarks)
        avg_ear = (left_ear + right_ear) / 2.0
        is_blinking = avg_ear < self.EAR_THRESHOLD

        # Full Gaze Direction (left/right/up/down/center)
        gaze_direction = self.get_full_gaze_direction(landmarks)
        
        # Get horizontal gaze ratio for precise tracking
        r_h_ratio = self.get_gaze_ratio(landmarks, self.R_EYE, self.R_IRIS)
        l_h_ratio = self.get_gaze_ratio(landmarks, self.L_EYE, self.L_IRIS)
        horizontal_gaze = (r_h_ratio + l_h_ratio) / 2.0
        
        return None, bool(is_blinking), gaze_direction, float(horizontal_gaze)
    
    def get_full_gaze_direction(self, landmarks):
        """
        Detects full gaze direction: left, right, up, down, or center.
        Returns: 'left', 'right', 'up', 'down', or 'center'
        """
        # Horizontal gaze
        r_h_ratio = self.get_gaze_ratio(landmarks, self.R_EYE, self.R_IRIS)
        l_h_ratio = self.get_gaze_ratio(landmarks, self.L_EYE, self.L_IRIS)
        horizontal = (r_h_ratio + l_h_ratio) / 2.0
        
        # Vertical gaze
        vertical = self.get_vertical_gaze_ratio(landmarks)
        
        # Determine primary direction
        # Horizontal thresholds
        if horizontal < 0.35:  # Looking left
            return 'left'
        elif horizontal > 0.65:  # Looking right
            return 'right'
        # Vertical thresholds (only if not strongly left/right)
        elif vertical < 0.35:  # Looking up
            return 'up'
        elif vertical > 0.65:  # Looking down
            return 'down'
        else:
            return 'center'
    
    def get_vertical_gaze_ratio(self, landmarks):
        """
        Get vertical gaze ratio (0 = up, 1 = down).
        Returns float between 0 and 1.
        """
        # Right eye
        r_top_y = float(landmarks[159].y)
        r_bottom_y = float(landmarks[145].y)
        r_iris_y = float(landmarks[self.R_IRIS].y)
        
        # Left eye
        l_top_y = float(landmarks[386].y)
        l_bottom_y = float(landmarks[374].y)
        l_iris_y = float(landmarks[self.L_IRIS].y)
        
        # Calculate relative position (0 = top, 1 = bottom)
        r_eye_height = r_bottom_y - r_top_y
        l_eye_height = l_bottom_y - l_top_y
        
        if r_eye_height != 0 and l_eye_height != 0:
            r_ratio = (r_iris_y - r_top_y) / r_eye_height
            l_ratio = (l_iris_y - l_top_y) / l_eye_height
            return (r_ratio + l_ratio) / 2.0
        
        return 0.5  # center