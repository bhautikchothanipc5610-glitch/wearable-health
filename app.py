from flask import Flask, jsonify, request, render_template, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import math, time, requests

# -----------------------------
# Fast2SMS Configuration
# -----------------------------
FAST2SMS_API_KEY = "YOUR_FAST2SMS_API_KEY"  # 🔑 Replace with your real key
TO_PHONE = "91XXXXXXXXXX"  # 🔢 Replace with your 10-digit number (no +)

# Rate-limit to avoid SMS flooding
last_sms_time = 0

def send_sms_alert(message):
    """Send SMS alert through Fast2SMS with cooldown."""
    global last_sms_time
    if time.time() - last_sms_time < 30:  # 30s cooldown
        print("⏳ SMS skipped (cooldown active)")
        return
    last_sms_time = time.time()

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "v3",
        "sender_id": "TXTIND",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": TO_PHONE
    }
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📱 SMS sent → {response.text}")
    except Exception as e:
        print(f"❌ SMS Send Error: {e}")

# -----------------------------
# Flask + Database Setup
# -----------------------------
app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -----------------------------
# Sensor Data Model
# -----------------------------
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(50))
    heart_rate = db.Column(db.Float)
    temperature = db.Column(db.Float)
    accel_x = db.Column(db.Float)
    accel_y = db.Column(db.Float)
    accel_z = db.Column(db.Float)
    hrv = db.Column(db.Float)
    alert = db.Column(db.String(50))
    stress_score = db.Column(db.Float)

with app.app_context():
    db.create_all()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    """Render dashboard UI."""
    return render_template("dashboard.html")

@app.route("/api/data", methods=["POST"])
def add_data():
    """Receive sensor data and calculate metrics + alerts."""
    data = request.get_json()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ax = data.get("accel_x", 0)
    ay = data.get("accel_y", 0)
    az = data.get("accel_z", 1)
    hrv = data.get("hrv", 50)
    heart_rate = data.get("heart_rate", 0)
    temperature = data.get("temperature", 0)

    total_accel = math.sqrt(ax**2 + ay**2 + az**2)
    alert = ""

    # --- Event Detection ---
    if total_accel < 0.3:
        alert = "Possible Fall (Freefall)"
        send_sms_alert(f"⚠️ {alert} detected at {timestamp}")
    elif total_accel > 3.0:
        alert = "Fall Detected (Impact)"
        send_sms_alert(f"⚠️ {alert} detected at {timestamp}")
    elif heart_rate > 110:
        alert = "High Heart Rate"
        send_sms_alert(f"⚠️ {alert} at {timestamp}")
    elif temperature > 38.0:
        alert = "Fever"
        send_sms_alert(f"⚠️ {alert} at {timestamp}")
    elif hrv < 35:
        alert = "High Stress"
        send_sms_alert(f"⚠️ {alert} at {timestamp}")

    # --- Stress Prediction ---
    stress_score = (
        (0.6 * heart_rate)
        - (0.4 * hrv)
        + (0.3 * (temperature - 36.5) * 10)
    )
    stress_score = max(0, min(stress_score, 50))  # clamp between 0–50

    if stress_score > 25:
        alert = "Predicted High Stress"
        send_sms_alert(f"⚠️ {alert} at {timestamp}")

    # Log for debugging
    print(f"[{timestamp}] HR={heart_rate} | Temp={temperature} | HRV={hrv} | Stress={stress_score:.2f} | Alert={alert}")

    # --- Save to DB ---
    record = SensorData(
        timestamp=timestamp,
        heart_rate=heart_rate,
        temperature=temperature,
        accel_x=ax,
        accel_y=ay,
        accel_z=az,
        hrv=hrv,
        stress_score=stress_score,
        alert=alert
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"message": "Data received"}), 200

@app.route("/api/data", methods=["GET"])
def get_data():
    """Return recent 20 sensor records."""
    records = SensorData.query.order_by(SensorData.id.desc()).limit(20).all()
    return jsonify([
        {
            "timestamp": r.timestamp,
            "heart_rate": r.heart_rate,
            "temperature": r.temperature,
            "accel_x": r.accel_x,
            "accel_y": r.accel_y,
            "accel_z": r.accel_z,
            "hrv": r.hrv,
            "stress_score": r.stress_score,
            "alert": r.alert
        } for r in records
    ])

@app.route("/export")
def export_data():
    """Export all data as CSV with seconds included."""
    records = SensorData.query.order_by(SensorData.id.asc()).all()

    def generate():
        yield "Timestamp (with seconds),Heart Rate,Temperature,Accel X,Accel Y,Accel Z,HRV,Stress Score,Alert\n"
        for r in records:
            yield f"{r.timestamp},{r.heart_rate},{r.temperature},{r.accel_x},{r.accel_y},{r.accel_z},{r.hrv},{r.stress_score},{r.alert}\n"

    filename = f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
