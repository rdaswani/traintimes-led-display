#!/usr/bin/env python3
import time
from datetime import datetime

import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# =========================
# CONFIG
# =========================

STATION_CODE = "NTN"
API_URL = f"https://huxley2.azurewebsites.net/departures/{STATION_CODE}/10"

NUM_TRAINS_TO_SHOW = 2
DISPLAY_SECONDS_PER_TRAIN = 5       # How long to show each train (if no scroll)
DEST_MAX_CHARS = 32                 # Safety cap before trimming destination text

# Scrolling behaviour
SCROLL_FRAME_DELAY = 0.05           # Seconds between scroll steps
SCROLL_START_X = 64                 # Start just off the right edge

# Clock position (top-right area)
CLOCK_X = 12
CLOCK_Y = 8

# RGBMatrix options
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = "adafruit-hat"
options.brightness = 60
options.gpio_slowdown = 4

# Font paths (relative to script working directory)
FONT_PATH_MAIN = "fonts/4x6.bdf"   # Train text
FONT_PATH_CLOCK = "fonts/5x8.bdf"  # Clock text


# =========================
# DATA & TEXT HELPERS
# =========================

def fetch_services():
    """Fetch departure board data from Huxley2 API."""
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        services = data.get("trainServices") or []
        return services
    except Exception as exc:
        print("ERROR fetching services:", exc)
        return None


def trim_dest(name: str) -> str:
    """Trim destination name to a safe maximum length."""
    if len(name) <= DEST_MAX_CHARS:
        return name
    return name[: DEST_MAX_CHARS - 1] + "…"


def classify_service(svc):
    """
    Convert a raw service dict into two display lines and a status flag.

    Returns:
        (line1, line2, status)
        status ∈ {"on_time", "delayed", "cancelled", "unknown"}
    """
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
    Measure the pixel width of a text string using the matrix font.
    """
    canvas.Clear()
    end_x = graphics.DrawText(canvas, font, 0, 0, color, text)
    width = end_x
    canvas.Clear()
    return width


# =========================
# DRAWING: CLOCK + TRAINS
# =========================

def draw_clock(offscreen_canvas, clock_font, clock_color):
    """Draw current time in HH:MM:SS at fixed top-right position."""
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    graphics.DrawText(offscreen_canvas, clock_font, CLOCK_X, CLOCK_Y,
                      clock_color, time_str)


def show_train_with_scroll(
    matrix,
    offscreen_canvas,
    font,
    color_top,
    color_bottom,
    line1: str,
    line2: str,
    clock_font,
    clock_color,
):
    """
    Show a single train:
    - If line1 fits within the panel width, show it statically for a few seconds,
      refreshing the clock periodically so seconds tick.
    - If too long, scroll line1 horizontally while keeping the bottom line static.
    """
    width = measure_text_width(offscreen_canvas, font, color_top, line1)
    panel_width = matrix.width

    # Y positions for 32px-high panel
    y1 = 16   # top line baseline
    y2 = 28   # bottom line baseline

    # Static display case
    if width <= panel_width:
        end_time = time.time() + DISPLAY_SECONDS_PER_TRAIN

        while time.time() < end_time:
            offscreen_canvas.Clear()
            graphics.DrawText(offscreen_canvas, font, 1, y1, color_top, line1)
            graphics.DrawText(offscreen_canvas, font, 1, y2, color_bottom, line2)

            draw_clock(offscreen_canvas, clock_font, clock_color)

            offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(0.25)  # refresh clock ~4 times per second

        return offscreen_canvas

    # Scrolling case
    x = SCROLL_START_X
    end_x = -width

    while x > end_x:
        offscreen_canvas.Clear()
        graphics.DrawText(offscreen_canvas, font, x, y1, color_top, line1)
        graphics.DrawText(offscreen_canvas, font, 1, y2, color_bottom, line2)

        draw_clock(offscreen_canvas, clock_font, clock_color)

        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        x -= 1
        time.sleep(SCROLL_FRAME_DELAY)

    time.sleep(0.5)
    return offscreen_canvas


# =========================
# MAIN LOOP
# =========================

def main():
    matrix = RGBMatrix(options=options)

    # Train text font
    font = graphics.Font()
    font.LoadFont(FONT_PATH_MAIN)

    # Clock font
    clock_font = graphics.Font()
    clock_font.LoadFont(FONT_PATH_CLOCK)

    # Colours
    green = graphics.Color(0, 255, 0)
    amber = graphics.Color(255, 165, 0)
    red = graphics.Color(255, 0, 0)
    white = graphics.Color(255, 255, 255)
    clock_color = white

    offscreen_canvas = matrix.CreateFrameCanvas()

    try:
        while True:
            services = fetch_services()

            if services is None:
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, font, 1, 16, red, "API ERROR")
                graphics.DrawText(offscreen_canvas, font, 1, 28, red, "Check network")
                draw_clock(offscreen_canvas, clock_font, clock_color)
                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                time.sleep(5)
                continue

            if not services:
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, font, 1, 16, amber, "NO DATA")
                graphics.DrawText(offscreen_canvas, font, 1, 28, amber, "No trains")
                draw_clock(offscreen_canvas, clock_font, clock_color)
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
                    line2,
                    clock_font,
                    clock_color,
                )

    except KeyboardInterrupt:
        matrix.Clear()


if __name__ == "__main__":
    main()
