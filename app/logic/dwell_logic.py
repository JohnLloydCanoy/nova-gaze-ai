import time
import pyautogui

class DwellManager:
    def __init__(self, dwell_time=1.5, threshold=0.1):
        """
        dwell_time: Seconds to look at a spot before clicking.
        threshold: How much the eye can 'wiggle' before the timer resets.
        """
        self.dwell_time = dwell_time
        self.threshold = threshold
        
        # State tracking
        self.last_gaze_pos = (0.5, 0.5)
        self.start_time = time.time()
        self.action_triggered = False

    def update(self, gaze_h, gaze_v):
        """Processes raw iris ratios to check for dwell intent."""
        
        # 1. Calculate how much the eye has moved since the last frame
        dist_h = abs(gaze_h - self.last_gaze_pos[0])
        dist_v = abs(gaze_v - self.last_gaze_pos[1])

        # 2. Check if the eye is 'staying still' within the threshold
        if dist_h < self.threshold and dist_v < self.threshold:
            elapsed = time.time() - self.start_time
            
            # 3. If they stare long enough, trigger the click
            if elapsed >= self.dwell_time and not self.action_triggered:
                self.execute_click()
                self.action_triggered = True
        else:
            # Eye moved too much; reset the timer
            self.start_time = time.time()
            self.last_gaze_pos = (gaze_h, gaze_v)
            self.action_triggered = False

    def execute_click(self):
        print("[Nova Logic] Dwell detected: Triggering Selection")
        pyautogui.click()