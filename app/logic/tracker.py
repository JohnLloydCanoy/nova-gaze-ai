import cv2
import mediapipe as mp
from scipy.spatial import distance as dist

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

def calculate_ear(eye_landmarks):

    # Vertical distances (need to test)
    v1 = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
    v2 = dist.euclidean(eye_landmarks[2], eye_landmarks[4])

    # Horizontal distance (need to test)
    h = dist.euclidean(eye_landmarks[0], eye_landmarks[3])
    return (v1 + v2) / (2.0 * h)

    #eyes are usually: Right Eye: [33, 159, 158, 133, 153, 145]
    #Left Eye: [362, 380, 374, 263, 386, 385]

cap = cv2.VideoCapture(0) #integrate into main.py to test

#make exception / try loop to test camera 

#loop body

cap.release()
cv2.destroyAllWindows()

#end of v1 initialization -vince