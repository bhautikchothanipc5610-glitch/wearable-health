import requests
import time
import random
from datetime import datetime

  #URL = "http://127.0.0.1:5000/api/data"      #for localhoast

URL = "https://wearable-health.onrender.com/api/data"

def simulate():
    while True:
        heart_rate = random.randint(60, 120)
        temperature = round(random.uniform(36.5, 38.5), 1)
        hrv = round(random.uniform(25, 80), 1)  # Heart Rate Variability

        accel_x = round(random.uniform(-0.2, 0.2), 2)
        accel_y = round(random.uniform(-0.2, 0.2), 2)
        accel_z = round(random.uniform(0.8, 1.2), 2)

        if random.random() < 0.05:
            accel_x = round(random.uniform(-3.0, 3.0), 2)
            accel_y = round(random.uniform(-3.0, 3.0), 2)
            accel_z = round(random.uniform(-3.0, 3.0), 2)
            print("💥 Simulated Fall Event!")

        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "heart_rate": heart_rate,
            "temperature": temperature,
            "accel_x": accel_x,
            "accel_y": accel_y,
            "accel_z": accel_z,
            "hrv": hrv
        }

        try:
            requests.post(URL, json=data)
            print("Sent:", data)
        except Exception as e:
            print("Error:", e)

        time.sleep(2)

if __name__ == "__main__":
    simulate()
