#!/usr/bin/env python3
"""
hello_panel.py
Scrolling LED text test.
"""

import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics


def create_matrix():
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1

    options.hardware_mapping = "adafruit-hat"
    options.scan_mode = 1
    options.gpio_slowdown = 2
    options.brightness = 80

    return RGBMatrix(options=options)


def main():
    matrix = create_matrix()
    canvas = matrix.CreateFrameCanvas()

    font = graphics.Font()
    font.LoadFont("7x13.bdf")

    message = "Hi MIRA DASWANI"
    color = graphics.Color(255, 200, 0)
    pos = canvas.width

    try:
        while True:
            canvas.Clear()
            length = graphics.DrawText(canvas, font, pos, 22, color, message)
            pos -= 1
            if pos + length < 0:
                pos = canvas.width
            canvas = matrix.SwapOnVSync(canvas)
            time.sleep(0.03)
    except KeyboardInterrupt:
        matrix.Clear()


if __name__ == "__main__":
    main()
