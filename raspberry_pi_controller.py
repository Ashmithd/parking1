import requests

API_URL = "http://127.0.0.1:5000/entry"

print("Raspberry Pi Gate Controller Started")

while True:

    vehicle_number = input("\nScan Vehicle RFID (Enter Vehicle Number): ")

    try:
        response = requests.post(API_URL, json={
            "vehicle_number": vehicle_number
        })

        data = response.json()

        print("Server Response:", data["message"])

        if data["status"] == "ALLOWED":
            print("Gate Opening...")
        else:
            print("Access Denied")

    except Exception as e:
        print("Connection Error:", e)
