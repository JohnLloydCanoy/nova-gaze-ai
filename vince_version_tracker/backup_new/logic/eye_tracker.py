"""
Eye Tracker Module for Nova-Gaze
Handles all eye tracking logic: gaze direction, blink detection, calibration.

Designed for EYES-ONLY tracking - no head movement required.
This is essential for users with ALS/paralysis who can only move their eyes.
"""

import math
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os


class EyeTracker:
    """
    Processes face landmarks to detect:
    - Gaze direction (left/right/up/down/center)
    - Blinks (single, double, long)
    - Eye aspect ratio (EAR)
    """
    
    # Landmark indices
    RIGHT_EYE = [33, 159, 158, 133, 153, 145]
    LEFT_EYE = [362, 380, 374, 263, 386, 385]
    RIGHT_IRIS = [468, 469, 470, 471, 472]
    LEFT_IRIS = [473, 474, 475, 476, 477]
    
    def __init__(self, model_path="face_landmarker.task"):
        """Initialize the eye tracker with MediaPipe FaceLandmarker."""
        self.model_path = model_path
        self._ensure_model_exists()
        self._init_detector()
        self._init_state()
    
    def _ensure_model_exists(self):
        """Download the face landmarker model if it doesn't exist."""
        if not os.path.exists(self.model_path):
            print(f"[EyeTracker] Downloading face landmarker model...")
            url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            urllib.request.urlretrieve(url, self.model_path)
            print("[EyeTracker] Download complete!")
    
    def _init_detector(self):
        """Initialize MediaPipe FaceLandmarker."""
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)
    
    def _init_state(self):
        """Initialize tracking state variables."""
        # Blink detection config
        self.ear_threshold = 0.20
        self.blink_consec_frames = 2
        self.long_blink_frames = 15
        
        # Gaze config
        self.gaze_horizontal_thresh = 0.35
        self.gaze_vertical_thresh = 0.40
        
        # Calibration state
        self.calibration_samples = []
        self.calibration_complete = False
        self.calibration_frames = 60  # ~2 seconds at 30fps
        self.baseline_iris_y = 0.5
        
        # Blink state
        self.frames_eyes_closed = 0
        self.blink_in_progress = False
        self.last_blink_time = 0
        self.double_blink_window = 0.4
        
        # Counters (for debugging/display)
        self.blink_count = 0
        self.double_blink_count = 0
        self.long_blink_count = 0
    
    def reset_calibration(self):
        """Reset calibration to recalibrate neutral eye position."""
        self.calibration_samples = []
        self.calibration_complete = False
        self.baseline_iris_y = 0.5
        print("[EyeTracker] Calibration reset. Look straight ahead.")
    
    def process_frame(self, rgb_frame):
        """
        Process a single frame and return tracking results.
        
        Args:
            rgb_frame: RGB numpy array from camera
            
        Returns:
            dict with keys:
                - face_detected: bool
                - gaze_h: float 0-1 (0=left, 0.5=center, 1=right)
                - gaze_v: float 0-1 (0=up, 0.5=center, 1=down)
                - gaze_direction: str ("LEFT", "RIGHT", "UP", "DOWN", "CENTER", etc.)
                - ear_left: float
                - ear_right: float
                - ear_avg: float
                - eyes_closed: bool
                - blink_event: str or None ("BLINK", "DOUBLE_BLINK", "LONG_BLINK")
                - calibrating: bool
                - calibration_progress: float 0-1
                - landmarks: list of face landmarks (for drawing)
        """
        result = {
            'face_detected': False,
            'gaze_h': 0.5,
            'gaze_v': 0.5,
            'gaze_direction': 'CENTER',
            'ear_left': 0.0,
            'ear_right': 0.0,
            'ear_avg': 0.0,
            'eyes_closed': False,
            'blink_event': None,
            'calibrating': not self.calibration_complete,
            'calibration_progress': len(self.calibration_samples) / self.calibration_frames,
            'landmarks': None
        }
        
        # Run MediaPipe detection
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection = self.detector.detect(mp_image)
        
        if not detection.face_landmarks:
            return result
        
        result['face_detected'] = True
        face_landmarks = detection.face_landmarks[0]
        result['landmarks'] = face_landmarks
        
        h, w = rgb_frame.shape[:2]
        
        # Get eye landmarks
        right_eye_pts = self._get_eye_landmarks(face_landmarks, self.RIGHT_EYE, w, h)
        left_eye_pts = self._get_eye_landmarks(face_landmarks, self.LEFT_EYE, w, h)
        
        # Calculate EAR
        result['ear_right'] = self._calculate_ear(right_eye_pts)
        result['ear_left'] = self._calculate_ear(left_eye_pts)
        result['ear_avg'] = (result['ear_left'] + result['ear_right']) / 2.0
        
        # Get iris centers
        right_iris = (face_landmarks[self.RIGHT_IRIS[0]].x * w, 
                      face_landmarks[self.RIGHT_IRIS[0]].y * h)
        left_iris = (face_landmarks[self.LEFT_IRIS[0]].x * w,
                     face_landmarks[self.LEFT_IRIS[0]].y * h)
        
        # Calculate horizontal gaze
        right_h = self._calculate_horizontal_gaze(right_eye_pts, right_iris)
        left_h = self._calculate_horizontal_gaze(left_eye_pts, left_iris)
        result['gaze_h'] = (right_h + left_h) / 2.0
        
        # Calculate vertical gaze (with calibration)
        right_v = self._calculate_vertical_iris_ratio(right_eye_pts, right_iris)
        left_v = self._calculate_vertical_iris_ratio(left_eye_pts, left_iris)
        avg_v_raw = (right_v + left_v) / 2.0
        
        # Auto-calibration
        if not self.calibration_complete:
            self.calibration_samples.append(avg_v_raw)
            if len(self.calibration_samples) >= self.calibration_frames:
                self.baseline_iris_y = sum(self.calibration_samples) / len(self.calibration_samples)
                self.calibration_complete = True
                print(f"[EyeTracker] Calibration complete! Baseline: {self.baseline_iris_y:.4f}")
        
        # Apply calibration to vertical gaze
        deviation = avg_v_raw - self.baseline_iris_y
        amplified = deviation * 8.0
        result['gaze_v'] = max(0.0, min(1.0, 0.5 + amplified))
        
        # Get gaze direction string
        result['gaze_direction'] = self._get_gaze_direction(result['gaze_h'], result['gaze_v'])
        
        # Process blink state machine
        result['eyes_closed'] = result['ear_avg'] < self.ear_threshold
        blink_event = self._process_blink_state(result['eyes_closed'])
        result['blink_event'] = blink_event
        
        return result
    
    def _get_eye_landmarks(self, face_landmarks, indices, w, h):
        """Extract eye landmark coordinates as (x, y) tuples."""
        return [(face_landmarks[i].x * w, face_landmarks[i].y * h) for i in indices]
    
    def _calculate_ear(self, eye_pts):
        """Calculate Eye Aspect Ratio."""
        v1 = self._distance(eye_pts[1], eye_pts[5])
        v2 = self._distance(eye_pts[2], eye_pts[4])
        h = self._distance(eye_pts[0], eye_pts[3])
        if h == 0:
            return 0.0
        return (v1 + v2) / (2.0 * h)
    
    def _calculate_horizontal_gaze(self, eye_pts, iris_center):
        """Calculate horizontal gaze ratio (0=left, 0.5=center, 1=right)."""
        outer = eye_pts[0]
        inner = eye_pts[3]
        eye_width = inner[0] - outer[0]
        if abs(eye_width) < 1:
            return 0.5
        ratio = (iris_center[0] - outer[0]) / eye_width
        return max(0.0, min(1.0, ratio))
    
    def _calculate_vertical_iris_ratio(self, eye_pts, iris_center):
        """Calculate raw vertical iris position relative to eye corners."""
        outer = eye_pts[0]
        inner = eye_pts[3]
        upper = eye_pts[1]
        lower = eye_pts[5]
        
        corner_y_mid = (outer[1] + inner[1]) / 2.0
        eye_height = lower[1] - upper[1]
        
        if eye_height < 3:
            return 0.5
        
        offset = iris_center[1] - corner_y_mid
        return offset / eye_height
    
    def _get_gaze_direction(self, h_ratio, v_ratio):
        """Convert gaze ratios to direction string."""
        horizontal = "CENTER"
        vertical = "CENTER"
        
        if h_ratio < self.gaze_horizontal_thresh:
            horizontal = "LEFT"
        elif h_ratio > (1.0 - self.gaze_horizontal_thresh):
            horizontal = "RIGHT"
        
        if v_ratio < self.gaze_vertical_thresh:
            vertical = "UP"
        elif v_ratio > (1.0 - self.gaze_vertical_thresh):
            vertical = "DOWN"
        
        if vertical == "CENTER" and horizontal == "CENTER":
            return "CENTER"
        elif vertical == "CENTER":
            return horizontal
        elif horizontal == "CENTER":
            return vertical
        else:
            return f"{vertical}-{horizontal}"
    
    def _process_blink_state(self, eyes_closed):
        """
        Process blink state machine.
        Returns: "BLINK", "DOUBLE_BLINK", "LONG_BLINK", or None
        """
        event = None
        
        if eyes_closed:
            self.frames_eyes_closed += 1
            
            if self.frames_eyes_closed >= self.blink_consec_frames and not self.blink_in_progress:
                self.blink_in_progress = True
            
            if self.frames_eyes_closed == self.long_blink_frames:
                self.long_blink_count += 1
                event = "LONG_BLINK"
        else:
            if self.blink_in_progress:
                self.blink_in_progress = False
                current_time = time.time()
                
                if self.frames_eyes_closed >= self.long_blink_frames:
                    pass  # Already counted
                else:
                    self.blink_count += 1
                    
                    if current_time - self.last_blink_time < self.double_blink_window:
                        self.double_blink_count += 1
                        event = "DOUBLE_BLINK"
                    else:
                        event = "BLINK"
                    
                    self.last_blink_time = current_time
            
            self.frames_eyes_closed = 0
        
        return event
    
    @staticmethod
    def _distance(p1, p2):
        """Euclidean distance between two points."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
