"""The toy car itself: position, heading, and the commands it accepts.

This module knows nothing about security.  It is the thing being protected.


You do not need to edit this file.
"""

import math
import threading
import time

FIELD = 400          # logical canvas size (px), matches the front-end <canvas>
STEP = 40            # pixels the car moves per command
MARGIN = 30          # keep the car this far from the walls

# Every command the car understands, and the action each one belongs to.
# Authorization is decided per action, not per command.
ACTION_OF = {
    "F": "move",
    "B": "move",
    "L": "move",
    "R": "move",
    "ADMIN_RESET": "admin_reset",
}
COMMANDS = set(ACTION_OF)
ACTIONS = sorted(set(ACTION_OF.values()))

lock = threading.Lock()
car = {"x": FIELD / 2, "y": FIELD / 2, "heading": 0}
last_command = {"command": "", "status": "", "ts": ""}


def now_str():
    return time.strftime("%H:%M:%S")


def state():
    with lock:
        return {**car, "last_command": dict(last_command)}


def reset():
    with lock:
        car.update({"x": FIELD / 2, "y": FIELD / 2, "heading": 0})
        last_command.update({"command": "", "status": "", "ts": ""})


def note(command, status):
    with lock:
        last_command.update({"command": command, "status": status,
                             "ts": now_str()})


def apply_command(command):
    """Move the car for one accepted command."""
    with lock:
        heading = car["heading"]
        if command == "L":
            car["heading"] = (heading - 90) % 360
        elif command == "R":
            car["heading"] = (heading + 90) % 360
        elif command in ("F", "B"):
            sign = 1 if command == "F" else -1
            rad = math.radians(heading)
            car["x"] += sign * STEP * math.sin(rad)       # heading 0 = up
            car["y"] -= sign * STEP * math.cos(rad)
            car["x"] = max(MARGIN, min(FIELD - MARGIN, car["x"]))
            car["y"] = max(MARGIN, min(FIELD - MARGIN, car["y"]))
        elif command == "ADMIN_RESET":
            car.update({"x": FIELD / 2, "y": FIELD / 2, "heading": 0})
