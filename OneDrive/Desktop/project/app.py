from flask import Flask, render_template, Response, request, jsonify
import sqlite3
import queue
import json
import os
from twilio.rest import Client                  
from model_runner import frame_generator_for_camera, register_alert_callback

app = Flask(__name__)

alert_queue = queue.Queue()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

USER_PHONE = "+918618840410" 
def send_sms_alert(camera, threat, confidence):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)

        msg_body = (
            f"⚠ THREAT DETECTED!\n"
            f"Camera: {camera}\n"
            f"Type: {threat}\n"
            f"Confidence: {confidence}%\n"
            f"Sent from Servalliance AI System."
        )

        message = client.messages.create(
            body=msg_body,
            from_=TWILIO_NUMBER,
            to=USER_PHONE
        )
        print("[SMS SENT] SID:", message.sid)

    except Exception as e:
        print("[SMS ERROR]", e)


# -------------------------
# DATABASE HELPERS
# -------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


def _receive_alert(data):
    print("[ALERT]", data)

    # 1. Send to dashboard popup
    alert_queue.put(data)

    # 2. Send SMS alert
    send_sms_alert(data["camera"], data["threat_type"], data["confidence"])

register_alert_callback(_receive_alert)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/subscription")
def subscription():
    return render_template("subscription.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/live_camera")
def live_camera():
    return render_template("live_camera.html")

# LOGIN API

@app.route("/login_user", methods=["POST"])
def login_user():
    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if row and row[0] == password:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"})

# REGISTER API

@app.route("/register_user", methods=["POST"])
def register_user():
    data = request.json
    username = data["username"]
    password = data["password"]

    try:
        conn = sqlite3.connect("users.db")
        conn.execute("INSERT INTO users (username, password) VALUES (?,?)",
                     (username, password))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except:
        return jsonify({"status": "exists"})


# VIDEO STREAMING

@app.route("/video_feed")
def video_feed():
    cam = request.args.get("camera", "0")
    return Response(
        frame_generator_for_camera(cam),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/alerts")
def alerts():
    def stream():
        while True:
            data = alert_queue.get()
            yield f"data: {json.dumps(data)}\n\n"
    return Response(stream(), mimetype="text/event-stream")

@app.route("/demo_output")
def demo_output():
    return render_template("demo_output.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
