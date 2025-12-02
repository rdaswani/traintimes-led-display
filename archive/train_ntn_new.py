#!/usr/bin/env python3
import time
import requests
from datetime import datetime

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# =========================
# CONFIG
# =========================

STATION_CODE = "NTN"             # Newton (Lanark)
STATION_NAME = "Newton (Lanark)" # For future header use if you want

API_URL = f"https://huxley2.azurewebsites.net/departures/{STATION_CODE}/10"

NUM_TRAINS_TO_SHOW = 2           # Only show the next 2 trains
DISPLAY_SECONDS_PER_TRAIN = 5    # How long to keep each train on screen
REFRESH_AFTER_CYCLE = True       # Fetch fresh data after showing the 2 trains

DEST_MAX_CHARS = 12              # Trim long destinations to fit panel

# LED Matrix options (tune if needed)
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = "adafruit-hat"  # or "regular" / "adafruit-hat-pwm" etc.

# Font path – update this if your fonts live somewhere else
FONT_PATH = "7x13.bdf"


# =========================
# DATA FETCHING
# =========================

def fetch_services():
    """
    Fetch services from Huxley2 for the given station.
    Returns a list of train service dicts (may be empty).
    """
    try:
        resp = requests.get(API_URL, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        services = data.get("trainServices") or []

        # Debug print
        for svc in services:
            std = svc.get("std")
            etd = svc.get("etd")
            dest = svc.get("destination", [{}])[0].get("locationName", "Unknown")
            print(f"DEBUG: {std} {dest} ETD: {etd}")

        return services

    except Exception as e:
        print(f"ERROR fetching data: {e}")
        return None


# =========================
# TEXT / STATUS HELPERS
# =========================

def trim_destination(name: str) -> str:
    """Trim destination name to fit on the panel."""
    if len(name) <= DEST_MAX_CHARS:
        return name
    return name[: DEST_MAX_CHARS - 1] + "…"


def classify_service(service):
    """
    Decide how to display the service:
    - On time
    - Delayed (STD -> ETD)
    - Cancelled
    Returns:
      top_line (str),
      bottom_line (str),
      status ("on_time" | "delayed" | "cancelled" | "unknown")
    """
    std = service.get("std", "??:??")
    etd = service.get("etd", "")
    dest = service.get("destination", [{}])[0].get("locationName", "Unknown")
    dest = trim_destination(dest)
    plat = service.get("platform") or "?"

    is_cancelled = service.get("isCancelled", False)

    # Cancelled takes priority
    if is_cancelled:
        top = f"{std} {dest}"
        bottom = f"P{plat} CANCELLED"
        status = "cancelled"

    # Unknown ETD (fallback)
    elif not etd:
        top = f"{std} {dest}"
        bottom = f"P{plat} Check ETD"
        status = "unknown"

    # On time (Huxley/Darwin style)
    elif etd == "On time" or etd == std:
        top = f"{std} {dest}"
        bottom = f"P{plat} On time"
        status = "on_time"

    # Delayed – ETD is a different time
    else:
        # show STD→ETD on top line to make delay obvious
        top = f"{std}->{etd} {dest}"
        bottom = f"P{plat} Delayed"
        status = "delayed"

    return top, bottom, status


# =========================
# DRAWING HELPERS
# =========================

def clear_matrix(matrix):
    matrix.Clear()


def draw_centered_two_line_text(matrix, font, color_top, color_bottom, line1: str, line2: str):
    """
    Draw two lines of text roughly centered vertically.
    We'll just left-align at x=0 for simplicity and keep it readable.
    """
    offscreen = matrix.CreateFrameCanvas()
    offscreen.Clear()

    # y coordinates (baseline) for 32px height panel using 7x13 font:
    y1 = 12
    y2 = 26

    graphics.DrawText(offscreen, font, 1, y1, color_top, line1)
    graphics.DrawText(offscreen, font, 1, y2, color_bottom, line2)

    matrix.SwapOnVSync(offscreen)


# =========================
# MAIN LOOP
# =========================

def main():
    matrix = RGBMatrix(options=options)

    # Load font
    font = graphics.Font()
    font.LoadFont(FONT_PATH)

    # Colors
    green = graphics.Color(0, 255, 0)
    amber = graphics.Color(255, 165, 0)
    red = graphics.Color(255, 0, 0)
    white = graphics.Color(255, 255, 255)

    try:
        while True:
            services = fetch_services()

            if services is None:
                # API error – show error message
                clear_matrix(matrix)
                draw_centered_two_line_text(
                    matrix,
                    font,
                    red,
                    red,
                    "API ERROR",
                    "Check network"
                )
                time.sleep(5)
                continue

            if not services:
                # No trains – show fallback
                clear_matrix(matrix)
                draw_centered_two_line_text(
                    matrix,
                    font,
                    amber,
                    amber,
                    "NO DATA",
                    "No trains found"
                )
                time.sleep(10)
                continue

            # Only consider the first N services
            services_to_show = services[:NUM_TRAINS_TO_SHOW]

            for svc in services_to_show:
                line1, line2, status = classify_service(svc)

                # Choose colors by status
                if status == "on_time":
                    c_top = green
                    c_bottom = green
                elif status == "delayed":
                    c_top = amber
                    c_bottom = amber
                elif status == "cancelled":
                    c_top = red
                    c_bottom = red
                else:
                    c_top = white
                    c_bottom = white

                draw_centered_two_line_text(matrix, font, c_top, c_bottom, line1, line2)
                time.sleep(DISPLAY_SECONDS_PER_TRAIN)

            # After showing the 2 trains, either refresh or loop again
            if REFRESH_AFTER_CYCLE:
                continue

    except KeyboardInterrupt:
        print("Exiting…")
        clear_matrix(matrix)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
