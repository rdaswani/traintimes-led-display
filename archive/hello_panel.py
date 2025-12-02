#!/usr/bin/env python3
"""
hello_panel.py

Simple test: show scrolling text on the LED panel.
Works with:
- Raspberry Pi 3 B+
- Adafruit RGB Matrix Bonnet
- 64x32 HUB75 panel
"""

import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics


def create_matrix():
    options = RGBMatrixOptions()
    options.rows = 32           # your panel height
    options.cols = 64           # your panel width
    options.chain_length = 1
    options.parallel = 1

    # These match what you used with the C demo:
    options.hardware_mapping = "adafruit-hat"  # Bonnet uses same mapping
    options.scan_mode = 1                      # 1/16 scan on many 64x32 panels
    options.gpio_slowdown = 2                 # helps reduce flicker
    # options.brightness = 80                 # you can tweak later (0–100)

    return RGBMatrix(options=options)


def main():
    matrix = create_matrix()
    canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    # Adjust this path if needed:
    font.LoadFont("7x13.bdf")

    text_color = graphics.Color(255, 255, 0)
    message = "I Love You Rani!"
    pos = canvas.width

    try:
        while True:
            canvas.Clear()
            length = graphics.DrawText(canvas, font, pos, 18, text_color, message)
            pos -= 1
            if pos + length < 0:
                pos = canvas.width

            time.sleep(0.03)
            canvas = matrix.SwapOnVSync(canvas)

    except KeyboardInterrupt:
        canvas.Clear()
        matrix.Clear()


if __name__ == "__main__":
    main()
