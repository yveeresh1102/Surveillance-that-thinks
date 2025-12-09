# model_runner.py
import os
import time
import threading
import collections
import cv2
from ultralytics import YOLO

# CONFIG
MODEL_PATH = "best.pt"           # path to your weights file
CONF_THRESHOLD = 0.45            # detection confidence threshold (0.0 - 1.0)
SAVE_FRAMES = 100                # number of frames to keep in rolling buffer (~10s at 10fps)
CLIP_FPS = 10                    # fps to save threat clips
CLIPS_DIR = "clips"              # directory to save clips

# Ensure clips dir exists
os.makedirs(CLIPS_DIR, exist_ok=True)

# Load model once (raises clear error if file missing/corrupt)
print("[model_runner] Loading YOLO model from:", MODEL_PATH)
try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    # re-raise with friendly message
    raise RuntimeError(f"Failed to load model '{MODEL_PATH}': {e}")

# mapping of camera_id -> buffer & capture resources
_camera_buffers = {}
_camera_caps = {}
_camera_locks = {}   # small lock per camera to protect resources

# callback set by app.py
alert_callback = None
def register_alert_callback(cb):
    global alert_callback
    alert_callback = cb

def _save_clip_file(camera_id, frames):
    """Save frames list as an mp4 clip and return filepath."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_cam = str(camera_id).replace("/", "_").replace(":", "_")
    filename = f"threat_cam{safe_cam}_{timestamp}.mp4"
    out_path = os.path.join(CLIPS_DIR, filename)

    if not frames:
        return None

    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, CLIP_FPS, (w, h))

    for f in frames:
        # ensure BGR and correct shape
        writer.write(f)

    writer.release()
    return out_path

def _trigger_alert(camera_id, cls_name, confidence, clip_path):
    """Form alert dict and call the registered callback (if any)."""
    data = {
        "camera": str(camera_id),
        "threat_type": cls_name,
        "confidence": round(confidence * 100, 2),
        "clip": clip_path
    }
    print("[model_runner] ALERT:", data)
    try:
        if alert_callback:
            alert_callback(data)
    except Exception as e:
        print("[model_runner] Error calling alert_callback:", e)

def _process_detections_and_maybe_alert(camera_id, results, frames_buffer):
    """
    results: ultralytics results for a single frame (results[0])
    frames_buffer: list of recent frames (copies)
    """
    try:
        r = results[0]  # single image result
    except Exception:
        return

    # boxes available in r.boxes; iterate and check confidences
    boxes = getattr(r, "boxes", None)
    if boxes is None:
        return

    for box in boxes:
        try:
            conf = float(box.conf.cpu().numpy()) if hasattr(box.conf, "cpu") else float(box.conf)
        except Exception:
            try:
                conf = float(box.conf)
            except Exception:
                conf = 0.0
        try:
            cls_idx = int(box.cls.cpu().numpy()) if hasattr(box.cls, "cpu") else int(box.cls)
        except Exception:
            cls_idx = int(box.cls)

        if conf >= CONF_THRESHOLD:
            # get class name safely
            cls_name = model.names.get(cls_idx, str(cls_idx)) if hasattr(model, "names") else str(cls_idx)

            # Save clip in background thread (copy buffer)
            saved_frames = list(frames_buffer)  # copy
            def bg_save_and_alert():
                clip_path = _save_clip_file(camera_id, saved_frames)
                _trigger_alert(camera_id, cls_name, conf, clip_path)
            threading.Thread(target=bg_save_and_alert, daemon=True).start()

def _draw_results_on_frame(results, frame):
    """Draw boxes and labels onto the frame (inplace)."""
    try:
        r = results[0]
    except Exception:
        return frame

    boxes = getattr(r, "boxes", None)
    if boxes is None:
        return frame

    for box in boxes:
        try:
            xyxy = box.xyxy.cpu().numpy()[0] if hasattr(box.xyxy, "cpu") else box.xyxy[0]
            x1, y1, x2, y2 = map(int, xyxy[:4])
        except Exception:
            continue

        try:
            conf = float(box.conf.cpu().numpy()) if hasattr(box.conf, "cpu") else float(box.conf)
        except Exception:
            conf = float(box.conf)

        try:
            cls_idx = int(box.cls.cpu().numpy()) if hasattr(box.cls, "cpu") else int(box.cls)
        except Exception:
            cls_idx = int(box.cls)

        cls_name = model.names.get(cls_idx, str(cls_idx)) if hasattr(model, "names") else str(cls_idx)
        label = f"{cls_name} {conf:.2f}"

        # Draw rectangle and label
        color = (0, 165, 255)  # orange-ish
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        # label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, label, (x1 + 3, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (0, 0, 0), 1, cv2.LINE_AA)

    return frame

def frame_generator_for_camera(camera_id):
    """
    Generator used by Flask video_feed to stream MJPEG.
    camera_id can be:
      - integer string: "0", "1" -> local webcams
      - RTSP/HTTP string: "rtsp://..." or encoded URL passed by client
    """
    cam_key = str(camera_id)

    # create capture if not exists (thread-safe)
    if cam_key not in _camera_caps:
        _camera_locks.setdefault(cam_key, threading.Lock())
        with _camera_locks[cam_key]:
            if cam_key not in _camera_caps:
                # if camera_id looks numeric -> open camera device; else try URL
                try:
                    if cam_key.isdigit():
                        cap = cv2.VideoCapture(int(cam_key))
                    else:
                        cap = cv2.VideoCapture(cam_key)
                except Exception:
                    cap = cv2.VideoCapture(cam_key)
                _camera_caps[cam_key] = cap
                _camera_buffers[cam_key] = collections.deque(maxlen=SAVE_FRAMES)

    cap = _camera_caps[cam_key]
    frames_buffer = _camera_buffers[cam_key]

    # basic loop
    while True:
        if cap is None:
            break
        success, frame = cap.read()
        if not success:
            # yield a small wait and continue (camera disconnected)
            time.sleep(0.1)
            continue

        # store copy of raw frame to buffer (for clips)
        frames_buffer.append(frame.copy())

        # Run model — do this try/except so a single failure doesn't break streaming
        try:
            # ultralytics accepts BGR numpy images directly
            results = model(frame)     # returns a Results object (list-like)
        except Exception as e:
            # If model fails (OOM / corrupted weights), print and continue sending raw frames
            print("[model_runner] model inference error:", e)
            results = []

        # draw detections
        try:
            annotated = _draw_results_on_frame(results, frame)
        except Exception as e:
            annotated = frame

        # If any detection passes threshold, we trigger alert (we pass results & buffer)
        try:
            # this inspects detections and will trigger bg save+alert
            _process_detections_and_maybe_alert(cam_key, results, frames_buffer)
        except Exception as e:
            print("[model_runner] error while processing detections:", e)

        # encode and yield frame as jpeg
        try:
            ret, buffer = cv2.imencode(".jpg", annotated)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        except Exception as e:
            print("[model_runner] encoding error:", e)
            time.sleep(0.01)
            continue
