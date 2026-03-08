#!/usr/bin/env python3
# coding: utf-8

import cv2
import time
import logging
import numpy as np
from ultralytics import YOLO
import threading
import queue
import torch
import math

# =====================
# CONFIG
# =====================

FOCAL_LENGTH_PX = 140.0
REAL_HUMAN_HEIGHT_M = 1.7
CONFIDENCE_THRESHOLD = 0.6

INFERENCE_SIZE = 416
DETECTION_EVERY_N_FRAMES = 3
ENABLE_CLAHE = False

CAMERA_HFOV_DEG = 60.0

# ---- STATIC DRONE DATA (PI TEST MODE) ----
STATIC_CAMERA_HEADING_DEG = 90.0
DRONE_LAT = 12.971599
DRONE_LON = 77.594566
DRONE_ALT = 10.0

LAT_OFFSET_DEG = 0.0
LON_OFFSET_DEG = 0.0
DIST_SCALE = 1.0

# =====================
# LOGGER
# =====================

def setup_logger():
    logger = logging.getLogger("PiHumanDetectionGPS")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(ch)
    return logger

logger = setup_logger()

# =====================
# VIDEO CAPTURE THREAD
# =====================

def video_capture_thread(cap, frame_queue, stop_event):
    while not stop_event.is_set():
        ret, frame = cap.read()
        if ret and frame_queue.qsize() < 2:
            frame_queue.put(frame)

# =====================
# DISTANCE ESTIMATION
# =====================

def estimate_distance(box_height_px):
    if box_height_px <= 0:
        return float('inf')
    d = (REAL_HUMAN_HEIGHT_M * FOCAL_LENGTH_PX) / box_height_px
    return d * DIST_SCALE

# =====================
# PREPROCESS
# =====================

def preprocess_frame(frame, size):
    frame = cv2.resize(frame, (size, size))
    if not ENABLE_CLAHE:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(3.0, (8, 8))
    cl = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

# =====================
# GEO HELPERS
# =====================

EARTH_RADIUS_M = 6378137.0

def pixel_to_bearing(center_x, frame_width, base_heading):
    norm = (center_x - frame_width / 2) / (frame_width / 2)
    offset = norm * (CAMERA_HFOV_DEG / 2)
    return (base_heading + offset) % 360

def project_gps(lat, lon, dist, bearing):
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brng = math.radians(bearing)

    d = dist / EARTH_RADIUS_M
    lat2 = math.asin(
        math.sin(lat1) * math.cos(d) +
        math.cos(lat1) * math.sin(d) * math.cos(brng)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2)
    )

    return math.degrees(lat2), math.degrees(lon2)

# =====================
# MAIN
# =====================

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    model = YOLO("yolov8n.pt")
    model.to(device)
    model.fuse()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_queue = queue.Queue(maxsize=3)
    stop_event = threading.Event()

    threading.Thread(
        target=video_capture_thread,
        args=(cap, frame_queue, stop_event),
        daemon=True
    ).start()

    last_results = None
    frame_index = 0

    logger.info("Press Q to exit")

    while True:
        if frame_queue.empty():
            time.sleep(0.002)
            continue

        frame = frame_queue.get()
        h, w = frame.shape[:2]

        human_detected = False  # 👈 STATUS FLAG

        run = frame_index % DETECTION_EVERY_N_FRAMES == 0

        if run:
            img = preprocess_frame(frame, INFERENCE_SIZE)
            with torch.no_grad():
                last_results = model(
                    img,
                    imgsz=INFERENCE_SIZE,
                    conf=CONFIDENCE_THRESHOLD,
                    verbose=False
                )[0]

        if last_results and last_results.boxes is not None:
            sx = w / INFERENCE_SIZE
            sy = h / INFERENCE_SIZE

            for box, conf, cls in zip(
                last_results.boxes.xyxy.cpu().numpy(),
                last_results.boxes.conf.cpu().numpy(),
                last_results.boxes.cls.cpu().numpy()
            ):
                if int(cls) != 0:
                    continue

                human_detected = True  # ✅ HUMAN FOUND

                x1, y1, x2, y2 = map(int, [box[0]*sx, box[1]*sy, box[2]*sx, box[3]*sy])
                bh = max(1, y2 - y1)
                dist = estimate_distance(bh)

                cx = (x1 + x2) // 2
                bearing = pixel_to_bearing(cx, w, STATIC_CAMERA_HEADING_DEG)
                lat, lon = project_gps(DRONE_LAT, DRONE_LON, dist, bearing)

                lat += LAT_OFFSET_DEG
                lon += LON_OFFSET_DEG

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
                cv2.circle(frame, (cx, (y1+y2)//2), 4, (0,0,255), -1)

                cv2.putText(
                    frame,
                    f"{dist:.2f}m | {lat:.6f},{lon:.6f}",
                    (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0,255,0),
                    2
                )

        # =====================
        # HUMAN STATUS DISPLAY
        # =====================

        if human_detected:
            cv2.putText(
                frame,
                "HUMAN DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                3
            )
        else:
            cv2.putText(
                frame,
                "NO HUMAN",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                3
            )

        cv2.imshow("Raspberry Pi Human Detection", frame)
        frame_index += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    stop_event.set()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()