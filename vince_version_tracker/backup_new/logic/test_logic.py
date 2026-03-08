# test_logic.py
import cv2
from app.logic.eye_tracker import EyeTracker

def run_test():
    tracker = EyeTracker()
    cap = cv2.VideoCapture(0)

    print("Starting Logic Test. Press 'q' to quit.")
    print("Step 1: Calibration. Look straight at the camera...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # EyeTracker expects RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = tracker.process_frame(rgb_frame)

        if results['face_detected']:
            # Display tracking status
            status = f"Dir: {results['gaze_direction']} | EAR: {results['ear_avg']:.2f}"
            if results['calibrating']:
                status = f"CALIBRATING: {int(results['calibration_progress']*100)}%"
            
            if results['blink_event']:
                print(f"EVENT DETECTED: {results['blink_event']}")

            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Nova-Gaze Logic Debug", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_test()