# Eye Tracking Feature (Zak's Implementation)

This folder contains the accurate eye tracking system ready for integration.

## Files

| File | Purpose |
|------|---------|
| `eye_tracker.py` | Main tracking class - gaze direction, blinks, calibration |
| `gaze_dot.py` | Visual gaze cursor + calibration overlay widgets |
| `face_landmarker.task` | MediaPipe model file (3.7MB) |
| `INPUT_LAYER_IMPLEMENTATION.md` | Full documentation |
| `EYE_GAZE_LOGIC_PLAN.md` | Design document |

## How to Integrate

1. **Copy files to app:**
   ```
   eye_tracker.py → app/logic/eye_tracker.py
   gaze_dot.py → app/components/gaze_dot.py
   face_landmarker.task → project root
   ```

2. **In camera.py, use EyeTracker:**
   ```python
   from app.logic.eye_tracker import EyeTracker
   
   self.eye_tracker = EyeTracker()
   tracking = self.eye_tracker.process_frame(rgb_frame)
   ```

3. **Available signals:**
   - `gaze_signal(float, float, str)` → gaze_h, gaze_v, direction
   - `blink_signal(str)` → "BLINK", "DOUBLE_BLINK", "LONG_BLINK"
   - `calibration_signal(bool, float)` → is_calibrating, progress

4. **For the gaze dot:**
   ```python
   from app.components.gaze_dot import GazeDot, CalibrationOverlay
   
   self.gaze_dot = GazeDot(parent, size=50)
   self.gaze_dot.set_gaze_position(h, v, screen_width, screen_height)
   ```

## Key Features

- **Eyes-only tracking** - Works for ALS/paralysis patients who can only move eyes
- **Auto-calibration** - First 2 seconds calibrates neutral eye position
- **Accurate vertical gaze** - Uses iris position with 8x amplification
- **Single/double/long blink detection**

## Questions?

Ask Zak or see the documentation files in this folder.
