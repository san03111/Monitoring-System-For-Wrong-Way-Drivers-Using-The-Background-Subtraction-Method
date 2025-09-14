import cv2
import numpy as np
import os
import Jetson.GPIO as GPIO
import pytesseract
import time
import re
import mysql.connector

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="san",
    passwd="qqqq",
    database="ta"
)
cursor = db.cursor()

# Video capture
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Change to your video source if needed

# Background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2(varThreshold=100, detectShadows=False)

# GPIO for buzzer
buzzer_pin = 12
GPIO.setmode(GPIO.BOARD)
GPIO.setup(buzzer_pin, GPIO.OUT)
GPIO.setwarnings(False)

def buzz_on():
    GPIO.output(buzzer_pin, GPIO.HIGH)

def buzz_off():
    GPIO.output(buzzer_pin, GPIO.LOW)

# Area definitions (example)
area1 = [(350, 273), (521, 449), (542, 425), (380, 261)]
area2 = [(391, 261), (546, 417), (561, 395), (423, 252)]

tracker = cv2.MultiTracker_create()
a1 = {}
counter = []
name = 1
name2 = 3
name3 = 3
path = "/var/www/html/Web"

# Load YOLO model (example, adjust as per your model)
net = cv2.dnn.readNetFromDarknet(r"yolov3tiny.cfg", r"model.weights")
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
classes = ["Pl"]

def detect_plates(frame):
    global name3
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layer_names = net.getLayerNames()
    output_layers_name = net.getUnconnectedOutLayersNames()
    layerOutputs = net.forward(output_layers_name)

    confidences = []
    boxes = []

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.4 and class_id == 0:
                center_x = int(detection[0] * frame.shape[1])
                center_y = int(detection[1] * frame.shape[0])
                w = int(detection[2] * frame.shape[1])
                h = int(detection[3] * frame.shape[0])
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            crp_img = frame[y:y + h, x:x + w]
            cv2.imwrite(os.path.join(path, str(name3) + '.png'), crp_img)
            crp_plat = str(name3) + '.png'
            name3 += 1

            ngt_img = cv2.bitwise_not(crp_img)
            image_path = str(name) + '.png'
            cv2.imwrite(image_path, ngt_img)
            if os.path.exists(image_path):
                name += 1
                return image_path, crp_plat
    return None, None

def preprocess_image(image_path):
    # Load the image
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Dilation and erosion to enhance the text regions
    kernel = np.ones((1, 1), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)

    # Apply median blurring to remove noise
    blurred = cv2.medianBlur(eroded, 3)

    # Resize the image
    resized = cv2.resize(blurred, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

    return resized

while True:
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame1, (1020, 500))
    fgmask = fgbg.apply(frame)
    _, thresh = cv2.threshold(fgmask, 250, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    list = []
    for contour in contours:
        if cv2.contourArea(contour) > 1000:  # Filter based on contour area
            x, y, w, h = cv2.boundingRect(contour)
            list.append([x, y, w, h])
    bbox_idx = tracker.update(list)
    for bbox in bbox_idx:
        x1, y1, w1, h1 = bbox
        cx = int((x1 + x1 + w1) / 2)
        cy = int((y1 + y1 + h1) / 2)
        result = cv2.pointPolygonTest(np.array(area1, np.int32), (cx, cy), False)
        cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1)
        if result >= 0:
            a1[id] = (cx, cy)
        if id in a1:
            result1 = cv2.pointPolygonTest(np.array(area2, np.int32), (cx, cy), False)
            if result1 >= 0:
                cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (0, 0, 255), 2)
                cv2.circle(frame, (cx, cy), 6, (0, 0, 255), -1)

                if counter.count(id) == 0:
                    counter.append(id)
                    print("Kendaraan Melawan Arah")

                    cv2.imwrite(os.path.join(path, str(name2) + '.jpg'), frame)
                    name2 += 1
                    crp_foto = str(name2 - 1) + '.jpg'

                    buzz_on()
                    time.sleep(0.5)
                    buzz_off()

                    crp_img_loc, crp_plat = detect_plates(frame1)
                    if crp_img_loc:
                        preprocessed_img = preprocess_image(crp_img_loc)
                        text = pytesseract.image_to_string(preprocessed_img, config='--psm 6')
                        alphanumeric_text = re.sub(r'[^a-zA-Z0-9]', '', text)
                        first_8_digits = alphanumeric_text[:8]
                        print("Plat:", first_8_digits)

                        query_pengendara = "SELECT namapengendara, notelepon FROM pengendara WHERE platkendaraan = %s"
                        val_pengendara = (first_8_digits,)
                        cursor.execute(query_pengendara, val_pengendara)
                        result_pengendara = cursor.fetchone()

                        waktu_pelanggar = time.strftime('%Y-%m-%d %H:%M:%S')

                        if result_pengendara:
                            namapengendara = result_pengendara[0]
                            notelepon = result_pengendara[1]

                            query_insert_pelanggar = "INSERT INTO pelanggar (platkendaraan, namapengendara, notelepon, waktu, foto) VALUES (%s, %s, %s, %s, %s)"
                            val_pelanggar = (first_8_digits, namapengendara, notelepon, waktu_pelanggar, crp_foto)
                            cursor.execute(query_insert_pelanggar, val_pelanggar)
                            db.commit()
                        else:
                            print("Plat Belum Terdaftar")
                            query_insert_pelanggar = "INSERT INTO belum (waktu, foto, plat) VALUES (%s, %s, %s)"
                            val_pelanggar = (waktu_pelanggar, crp_foto, crp_plat)
                            cursor.execute(query_insert_pelanggar, val_pelanggar)
                            db.commit()
                    else:
                        print("Gagal menyimpan gambar plat nomor")

                        waktu_pelanggar = time.strftime('%Y-%m-%d %H:%M:%S')
                        query_insert_pelanggar = "INSERT INTO belum (waktu, foto, plat) VALUES (%s, %s, '')"
                        val_pelanggar = (waktu_pelanggar, crp_foto)
                        cursor.execute(query_insert_pelanggar, val_pelanggar)
                        db.commit()

    cv2.polylines(frame, [np.array(area1, np.int32)], True, (0, 255, 0), 2)
    cv2.polylines(frame, [np.array(area2, np.int32)], True, (0, 0, 255), 2)
    p = len(counter)
    cv2.imshow('Original', frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

GPIO.cleanup()
cap.release()
cv2.destroyAllWindows()

