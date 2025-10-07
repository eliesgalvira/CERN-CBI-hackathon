#!/usr/bin/env python3
import sys
import time
from collections import deque

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import serial.tools.list_ports

PORT = "/dev/ttyACM0"  # set to your device
BAUD = 9600
READ_TIMEOUT = 0.2  # seconds
RETRY_DELAY = 1.0   # seconds between open retries
MAX_POINTS = 2000   # number of points to keep in the plot window

# CSV line format expected from Arduino:
# timestamp_ms,raw,volts,...
# Header line may exist; we ignore non-numeric lines gracefully.


def find_port(preferred: str) -> str | None:
    # If preferred exists, use it. Otherwise, try first Arduino-like port.
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if p.device == preferred:
            return p.device
    # Fallback: pick the first /dev/ttyACM* or /dev/ttyUSB*
    for p in ports:
        if "ACM" in p.device or "USB" in p.device:
            return p.device
    return None


def open_serial():
    dev = find_port(PORT)
    if not dev:
        return None
    try:
        ser = serial.Serial(dev, BAUD, timeout=READ_TIMEOUT)
        # Give the board a moment to reset (common on Arduino)
        time.sleep(1.0)
        ser.reset_input_buffer()
        return ser
    except Exception:
        return None


def parse_line(line: str):
    # Return (t_ms, volts) or None if unparsable
    # We accept CSV with at least 3 fields: timestamp_ms,raw,volts
    try:
        parts = line.strip().split(",")
        if len(parts) < 3:
            return None
        t_ms = float(parts[0])
        volts = float(parts[2])
        return t_ms, volts
    except Exception:
        return None


def reader_generator():
    """
    Generator that yields (t_ms, volts) as data arrives.
    If port is missing or quiet, it keeps trying without crashing.
    """
    ser = None
    last_data_time = 0.0

    while True:
        if ser is None or not ser.is_open:
            ser = open_serial()
            if ser is None:
                time.sleep(RETRY_DELAY)
                continue
            last_data_time = 0.0

        try:
            line = ser.readline().decode("utf-8", errors="ignore")
            if not line:
                # No data this cycle
                # If the port vanished, try to reopen next loop
                if not ser.is_open:
                    ser = None
                continue

            data = parse_line(line)
            if data is None:
                # Ignore headers or malformed lines
                continue

            last_data_time = time.time()
            yield data

        except serial.SerialException:
            # Port disappeared; retry
            try:
                ser.close()
            except Exception:
                pass
            ser = None
            time.sleep(RETRY_DELAY)
        except UnicodeDecodeError:
            # Ignore junk bytes
            continue
        except Exception:
            # Unexpected error; keep running
            time.sleep(0.05)


def main():
    # Deques for rolling window
    xs = deque(maxlen=MAX_POINTS)
    ys = deque(maxlen=MAX_POINTS)

    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=1.5)
    ax.set_title("Live Voltage from Serial")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Volts")
    ax.grid(True)

    t0 = [None]  # mutable holder to capture first timestamp
    gen = reader_generator()

    def init():
        line.set_data([], [])
        return (line,)

    def update(_frame):
        # Pull several samples per animation frame for smoother plot
        pulled = 0
        max_pull = 200
        now_s = time.time()
        while pulled < max_pull:
            try:
                t_ms, v = next(gen)
            except StopIteration:
                break
            if t0[0] is None:
                t0[0] = t_ms
            xs.append((t_ms - t0[0]) / 1000.0)
            ys.append(v)
            pulled += 1

        if not xs:
            # No data yet; keep waiting
            return (line,)

        # Update plot limits dynamically
        line.set_data(xs, ys)
        ax.set_xlim(max(0, xs[0]), xs[-1] if xs[-1] > 5 else 5)

        # Y autoscale with a small margin
        ymin = min(ys)
        ymax = max(ys)
        if ymin == ymax:
            ymin -= 0.05
            ymax += 0.05
        pad = max(0.05, (ymax - ymin) * 0.1)
        ax.set_ylim(ymin - pad, ymax + pad)

        return (line,)

    ani = animation.FuncAnimation(
        fig, update, init_func=init, interval=50, blit=True
    )

    try:
        plt.show()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
