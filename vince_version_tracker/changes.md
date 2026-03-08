# March 8, 2026: by Vince Balaman

## 1. Background of this branch:
First and most important part, the old tracker.py uses the logic of the old mediapipe API that uses the .solutions logic which is outdated. In order to counter that we transition to the newer API logic which uses a a unified tasks framework, requiring imports from mediapipe.tasks.python.vision.
    -(In the old version, model weights were often bundled with the library or downloaded invisibly. In the new API, you must explicitly provide a compiled model asset, such as face_landmarker.task, and define its path in BaseOptions.)

## 2. About this version
Most updates in this version is about fixing this error and trying to merge this fix into the main branch

## 3. Process
    -In order to 'fix' this I have removed the tracker.py which is the root of the problems as it uses the old format (Trying to use the old API logic)
    -I used the eye_tracker.py to replace this module as it uses the new API logic
    -I then made different portable test module to test the eye_tracker module & test the integration of camera.py -> gaze_dot.py -> test_gaze_dot_logic.py

## 4. Running portable test modules
    -test_logic:
    .\venv\Scripts\python.exe -m app.logic.test_logic

    -test_gaze_dot_logic:
    .\venv\Scripts\python.exe -m app.logic.test_gaze_dot_logic 
    ***Note: test_gaze_dot_logic is only an integration, not the final product, so functionalities are limited and gaze pointer is not accurate and needs to be polished. It only recognizes vertical gazes and minimal horizontal gazes***   

## 5. Future changes
    -finalize the actions in eye_tracker
    -make the gaze_dot scanning smoother
    -fix the integration of camera and gaze_dot
    -integrate eye_tracker with Nove