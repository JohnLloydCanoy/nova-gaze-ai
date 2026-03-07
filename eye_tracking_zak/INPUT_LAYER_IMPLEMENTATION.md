# Nova-Gaze Input Layer — Implementation Summary

**Date:** Session documentation  
**Purpose:** Track implementation progress for team handoff

---

## Quick Start

```powershell
# Run the app
cd "c:\Users\Zach Alfred\Desktop\NovaGaze\nova-gaze-ai"
.\venv\Scripts\python.exe main.py
```

The app will:
1. Open camera, start auto-calibration (~2 seconds)
2. Show "Calibrating... Look straight ahead" overlay
3. After calibration, cyan gaze dot appears and follows your eyes
4. Blink detection active — dot pulses on blink events

---

## Changelog — Files Added/Modified

###  NEW FILES

| File | Purpose |
|------|---------|
| `app/logic/eye_tracker.py` | Central eye tracking class — gaze direction, blink detection, auto-calibration |
| `app/components/gaze_dot.py` | `GazeDot` widget (cyan cursor) + `CalibrationOverlay` widget |
| `test_mediapipe.py` | Standalone test script for debugging tracking |
| `face_landmarker.task` | MediaPipe model file (auto-downloaded) |
| `docs/EYE_GAZE_LOGIC_PLAN.md` | Design document for Input Layer |

### MODIFIED FILES

| File | Changes |
|------|---------|
| `app/vision/camera.py` | Added eye tracking integration, Qt signals for gaze/blink/calibration |
| `app/layout.py` | Connected to eye tracking signals, creates gaze dot overlay |

---

## Phase-by-Phase Implementation

### Phase 1: MediaPipe Face Landmarks ✅

**Problem:** MediaPipe 0.10.x breaking changes  
- Old API: `mp.solutions.face_mesh` — **NO LONGER EXISTS**
- New API: `mediapipe.tasks.python.vision.FaceLandmarker`

**Solution:** Complete rewrite using new Tasks API

```python
# OLD (broken in 0.10.x)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(...)

# NEW (working)
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(model_asset_path="face_landmarker.task")
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.FaceLandmarker.create_from_options(options)

# Usage
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
result = detector.detect(mp_image)
```

**Model file:** Downloads automatically from Google Storage on first run.

---

### Phase 2: Eye Aspect Ratio (EAR) ✅

**Landmark indices:**
```python
RIGHT_EYE = [33, 159, 158, 133, 153, 145]  # outer, upper2, upper1, inner, lower1, lower2
LEFT_EYE = [362, 380, 374, 263, 386, 385]
```

**EAR Formula:**
```
EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
```

Where p1-p6 are the eye landmark points. Closed eyes → low EAR (~0.15), open eyes → high EAR (~0.25+).

**Threshold:** `ear_threshold = 0.20`

---

### Phase 3: Blink Detection State Machine ✅

**Detects:**
- **Single blink:** Eyes closed < 0.5 seconds
- **Double blink:** Two single blinks within 0.4 seconds
- **Long blink:** Eyes closed > 0.5 seconds (~15 frames at 30fps)

**State machine logic in `eye_tracker.py`:**
```python
def _process_blink_state(self, eyes_closed):
    if eyes_closed:
        self.frames_eyes_closed += 1
        if self.frames_eyes_closed == self.long_blink_frames:
            return "LONG_BLINK"
    else:
        if self.blink_in_progress:
            # Eyes just opened
            if self.frames_eyes_closed >= self.blink_consec_frames:
                if self.frames_eyes_closed < self.long_blink_frames:
                    # Check for double blink
                    now = time.time()
                    if now - self.last_blink_time < self.double_blink_window:
                        return "DOUBLE_BLINK"
                    else:
                        return "BLINK"
            self.frames_eyes_closed = 0
    return None
```

---

### Phase 4: Gaze Direction (Eyes-Only) ✅

**CRITICAL:** This must be EYES-ONLY tracking. ALS/paralysis patients cannot move their heads — only their eyes.

**Problem with head-based approach:**
- Initial implementation used head pose rotation (pitch angle)
- This doesn't work for users who can't move their heads!

**Solution:** Iris-only tracking with auto-calibration

**Iris landmarks:**
```python
RIGHT_IRIS = [468, 469, 470, 471, 472]  # 468 is center
LEFT_IRIS = [473, 474, 475, 476, 477]   # 473 is center
```

**Horizontal gaze:** Iris position relative to eye corners (straightforward)
```python
def _calculate_horizontal_gaze(self, eye_pts, iris_center):
    outer = eye_pts[0]  # Outer corner
    inner = eye_pts[3]  # Inner corner
    eye_width = inner[0] - outer[0]
    ratio = (iris_center[0] - outer[0]) / eye_width
    return max(0.0, min(1.0, ratio))  # 0=left, 0.5=center, 1=right
```

**Vertical gaze:** This was HARD because eye opening height changes with blinks

**Why it's tricky:**
- Iris Y position is measured relative to eye opening
- When looking down, eyelids also droop slightly
- RAW iris ratio has very small variance (~0.02 range)

**Solution: Auto-calibration + Amplification**
```python
# During first ~60 frames, collect samples while user looks straight
if not self.calibration_complete:
    self.calibration_samples.append(avg_v_raw)
    if len(self.calibration_samples) >= self.calibration_frames:
        self.baseline_iris_y = sum(self.calibration_samples) / len(self.calibration_samples)
        self.calibration_complete = True

# Apply calibration: measure deviation from baseline, amplify 8x
deviation = avg_v_raw - self.baseline_iris_y
amplified = deviation * 8.0  # Small movements → big cursor movements
gaze_v = max(0.0, min(1.0, 0.5 + amplified))
```

**Direction thresholds:**
```python
gaze_horizontal_thresh = 0.35  # < 0.35 = LEFT, > 0.65 = RIGHT
gaze_vertical_thresh = 0.40    # < 0.40 = UP, > 0.60 = DOWN
```

---

### Phase 5: App Integration ✅

**Signal architecture:**

```
CameraThread (QThread)
    │
    ├── Captures frames at ~30 fps
    ├── Calls eye_tracker.process_frame(rgb_frame)
    │
    └── Emits Qt Signals:
          ├── gaze_signal(float, float, str)     → h_ratio, v_ratio, direction
          ├── blink_signal(str)                   → "BLINK" / "DOUBLE_BLINK" / "LONG_BLINK"
          ├── calibration_signal(bool, float)     → is_calibrating, progress
          └── tracking_data_signal(dict)          → Full tracking dict for advanced use
```

**Connecting to signals (in layout.py):**
```python
# In MainWindow.__init__:
self.camera_feed.gaze_signal.connect(self.on_gaze)
self.camera_feed.blink_signal.connect(self.on_blink)
self.camera_feed.calibration_signal.connect(self.on_calibration)

def on_gaze(self, h, v, direction):
    screen = self.screen().geometry()
    self.gaze_dot.set_gaze_position(h, v, screen.width(), screen.height())

def on_blink(self, event):
    self.gaze_dot.pulse_on_blink()
    print(f"[Blink] {event}")

def on_calibration(self, is_calibrating, progress):
    self.gaze_dot.set_calibrating(is_calibrating)
    self.calibration_overlay.set_calibrating(is_calibrating)
```

---

### Phase 6: Visual Gaze Dot ✅

**GazeDot widget features:**
- Cyan gradient with white center
- Click-through (doesn't intercept mouse events)
- Smooth movement with exponential moving average
- Pulse animation on blink

**Key code:**
```python
class GazeDot(QWidget):
    def set_gaze_position(self, h_ratio, v_ratio, screen_width, screen_height):
        # Convert ratios to screen coordinates
        self._target_x = int(h_ratio * screen_width) - self.dot_size // 2
        self._target_y = int(v_ratio * screen_height) - self.dot_size // 2
        
        # Apply smoothing (exponential moving average)
        self._current_x += (self._target_x - self._current_x) * self._smoothing
        self._current_y += (self._target_y - self._current_y) * self._smoothing
        
        self.move(int(self._current_x), int(self._current_y))
```

**CalibrationOverlay:** Shows "Calibrating... Look straight ahead" during calibration, fades out when complete.

---

## Issues Encountered & Fixes

### Issue 1: ModuleNotFoundError for mediapipe.solutions
**Error:** `AttributeError: module 'mediapipe' has no attribute 'solutions'`  
**Cause:** MediaPipe 0.10.x removed the `solutions` module entirely  
**Fix:** Rewrote to use new Tasks API (`FaceLandmarker`)

### Issue 2: Model not found
**Error:** `RuntimeError: Unable to open file at face_landmarker.task`  
**Fix:** Added auto-download in `EyeTracker._ensure_model_exists()`

### Issue 3: Vertical gaze stuck on "DOWN"
**Cause:** Used head pose pitch angle for vertical gaze  
**Why bad:** ALS patients can't move their heads!  
**Fix:** Rewrote to use iris-only vertical tracking with calibration

### Issue 4: Iris Y movements too small to detect
**Cause:** Raw iris vertical ratio only varies by ~0.02  
**Fix:** Auto-calibration baseline + 8x amplification

### Issue 5: Running wrong Python executable
**Symptom:** `ModuleNotFoundError: No module named 'mediapipe'`  
**Cause:** Using system Python instead of venv  
**Fix:** Always use `.\venv\Scripts\python.exe`

---

## What's Working Well

1. **Face detection:** Stable MediaPipe tracking, ~30 fps
2. **Blink detection:** Single/double/long blinks detected reliably
3. **Horizontal gaze:** Left/right detection works well
4. **Auto-calibration:** Sets baseline automatically, no manual step needed
5. **Visual feedback:** Gaze dot moves smoothly, pulses on blink
6. **Signal architecture:** Clean separation between tracking and UI

---

## What's Left To Do

### Must Have (P0)
- [ ] **Dwell detection:** Detect when user looks at same spot for N seconds
- [ ] **Gesture engine:** Map blinks + gaze to actions (CLICK, SCROLL, etc.)
- [ ] **Connect to Reasoning Layer:** Hand off events to the Nova AI team

### Should Have (P1)
- [ ] **Predictive Action Menu:** Popup menu near gaze point (see Section 5.2 in design doc)
- [ ] **Manual calibration:** 9-point calibration for more accuracy
- [ ] **Wink detection:** Distinguish left vs right eye blink

### Nice to Have (P2)
- [ ] **Sensitivity settings:** Let user adjust thresholds
- [ ] **Persist calibration:** Save/load calibration profile
- [ ] **Head movement adaptation:** For users who CAN move their heads, use that data too

---

## Testing the Implementation

### Quick test (standalone):
```powershell
cd "c:\Users\Zach Alfred\Desktop\NovaGaze\nova-gaze-ai"
.\venv\Scripts\python.exe test_mediapipe.py
```
This opens a debug window showing landmarks, EAR values, gaze direction.

### Full app test:
```powershell
.\venv\Scripts\python.exe main.py
```
Overlay appears with camera feed (40% opacity) and gaze dot.

### What to verify:
1. Camera feed shows in top-left
2. "Calibrating..." message appears for ~2 seconds
3. After calibration, cyan dot appears
4. Dot follows eye movement (left/right should be responsive)
5. Blink causes dot to pulse
6. Check console for blink events

---

## File Reference

### app/logic/eye_tracker.py
- **Class:** `EyeTracker`
- **Main method:** `process_frame(rgb_frame)` → returns tracking dict
- **Calibration:** Auto-calibrates during first 60 frames
- **Reset:** Call `reset_calibration()` to recalibrate

### app/vision/camera.py
- **Class:** `CameraThread` — QThread that captures video + processes tracking
- **Class:** `CameraFeedWidget` — Widget that displays feed + exposes signals
- **Signals:** `gaze_signal`, `blink_signal`, `calibration_signal`, `tracking_data_signal`

### app/components/gaze_dot.py
- **Class:** `GazeDot` — Visual gaze cursor
- **Class:** `CalibrationOverlay` — "Calibrating..." message

### app/layout.py
- **Connects:** Camera signals to gaze dot
- **Handlers:** `on_gaze()`, `on_blink()`, `on_calibration()`

---

## For Next Team Member(KAMO NA BAHALA)

1. **Read this doc first** — gives you the full picture
2. **Run `test_mediapipe.py`** — see the raw tracking data
3. **Next priority:** Implement dwell detection (P0)
4. **Key insight:** Vertical tracking uses iris-only with calibration — don't try to use head pose!
5. **Ask me** if you need context on why something was done a certain way

Good luck! 
