import time
import math

class DwellManager:
    def __init__(self, dwell_time=0.8, threshold=0.05):
        """
        dwell_time: Seconds to stay in spot (Design Doc says 800ms).
        threshold: The 'wiggle room' for the iris ratio.
        """
        self.dwell_time = dwell_time
        self.threshold = threshold
        
        # State tracking
        self.last_gaze_pos = (0.5, 0.5)
        self.start_time = time.time()
        self.is_locked = False

    def update(self, gaze_h, gaze_v):
        """
        Processes iris ratios to check for dwell intent.
        Returns: (is_locked, progress_percentage)
        """
        now = time.time()
        
        # 1. Calculate movement distance (Euclidean)
        dist = math.sqrt((gaze_h - self.last_gaze_pos[0])**2 + 
                         (gaze_v - self.last_gaze_pos[1])**2)

        # 2. Check if the eye is 'staying still'
        if dist < self.threshold:
            elapsed = now - self.start_time
            
            # Calculate progress for your debug dots (0.0 to 1.0)
            progress = min(elapsed / self.dwell_time, 1.0)
            
            if elapsed >= self.dwell_time:
                self.is_locked = True
            
            return self.is_locked, progress
        else:
            # Gaze moved; reset everything
            self.start_time = now
            self.last_gaze_pos = (gaze_h, gaze_v)
            self.is_locked = False
            return False, 0.0

    def get_status_color(self):
        """Returns a color for the debug dots based on dwell state."""
        return (0, 255, 0) if self.is_locked else (0, 255, 255)