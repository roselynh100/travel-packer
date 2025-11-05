import usb.core
import usb.util
import time
import json

# Scale IDs
VENDOR_ID = 0x0922
PRODUCT_ID = 0x8009

def get_weight(wait_time=6.0):
    """Reads weight from DYMO M25 scale and returns average (kg) in JSON format."""
    
    # Find scale 
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        return json.dumps({"error": "Scale not detected"})

    # Configure device for communication 
    try:
        dev.set_configuration()
    except usb.core.USBError:
        pass

    # Select the first USB endpoint for reading data
    endpoint = dev[0][(0, 0)][0]

    print("Place the item on the scale...")
    time.sleep(2)  # Wait before collecting data for stability

    readings = []            # Stores valid stable readings
    start_time = time.time() # Start measurement timer

    # Collect data for the specified duration
    while time.time() - start_time < wait_time:
        try:
            data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout=1000)
            if len(data) >= 6:
                status = data[1]                  # Status byte (bit 2 indicates stability for DYMO)
                grams = data[4] + 256 * data[5]   # Combine bytes 4 and 5 for weight in grams

                # Append only stable readings
                if status & 0x04 == 0x04:
                    readings.append(grams)

        except usb.core.USBError:
            time.sleep(0.1)  # Retry briefly after a read error
            continue

    # Release device resources after reading
    usb.util.dispose_resources(dev)

    # Handle case where no stable readings were obtained
    if len(readings) < 1:
        return json.dumps({"error": "No valid readings"})

    # Average the last 3 stable readings for smoother output
    recent_readings = readings[-3:]
    avg_grams = sum(recent_readings) / len(recent_readings)
    avg_kg = avg_grams / 1000

    # Return final averaged result in kilograms
    return json.dumps({
        "total_weight_kg": round(avg_kg, 3)
    })


if __name__ == "__main__":
    result = get_weight(wait_time=6.0)
    print("Result:", result)
