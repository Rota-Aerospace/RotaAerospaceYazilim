import cv2
import numpy as np

yakala = cv2.VideoCapture(0)

while True :
    deger , kare = yakala.read()

    cv2.imshow("ben", kare )
    a = cv2.waitKey(1)

    if a == 27 :
        break

    elif a == ord("s") :
        cv2.imwrite("kayıt1",yakala)

yakala.release
cv2.destroyAllWindows




