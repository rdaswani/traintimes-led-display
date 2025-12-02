#!/usr/bin/env python3
import time
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# =========================
# CONFIG
# =========================

STATION_CODE = "NTN"
API_URL = f"https://huxley2.azurewebsites.net/departures/{STATION_CODE}/10"

NUM_TRAINS_TO_SHOW = 2
DISPLAY_SECONDS_PER_TRAIN = 5       # used for non-scrolling cases
DEST_MAX_CHARS = 32                 # just a safety cap, scrolling will handle long ones

# Scrolling behaviour
SCROLL_FRAME_DELAY = 0.05           # seconds between scroll steps (~20 FPS)
SCROLL_START_X = 64                 # start just off the right edge

# --- COPY THESE FROM YOUR WORKING SCRIPT IF DIFFERENT ---
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = "adafruit-hat"  # this is what worked for you
options.brightness = 60
options.gpio_slowdown = 4                  # helped stabilise timing on your Pi

FONT_PATH = "5x8.bdf"  # smaller font


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
            print(f"DEBUG: STD={std} ETD={etd} DEST={dest}")
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


def measure_text_width(canvas, font, color, text: str) -> int:
    """
    Use DrawText's return value to measure width in pixels.
    We draw at (0,0) on a cleared canvas then clear again.
    """
    canvas.Clear()
    end_x = graphics.DrawText(canvas, font, 0, 0, color, text)
    width = end_x  # start x was 0
    canvas.Clear()
    return width


def show_train_with_scroll(matrix, offscreen_canvas, font,
                           color_top, color_bottom,
                           line1: str, line2: str):
    """
    Show one train. If line1 is wider than the matrix, scroll it.
    Returns the (possibly updated) offscreen_canvas.
    """
    width = measure_text_width(offscreen_canvas, font, color_top, line1)
    panel_width = matrix.width

    # Y positions chosen for 6x10 font on 32px panel
    y1 = 11   # top line baseline
    y2 = 24   # bottom line baseline

    # 1) If it fits, just show static for DISPLAY_SECONDS_PER_TRAIN
    if width <= panel_width:
        offscreen_canvas.Clear()
        graphics.DrawText(offscreen_canvas, font, 1, y1, color_top, line1)
        graphics.DrawText(offscreen_canvas, font, 1, y2, color_bottom, line2)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(DISPLAY_SECONDS_PER_TRAIN)
        return offscreen_canvas

    # 2) Too long → scroll horizontally
    # Start off-screen right, scroll left until text fully off left edge.
    x = SCROLL_START_X
    end_x = -width

    while x > end_x:
        offscreen_canvas.Clear()
        graphics.DrawText(offscreen_canvas, font, x, y1, color_top, line1)
        graphics.DrawText(offscreen_canvas, font, 1, y2, color_bottom, line2)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        x -= 1
        time.sleep(SCROLL_FRAME_DELAY)

    # Small pause at the end so it doesn't instantly jump to next train
    time.sleep(0.5)
    return offscreen_canvas


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

    offscreen_canvas = matrix.CreateFrameCanvas()

    try:
        while True:
            services = fetch_services()

            if services is None:
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, font, 1, 11, red,   "API ERROR")
                graphics.DrawText(offscreen_canvas, font, 1, 24, red,   "Check network")
                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                time.sleep(5)
                continue

            if not services:
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, font, 1, 11, amber, "NO DATA")
                graphics.DrawText(offscreen_canvas, font, 1, 24, amber, "No trains")
                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                time.sleep(10)
                continue

            for svc in services[:NUM_TRAINS_TO_SHOW]:
                line1, line2, status = classify_service(svc)

                if status == "on_time":
                    col = green
                elif status == "delayed":
                    col = amber
                elif status == "cancelled":
                    col = red
                else:
                    col = white

                offscreen_canvas = show_train_with_scroll(
                    matrix,
                    offscreen_canvas,
                    font,
                    col,
                    col,
                    line1,
                    line2
                )

    except KeyboardInterrupt:
        matrix.Clear()


if __name__ == "__main__":
    main()
