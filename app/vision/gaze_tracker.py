import time
import math
import os
import urllib.request
import cv2
import mediapipe as mp


class GazeAnalyzer:
    FACE_LANDMARKER_MODEL_URL = (
        "https://storage.googleapis.com/mediapipe-models/"
        "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    )

    def __init__(self):
        self.face_mesh = None
        self.face_landmarker = None
        self.face_mesh_available = False
        self.face_landmarker_available = False
        self.pipeline_name = "DISABLED"
        self.pipeline_reason = "No compatible MediaPipe face backend found"

        if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                self.face_mesh_available = True
                self.pipeline_name = "FaceMesh"
                self.pipeline_reason = ""
            except Exception as exc:
                self.pipeline_reason = f"FaceMesh init failed: {exc}"

        # Fallback for environments where `mp.solutions.face_mesh` is unavailable.
        if not self.face_mesh_available and hasattr(mp, "tasks"):
            self._init_face_landmarker_tasks()

        self.session_active = False

        # State tracking
        self.current_state = "CENTER"
        self.state_start_time = time.time()

        # Forgiving Thresholds
        self.EAR_BLINK_THRESHOLD = 0.12
        self.UP_THRESHOLD = -0.15
        self.DOWN_THRESHOLD = 0.18
        self.RIGHT_THRESHOLD = 0.15
        self.RIGHT_HOLD_SECONDS = 5.0

    def _get_face_landmarker_model_path(self):
        model_dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "models")
        os.makedirs(model_dir, exist_ok=True)
        return os.path.join(model_dir, "face_landmarker.task")

    def _ensure_face_landmarker_model(self):
        model_path = self._get_face_landmarker_model_path()
        if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
            return model_path

        try:
            with urllib.request.urlopen(self.FACE_LANDMARKER_MODEL_URL, timeout=20) as response:
                model_bytes = response.read()
            with open(model_path, "wb") as model_file:
                model_file.write(model_bytes)
            return model_path
        except Exception as exc:
            self.pipeline_reason = f"FaceLandmarker model download failed: {exc}"
            return None

    def _init_face_landmarker_tasks(self):
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
        except Exception as exc:
            self.pipeline_reason = f"MediaPipe Tasks import failed: {exc}"
            return

        model_path = self._ensure_face_landmarker_model()
        if not model_path:
            return

        try:
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(
                options)
            self.face_landmarker_available = True
            self.pipeline_name = "FaceLandmarker"
            self.pipeline_reason = ""
        except Exception as exc:
            self.pipeline_reason = f"FaceLandmarker init failed: {exc}"

    def _get_landmarks(self, frame):
        if self.face_mesh_available:
            results = self.face_mesh.process(frame)
            if results.multi_face_landmarks:
                return results.multi_face_landmarks[0].landmark
            return None

        if self.face_landmarker_available:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            results = self.face_landmarker.detect(mp_image)
            if results.face_landmarks:
                return results.face_landmarks[0]
            return None

        return None

    def _calculate_distance(self, point1, point2):
        """Helper function to calculate the 2D distance between two facial landmarks."""
        return math.hypot(point1.x - point2.x, point1.y - point2.y)

    def process_frame(self, frame):
        """
        Takes an RGB frame, analyzes the Eye Aspect Ratio, tracks time, 
        and returns any triggered events based on the user's gaze.
        """
        img_h, img_w = frame.shape[:2]

        if not (self.face_mesh_available or self.face_landmarker_available):
            status_text = f"GAZE: DISABLED [{self.pipeline_reason}]"
            return frame, None, status_text, 0.0

        new_state = "CENTER"
        event_to_emit = None
        progress = 0.0

        landmarks = self._get_landmarks(frame)

        if landmarks:
            if len(landmarks) <= 473:
                status_text = f"GAZE: DISABLED [{self.pipeline_name} missing iris landmarks]"
                return frame, None, status_text, 0.0

            # Extract Left Eye Landmarks
            iris = landmarks[473]
            eye_top = landmarks[159]
            eye_bottom = landmarks[145]
            eye_inner = landmarks[133]
            eye_outer = landmarks[33]

            # 1. Calculate Eye Aspect Ratio (EAR)
            eye_height = self._calculate_distance(eye_top, eye_bottom)
            eye_width = self._calculate_distance(eye_inner, eye_outer)

            if eye_height == 0:
                eye_height = 0.001
            if eye_width == 0:
                eye_width = 0.001

            ear = eye_height / eye_width

            # 2. Calculate Normalized Gaze Direction
            eye_center_y = (eye_top.y + eye_bottom.y) / 2
            eye_center_x = (eye_inner.x + eye_outer.x) / 2

            vertical_ratio = (iris.y - eye_center_y) / eye_height
            horizontal_ratio = (iris.x - eye_center_x) / eye_width

            # 3. Determine the current physical state
            if ear < self.EAR_BLINK_THRESHOLD:
                new_state = "CLOSED"
            else:
                if vertical_ratio < self.UP_THRESHOLD:
                    new_state = "UP"
                elif vertical_ratio > self.DOWN_THRESHOLD:
                    new_state = "DOWN"
                elif horizontal_ratio > self.RIGHT_THRESHOLD:
                    new_state = "RIGHT"

            # Visual UI Feedback: The dot on their eye turns Cyan when active, Gray when sleeping
            cx, cy = int(iris.x * img_w), int(iris.y * img_h)
            dot_color = (0, 229, 255) if self.session_active else (
                150, 150, 150)
            cv2.circle(frame, (cx, cy), 3, dot_color, -1)

        # --- TIME MANAGEMENT LOGIC ---
        if new_state != self.current_state:
            # The user looked somewhere else; reset the timer immediately
            self.current_state = new_state
            self.state_start_time = time.time()

        else:
            elapsed = time.time() - self.state_start_time

            # 1. The "Ignition Switch" (Can happen at any time)
            if new_state == "CLOSED":
                progress = min(elapsed / 5.0, 1.0)  # 5 seconds to trigger SCAN
                if elapsed >= 5.0:
                    event_to_emit = "SCAN"
                    self.session_active = True  # <--- WAKE UP THE SYSTEM
                    self.state_start_time = time.time()

            # 2. The Gaze Commands (ONLY run if the session is active!)
            elif self.session_active:
                if new_state == "UP":
                    progress = min(elapsed / 3.0, 1.0)
                    if elapsed >= 3.0:
                        event_to_emit = "SELECT_UP"
                        self.state_start_time = time.time()

                elif new_state == "DOWN":
                    progress = min(elapsed / 3.0, 1.0)
                    if elapsed >= 3.0:
                        event_to_emit = "SELECT_DOWN"
                        self.state_start_time = time.time()

                elif new_state == "RIGHT":
                    progress = min(elapsed / self.RIGHT_HOLD_SECONDS, 1.0)
                    if elapsed >= self.RIGHT_HOLD_SECONDS:
                        event_to_emit = "CLICK"
                        self.session_active = False  # <--- PUT SYSTEM BACK TO SLEEP AFTER CLICK
                        self.state_start_time = time.time()

        # Update the UI text so the user knows if the system is awake or asleep
        mode_text = "ACTIVE" if self.session_active else "AWAITING SCAN"
        status_text = f"GAZE: {new_state} [{mode_text} | {self.pipeline_name}]"

        return frame, event_to_emit, status_text, progress
