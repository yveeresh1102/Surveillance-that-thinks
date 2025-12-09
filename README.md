**SURVEILLANCE THAT THINKS – AI-Powered CCTV Monitoring System**

An advanced **AI-based real-time CCTV surveillance system** that detects threats, streams live camera feeds, saves event clips, and sends instant alerts.
Built using **Flask, OpenCV, Deep Learning, and Twilio SMS alerts**.


## **Features**
###  **Real-Time Threat Detection**
* Detects suspicious activity using deep learning
* Works on webcam, external USB camera, or RTSP/IP cameras
* Frame-by-frame model inference

### **Live Streaming Dashboard**
* View multiple camera feeds
* Dedicated pages for each camera
* IP camera support

###  **Instant Alerts**
* Saves threat clips automatically
* Pushes alerts to UI using SSE (Server-Sent Events)
* Twilio SMS alert integration (optional)

###  **User Authentication**
* Login & Register using SQLite
* Subscription page with access control
* Secure session control

###  **Demo Video Included**
* System includes demo threat-detection footage for testing

###  **Admin Dashboard**
* View alerts
* Access cameras
* Monitor threats live

##  **Project Structure**

project/
│── app.py                 # Main Flask app
│── model_runner.py        # Model + video processing logic
│── templates/             # All HTML pages
│── static/                # JS, CSS, images, demo videos
│── clips/                 # Auto-saved threat clips
│── users.db               # SQLite authentication DB
│── requirements.txt       # Python dependencies
│── README.md              # Project documentation

##  **Installation**
### 1️⃣ Clone the repository

```bash
git clone https://github.com/yveeresh1102/Surveillance-that-thinks.git
cd Surveillance-that-thinks


### Install dependencies

```bash
pip install -r requirements.txt


###  Run the Application

```bash
python app.py

Server runs at:
 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**



##  **Add Your Camera**

### Webcam (Default)
/live_camera?camera=0

### USB Camera
/live_camera?camera=1

### RTSP/IP Camera

Enter URL:

rtsp://username:password@IP:port/stream


##  **(Optional) Enable Twilio SMS Alerts**

Add this in `model_runner.py`:

```python
TWILIO_SID = "your_sid"
TWILIO_TOKEN = "your_token"
FROM_NUMBER = "+1xxxxxxxxxx"
TO_NUMBER = "+91xxxxxxxxxx"


##  **Future Enhancements**

* Weapon detection expansion
* Face recognition for access control
* Cloud storage for clips
* Advanced subscription plans


## **Developers**

**Y. Veeresh**
B.Tech CSE 

