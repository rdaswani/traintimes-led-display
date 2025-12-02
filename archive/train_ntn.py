#!/usr/bin/env python3
import time
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

STATION = "NTN"
HUXLEY_URL = f"https://huxley2.azurewebsites.net/departures/{STATION}/10"

def fetch_data():
    try:
        r = requests.get(HUXLEY_URL, timeout=5)
        data = r.json()
        services = data.get("trainServices", [])
        # DEBUG: print first few services
        for svc in services[:5]:
            dest = svc["destination"][0]["locationName"] if svc.get("destination") else "Unknown"
            print("DEBUG:", svc.get("std"), dest, "ETD:", svc.get("etd"))
        return services
    except Exception as e:
        print("ERROR:", e)
        return []

def format_dep(svc):
    time_str = svc.get("std", "--:--")
    dest_name = svc["destination"][0]["locationName"] if svc.get("destination") else "Unknown"
    plat = svc.get("platform", "?")
    etd = svc.get("etd", "")

    status = ""
    if etd not in ("On time", "On Time", "OnTime", ""):
        status = etd

    return f"{time_str} {dest_name[:10]} P{plat} {status}".strip()

def create_matrix():
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.hardware_mapping = "adafruit-hat"
    options.gpio_slowdown = 2
    return RGBMatrix(options=options)

def main():
    matrix = create_matrix()
    canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    font.LoadFont("6x9.bdf")

    while True:
        services = fetch_data()[:3]
        if not services:
            messages = ["NO DATA"]
        else:
            messages = [format_dep(s) for s in services]

        for msg in messages:
            pos = canvas.width
            msg_len = len(msg) * 6
            while pos > -msg_len:
                canvas.Clear()
                graphics.DrawText(canvas, font, pos, 18, graphics.Color(255,255,0), msg)
                canvas = matrix.SwapOnVSync(canvas)
                pos -= 1
                time.sleep(0.03)

        time.sleep(2)

if __name__ == "__main__":
    main()
