# Mini Real-Time Train Departure Board (Newton, NTN)

A small side project: a **real-time train departure board** for my kitchen wall, powered by a Raspberry Pi and a 64×32 RGB LED matrix.

It shows:

- Live departures for my local station (Newton, code `NTN`)
- Platform information
- Delay status (`STD -> ETD` when late)
- Colour-coded status (on time / delayed / cancelled)
- Auto-scrolling for long destinations
- A live HH:MM:SS clock in the corner

---

## Hardware

- **Raspberry Pi 3 Model B+**
- **Adafruit RGB Matrix Bonnet**
- **64×32 RGB LED matrix (HUB75, P4)**
- **5V 10A power supply** (panel + Pi from same PSU)
- Ribbon cable (HUB75)
- A jumper wires (common ground between Pi and panel)

---

## Software & Libraries

- Python 3
- `requests` (HTTP calls to the API)
- `rgbmatrix` (Henner Zeller’s rpi-rgb-led-matrix)
- Huxley2 public API (Darwin-powered live data)

Install the matrix library (summarised):

```bash
# Clone the matrix repo (if not already installed)
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix

# Build and install Python bindings
make build-python