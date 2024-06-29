from CameraManager import Camera
import cv2

cam = Camera()

frame, framehsv = cam.capture_array()

simplified_image = cam.simplify_image(framehsv, [0, 255, 0], [0, 0, 255])

# save the image
cv2.imwrite('simplified_image.jpg', simplified_image)
