# Nova-Gaze: Eye Gaze Logic — Design Document

> Planning Phase  


---

## 1. Overview

Our team is responsible for turning raw webcam frames into **meaningful user actions**. We take video input, extract eye/face landmarks via MediaPipe, and output structured events like "click", "scroll up", or "move cursor to (x, y)".

The other teams consume our output:
- **Reasoning Layer** receives our gaze coordinates + gesture events to determine user intent
- **Execution Layer** acts on the intent (clicking buttons, filling forms, etc.)

---

## 2. Data Flow

```
┌──────────┐    ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Webcam   │───▶│  MediaPipe   │───▶│  Gaze Pipeline   │───▶│  Event Output    │
│  (OpenCV) │    │  FaceMesh    │    │                  │    │                  │
│           │    │  468+ points │    │  • EAR (blink)   │    │  • CLICK         │
│  30 fps   │    │  + iris      │    │  • Iris → screen │    │  • SCROLL_UP     │
│           │    │              │    │  • Dwell timer   │    │  • SCROLL_DOWN   │
└──────────┘    └──────────────┘    │  • Gesture FSM   │    │  • MOVE(x, y)    │
                                    └──────────────────┘    │  • CANCEL        │
                                                            │  • CONFIRM       │
                                                            └──────────────────┘
```

---

## 3. MediaPipe Landmarks We Use

MediaPipe FaceMesh with `refine_landmarks=True` gives us **478 landmarks**. We care about these subsets:

### 3.1 Eye Contour Landmarks (for EAR / blink detection)
| Eye   | Landmark Indices                     | Purpose                   |
|-------|--------------------------------------|---------------------------|
| Right | `[33, 159, 158, 133, 153, 145]`     | EAR blink detection       |
| Left  | `[362, 380, 374, 263, 386, 385]`    | EAR blink detection       |

**Ordering for EAR formula:**
```
Index 0 = outer corner,  Index 3 = inner corner  (horizontal)
Index 1 = upper lid (outer), Index 2 = upper lid (inner)  (vertical top)
Index 5 = lower lid (outer), Index 4 = lower lid (inner)  (vertical bottom)
```

### 3.2 Iris Landmarks (for gaze direction)
| Eye   | Landmark Indices     | Purpose              |
|-------|----------------------|----------------------|
| Right | `[468, 469, 470, 471, 472]` | Right iris (center = 468) |
| Left  | `[473, 474, 475, 476, 477]` | Left iris (center = 473)  |

### 3.3 Eye Corner Landmarks (for relative iris position)
| Point              | Right Eye | Left Eye |
|--------------------|-----------|----------|
| Inner corner       | 133       | 362      |
| Outer corner       | 33        | 263      |

---

## 4. Core Computations

### 4.1 Eye Aspect Ratio (EAR) — Blink Detection

**Already in `tracker.py`** (Vince's v1).

```
EAR = (|v1| + |v2|) / (2 * |h|)
```

- **Open eye:** EAR ≈ 0.25–0.30
- **Closed eye:** EAR < 0.20 (threshold to tune)

**Key thresholds to calibrate:**
| Parameter                | Default Value | What it controls                          |
|--------------------------|---------------|-------------------------------------------|
| `EAR_BLINK_THRESHOLD`   | 0.20          | EAR below this = "eye closed"             |
| `BLINK_CONSEC_FRAMES`   | 2             | Minimum frames eyes must be closed = blink|
| `LONG_BLINK_FRAMES`     | 15 (~0.5s)    | Frames closed before it's a "long blink"  |
| `DOUBLE_BLINK_WINDOW`   | 10 (~0.33s)   | Max frames between blinks for double-blink|

### 4.2 Gaze Direction — Iris Relative Position

To know WHERE the user is looking, we compute the **iris position relative to the eye corners**:

```
          iris_x - inner_corner_x
ratio = ───────────────────────────
         outer_corner_x - inner_corner_x
```

| Ratio Value       | Meaning         |
|--------------------|-----------------|
| 0.0 – 0.35        | Looking RIGHT   |
| 0.35 – 0.65       | Looking CENTER  |
| 0.65 – 1.0        | Looking LEFT    |

> Same idea applies vertically using upper/lower eyelid landmarks.

### 4.3 Gaze-to-Screen Coordinate Mapping

This is the hardest part. We need **calibration** to map eye gaze ratios → actual screen pixel positions.

**Calibration approach:**
1. Show dots at 9 known screen positions (3×3 grid)
2. User looks at each dot for 2 seconds
3. Record iris ratios at each position
4. Build a mapping function (linear interpolation or polynomial regression)

```
screen_x = map(iris_horizontal_ratio, calibration_data)  
screen_y = map(iris_vertical_ratio, calibration_data)
```

### 4.4 Dwell Detection

A **dwell** = gaze stays within a small radius for a sustained time.

| Parameter            | Default Value | Purpose                                   |
|----------------------|---------------|-------------------------------------------|
| `DWELL_RADIUS_PX`   | 50 px         | Max movement to still count as "dwelling" |
| `DWELL_TIME_MS`     | 800 ms        | Time to trigger a dwell event             |
| `DWELL_COOLDOWN_MS` | 500 ms        | Cooldown after a dwell fires              |

**Logic:**
```
if distance(current_gaze, dwell_anchor) < DWELL_RADIUS:
    if elapsed_time > DWELL_TIME:
        fire DWELL event
        start cooldown
else:
    reset dwell_anchor to current_gaze
    reset timer
```

---

## 5. Gesture-to-Action Mapping (mostly na ambag)

This is what our module outputs to the rest of the system:

| Gesture                        | How Detected                                        | Action         | Use Case                          |
|--------------------------------|-----------------------------------------------------|----------------|-----------------------------------|
| **Dwell**                      | Gaze stays in place > 800ms                         | `HOVER_SELECT` | Highlight a UI element            |
| **Blink** (both eyes)          | EAR drops below threshold for 2-3 frames            | `CLICK`        | Confirm / click a button          |
| **Double Blink**               | Two blinks within 0.33s                             | `RIGHT_CLICK`  | Open context menu                 |
| **Long Blink** (>0.5s)         | EAR below threshold for 15+ frames                  | `CANCEL`       | Dismiss / go back                 |
| **Dwell + Blink**              | Dwell fires, then blink within 0.5s                 | `CONFIRM`      | Most reliable "I want to click this" |
| **Look Left** (sustained)      | Horizontal ratio < 0.35 for > 0.5s                  | `SCROLL_LEFT`  | Navigate back / scroll left       |
| **Look Right** (sustained)     | Horizontal ratio > 0.65 for > 0.5s                  | `SCROLL_RIGHT` | Navigate forward / scroll right   |
| **Look Up** (sustained)        | Vertical ratio shifted up for > 0.5s                | `SCROLL_UP`    | Scroll page up                    |
| **Look Down** (sustained)      | Vertical ratio shifted down for > 0.5s              | `SCROLL_DOWN`  | Scroll page down                  |
| **Wink Left**                  | Only left EAR drops (right stays open)              | `MODIFIER_L`   | Reserved for future use           |
| **Wink Right**                 | Only right EAR drops (left stays open)              | `MODIFIER_R`   | Reserved for future use           |

### 5.1 Safety: Distinguishing Intentional vs Natural Blinks

Natural blinks are ~100–150ms. We use:
- **Minimum closed duration** (2 frames at 30fps ≈ 66ms) to filter noise
- **Dwell + Blink combo** as the primary interaction — a blink only counts as a "click" if the user was already dwelling on something
- **Cooldown timers** to prevent rapid-fire accidental triggers

### 5.2 Predictive Action Menu (Quick Actions Popup)

A floating menu that appears to help users when the system needs clarification or when manually triggered.

#### When It Appears

| Trigger                          | Description                                              |
|----------------------------------|----------------------------------------------------------|
| **Uncertainty**                  | System detects dwell but isn't sure what user wants (e.g., gaze between two buttons) |
| **Look at corner** (manual)      | User looks at a designated screen corner for 0.5s to summon it |
| **Ambiguous context**            | Multiple clickable elements near gaze position           |

#### Menu Options (Basic Navigation)

The menu shows 3-5 action buttons, each with the gesture instruction:

```
┌─────────────────────────────────────────────────────┐
│              What would you like to do?             │
├─────────────────────────────────────────────────────┤
│                                                     │
│   [ 👆 Click here ]         ← Blink to select       │
│                                                     │
│   [ ⬆️ Scroll Up ]          ← Look up to select     │
│                                                     │
│   [ ⬇️ Scroll Down ]        ← Look down to select   │
│                                                     │
│   [ ⬅️ Go Back ]            ← Look left to select   │
│                                                     │
│   [ ❌ Cancel ]              ← Long blink to close   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Selection Methods (depends on choice)

| Menu Option       | How to Select                     | Why this gesture              |
|-------------------|-----------------------------------|-------------------------------|
| Click here        | Dwell on option + Blink           | Confirms intentional click    |
| Scroll Up         | Look up (sustained 0.5s)          | Intuitive — look in direction |
| Scroll Down       | Look down (sustained 0.5s)        | Intuitive — look in direction |
| Go Back           | Look left (sustained 0.5s)        | Intuitive — "back" is left    |
| Cancel/Dismiss    | Long blink (0.5s)                 | Universal "nevermind" gesture |

#### Smart Suggestions (Future: learns from patterns)

The system remembers what user did before in similar situations:

| Context                              | Suggested First Option                  |
|--------------------------------------|-----------------------------------------|
| On a form, looking near "Submit"     | "Click Submit button"                   |
| At bottom of page                    | "Scroll Down" (or "Go to next page")    |
| Popup appeared                       | "Close popup" / "Click X"               |
| Previously clicked same button       | Show that button first next time        |

#### Menu Parameters

| Parameter               | Default Value | Purpose                                     |
|-------------------------|---------------|---------------------------------------------|
| `MENU_TRIGGER_CORNER`   | Top-right     | Which corner summons the menu               |
| `MENU_CORNER_DWELL_MS`  | 500 ms        | How long to look at corner to trigger       |
| `MENU_TIMEOUT_MS`       | 5000 ms       | Auto-dismiss if no selection made           |
| `MENU_OPTION_DWELL_MS`  | 600 ms        | Dwell time on an option before highlight    |

#### UI Component: `ActionMenuWidget`

- Semi-transparent popup (similar style to the top control tab)
- Appears near gaze position but not blocking it
- Each option shows: icon + label + gesture hint
- Highlighted option has visual feedback (glow/border)
- Dismisses after selection or timeout

---

## 6. Components to Build

### 6.1 Module Structure

```
app/
  vision/
    __init__.py
    camera.py            ← ✅ DONE — Camera thread + feed widget (from merged branch)
  setting/
    __init__.py
    config.py            ← ✅ DONE — Env config for Nova API keys (from merged branch)
  components/
    __init__.py
    tab.py               ← ✅ DONE — Top control tab widget
    button.py            ← (empty for now)
    action_menu.py       ← NEW: Predictive Action Menu popup widget
  logic/
    __init__.py
    tracker.py           ← Needs rewrite: hook MediaPipe into existing CameraThread
    blink_detector.py    ← EAR-based blink/wink state machine
    gaze_estimator.py    ← Iris → screen coordinate mapping
    dwell_detector.py    ← Fixation / dwell detection
    gesture_engine.py    ← Combines all signals → outputs action events
    calibration.py       ← 9-point calibration routine
    action_predictor.py  ← NEW: Logic for when to show menu + smart suggestions
```

> **Note:** `camera.py` already handles the webcam in a QThread. Our gaze logic
> must process frames FROM that thread — do NOT open a second `cv2.VideoCapture`.

### 6.2 Component Descriptions

| Component            | Input                        | Output                          | Priority | Status   |
|----------------------|------------------------------|---------------------------------|----------|----------|
| `camera.py`          | Webcam (cv2)                 | Raw frames via Qt signal        | P0       | ✅ Done  |
| `tracker.py`         | Frames from CameraThread     | Raw landmarks (478 points)      | P0       | Needs rewrite |
| `blink_detector.py`  | Eye landmarks (12 points)    | Blink events (single/double/long/wink) | P0 | Not started |
| `gaze_estimator.py`  | Iris + eye corner landmarks  | Screen coordinates (x, y)       | P0       | Not started |
| `dwell_detector.py`  | Screen coordinates stream    | Dwell events (position + duration) | P1    | Not started |
| `gesture_engine.py`  | All detector outputs         | Final action events             | P1       | Not started |
| `action_menu.py`     | Show/hide signal + options   | User's selected action          | P1       | Not started |
| `action_predictor.py`| Gaze context + history       | When to show menu + suggestions | P2       | Not started |
| `calibration.py`     | User looking at dots         | Calibration mapping data        | P2       | Not started |

**Priority Key:** P0 = must have for basic demo, P1 = must have for full demo, P2 = nice to have

### 6.3 Event Format

Every action we emit should follow a consistent structure:

```python
@dataclass
class GazeEvent:
    type: str          # "CLICK", "SCROLL_UP", "HOVER_SELECT", etc.
    x: int             # Screen pixel X
    y: int             # Screen pixel Y  
    confidence: float  # 0.0 – 1.0 (how sure we are)
    timestamp: float   # time.time()
```

---

## 7. Implementation Order

```
Step 1:  ✅ camera.py — Camera thread is running (done by teammate)
            ↓
Step 2:  tracker.py — Add MediaPipe processing INTO existing CameraThread
            ↓
Step 3:  blink_detector.py — Detect blinks using EAR (build on Vince gwapo's work)
            ↓
Step 4:  gaze_estimator.py — Get iris ratios, basic center/left/right detection
            ↓
Step 5:  Wire into UI — Show a gaze dot on the overlay, react to blinks
            ↓
Step 6:  dwell_detector.py — Add fixation detection
            ↓
Step 7:  gesture_engine.py — Combine everything into action events
            ↓
Step 8:  action_menu.py — Build the Predictive Action Menu UI component
            ↓
Step 9:  action_predictor.py — Logic for when to show menu + remember patterns
            ↓
Step 10: calibration.py — 9-point calibration for accurate screen mapping
            ↓
Step 11: Hand off GazeEvent stream to Reasoning Layer team
```

---

## 8. Integration with PySide6 UI

The camera already runs in a **separate QThread** (`CameraThread` in `camera.py`).
We add our gaze processing into that same thread — no need to create a new one.

```
Main Thread (PySide6 event loop)
    │
    ├── Overlay Window (transparent, always-on-top)
    │     ├── CameraFeedWidget (top-left, 40% opacity) ← ✅ Already working
    │     ├── Gaze cursor dot (updated via signal)     ← To build
    │     └── ActionMenuWidget (popup near gaze)       ← To build (Section 5.2)
    │
    └── CameraThread (QThread) — already in camera.py
          ├── Camera capture loop (30 fps)             ← ✅ Already working
          ├── MediaPipe landmark extraction             ← To add
          ├── Blink / Gaze / Dwell detection            ← To add
          └── Emits Qt Signals → Main Thread
               • change_pixmap_signal(QImage)           ← ✅ Already working
               • landmarks_signal(landmarks)            ← To add
               • gaze_moved(x, y)                       ← To add
               • action_triggered(GazeEvent)            ← To add
               • show_action_menu(options, position)    ← To add (for Predictive Menu)
               • menu_option_selected(action)           ← To add (user picked an option)
```

---

## 9. Known Challenges & Mitigations

| Challenge                          | Mitigation                                              |
|------------------------------------|---------------------------------------------------------|
| Head movement shifts gaze reading  | Use head pose estimation to compensate iris offset       |
| Lighting variation affects tracking| MediaPipe is fairly robust; add histogram equalization if needed |
| Natural blinks trigger false clicks| Use dwell+blink combo, not standalone blink              |
| Calibration drifts over time       | Allow quick re-calibration (look at center point)        |
| Low-spec webcam = low FPS          | Target 15fps minimum; reduce MediaPipe complexity if needed |
| User fatigue from sustained gaze   | Add rest mode (e.g., close eyes 2s = pause tracking)    |
| Action menu appears too often      | Only show on uncertainty or manual trigger (corner look) |
| Menu blocks what user wants to see | Position menu offset from gaze, make it semi-transparent |
| Wrong suggestion shown first       | Learn from history; most-used action bubbles to top      |

---

## 10. Testing Plan

| Test                          | Method                                             |
|-------------------------------|----------------------------------------------------|
| EAR values are correct        | Print EAR while opening/closing eyes               |
| Blink detection works         | Count blinks vs. actual blinks over 30 seconds     |
| Gaze left/right/center        | Look at screen edges, verify ratios                |
| Dwell fires reliably          | Stare at a point, confirm event fires at ~800ms    |
| No false triggers             | Use normally for 60s, count unintended events      |
| Thread doesn't block UI       | Resize/drag overlay while tracker runs             |
| Action menu appears on corner | Look at top-right corner for 0.5s → menu shows    |
| Menu option selection works   | Look at "Scroll Up" + hold → action triggers       |
| Menu dismisses on long blink  | Open menu, long blink → menu closes                |
| Menu timeout works            | Open menu, do nothing for 5s → auto-dismiss        |

---

## Appendix: MediaPipe Eye Landmark Diagram

```
        1 (159)          2 (158)          ← Upper eyelid
       /                      \
0 (33) ──────── iris ────────── 3 (133)  ← Right eye
       \                      /
        5 (145)          4 (153)          ← Lower eyelid

        1 (380)          2 (374)          ← Upper eyelid
       /                      \
0 (362) ──────── iris ────────── 3 (263)  ← Left eye
       \                      /
        5 (386)          4 (385)          ← Lower eyelid
```

# UPDATE
Last Updated: March 6, 2026