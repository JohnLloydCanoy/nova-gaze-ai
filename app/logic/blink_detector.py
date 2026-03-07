import time

class BlinkDetector:
    def __init__(self):
        # Thresholds from your EYE_GAZE_LOGIC_PLAN.md
        self.EAR_THRESHOLD = 0.20 
        self.BLINK_CONSEC_FRAMES = 2 
        self.LONG_BLINK_FRAMES = 15 
        self.DOUBLE_BLINK_WINDOW = 0.4  # Seconds between blinks

        self.closed_frames = 0
        self.last_blink_time = 0
        self.blink_ready_for_double = False
        self.blink_count = 0

    def update(self, avg_ear):
        """Processes EAR and returns 'CLICK', 'RIGHT_CLICK', or 'CANCEL'"""
        action = None
        current_time = time.time()

        if avg_ear < self.EAR_THRESHOLD:
            self.closed_frames += 1
            return None
        
        if self.closed_frames > 0:
            if self.closed_frames >= self.LONG_BLINK_FRAMES:
                action = "CANCEL"
                self.blink_ready_for_double = False
            elif self.closed_frames >= self.BLINK_CONSEC_FRAMES:
                # Check if this is the second part of a double blink
                if self.blink_ready_for_double and (current_time - self.last_blink_time <= self.DOUBLE_BLINK_WINDOW):
                    action = "RIGHT_CLICK"
                    self.blink_ready_for_double = False
                else:
                    action = "CLICK"
                    self.blink_ready_for_double = True
                    self.last_blink_time = current_time
            
            self.closed_frames = 0
            if action: self.blink_count += 1

        # Reset double blink window if too much time passes
        if self.blink_ready_for_double and (current_time - self.last_blink_time > self.DOUBLE_BLINK_WINDOW):
            self.blink_ready_for_double = False

        return action