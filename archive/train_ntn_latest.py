#!/usr/bin/env python3
import time
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# =========================
# CONFIG
# =========================

STATION_CODE = "EUS"
API_URL = f"https://huxley2.azurewebsites.net/departures/{STATION_CODE}/10"

NUM_TRAINS_TO_SHOW = 2
DISPLAY_SECONDS_PER_TRAIN = 5
DEST_MAX_CHARS = 12

# --- COPY THESE FROM YOUR WORKING "hello" SCRIPT IF DIFFERENT ---
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = "adafruit-hat" # change if your hello script uses something else
options.brightness = 60 # tweak if needed
options.gpio_slowdown = 2
# options.gpio_slowdown = 4 # uncomment if your hello script sets this
try:
	options.hardware_pulsing = False
except AttributeError:
	options.disable_hardware_pulsing = True


FONT_PATH = "5x8.bdf"


# =========================
# HELPERS
# =========================

def fetch_services():
    try:
        r = requests.get(API_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
        services = data.get("trainServices") or []

        for svc in services:
            std = svc.get("std")
            etd = svc.get("etd")
            dest = svc.get("destination", [{}])[0].get("locationName", "Unknown")
            print(f"DEBUG: {std} {dest} ETD={etd}")
        return services
    except Exception as e:
        print("ERROR fetching services:", e)
        return None


def trim_dest(name: str) -> str:
    if len(name) <= DEST_MAX_CHARS:
        return name
    return name[: DEST_MAX_CHARS - 1] + "…"


def classify_service(svc):
    std = svc.get("std", "??:??")
    etd = svc.get("etd", "")
    dest = trim_dest(svc.get("destination", [{}])[0].get("locationName", "Unknown"))
    plat = svc.get("platform") or "?"

    cancelled = svc.get("isCancelled", False)

    if cancelled:
        top = f"{std} {dest}"
        bottom = f"P{plat} CANCELLED"
        status = "cancelled"
    elif not etd:
        top = f"{std} {dest}"
        bottom = f"P{plat} Check ETD"
        status = "unknown"
    elif etd == "On time" or etd == std:
        top = f"{std} {dest}"
        bottom = f"P{plat} On time"
        status = "on_time"
    else:
        top = f"{std}->{etd} {dest}"
        bottom = f"P{plat} Delayed"
        status = "delayed"

    return top, bottom, status


# =========================
# MAIN
# =========================

def main():
    matrix = RGBMatrix(options=options)

    font = graphics.Font()
    font.LoadFont(FONT_PATH)

    green = graphics.Color(0, 255, 0)
    amber = graphics.Color(255, 165, 0)
    red = graphics.Color(255, 0, 0)
    white = graphics.Color(255, 255, 255)
    blue = graphics.Color(0,0,255)

    try:
        while True:
            services = fetch_services()

            if services is None:
                matrix.Clear()
                graphics.DrawText(matrix, font, 1, 14, red, "API ERROR")
                graphics.DrawText(matrix, font, 1, 28, red, "Check network")
                time.sleep(5)
                continue

            if not services:
                matrix.Clear()
                graphics.DrawText(matrix, font, 1, 14, amber, "NO DATA")
                graphics.DrawText(matrix, font, 1, 28, amber, "No trains")
                time.sleep(10)
                continue

            for svc in services[:NUM_TRAINS_TO_SHOW]:
                line1, line2, status = classify_service(svc)

                if status == "on_time":
                    col = blue
                elif status == "delayed":
                    col = amber
                elif status == "cancelled":
                    col = red
                else:
                    col = white

                matrix.Clear()
                # Baselines chosen to roughly match your good "hello" demo:
                graphics.DrawText(matrix, font, 1, 14, col, line1)
                graphics.DrawText(matrix, font, 1, 28, col, line2)
                time.sleep(DISPLAY_SECONDS_PER_TRAIN)

    except KeyboardInterrupt:
        matrix.Clear()


if __name__ == "__main__":
    main()
