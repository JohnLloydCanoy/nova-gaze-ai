def __init__(self):
        super().__init__()
        self._run_flag = True
        # Ensure we use EyeTracker (New API) not GazeTracker (Old API)
        self.eye_tracker = EyeTracker()