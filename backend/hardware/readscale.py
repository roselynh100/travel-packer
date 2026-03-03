import json
import time

import serial


def get_weight(port="/dev/cu.usbserial-0001", baudrate=115200):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
    except:
        return json.dumps({"error": "Serial open failed"})

    print("Place the item on the scale. Measuring in 5, 4, 3, 2, 1...")
    time.sleep(5)

    readings = []
    start = time.time()

    while time.time() - start < 15:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        try:
            w = float(line)
        except:
            continue

        if w >= 0.10:  # start getting readings when weight is greater than 0.1kg
            readings.append(w)
            if len(readings) > 5:
                readings.pop(0)
            if len(readings) == 5 and all(
                abs(readings[i] - readings[i - 1]) <= 0.03 for i in range(1, 5)
            ):  # threshold for stability is 30grams
                avg = sum(readings) / 5
                return json.dumps({"total_weight_kg": round(avg, 3)})
        else:
            readings = []

    return json.dumps({"error": "Timeout or unstable readings"})


if __name__ == "__main__":
    print(get_weight())
