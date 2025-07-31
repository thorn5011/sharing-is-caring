"""
Utility script to validate and cycle through all flags defined in ``flags.json``.

This script reads the ``flags.json`` file used by the monitor SQL project
and performs two tasks:

1. **Validation** – It verifies that each flag entry contains exactly 64
   colour codes and that each code corresponds to a colour defined in
   ``monitor_sql.py``. If a mismatch is found, details are printed.
2. **Display loop** – It optionally loops through all flags and displays
   them on a Sense HAT. When run on a system without a Sense HAT, it
   simply prints the flag codes in order.

Run the script directly to execute both the validation and (if the
Sense HAT library is available) to cycle through the flags with a
pause between them. Adjust the delay by passing a number of seconds
as the first command‑line argument.

Example usage:

    python test_flags.py 2

This will validate the flags and then show each flag on the Sense HAT
for two seconds. Without an argument it defaults to one second per
flag. If the Sense HAT is not detected, the script will skip
displaying and print the names of the flags instead.
"""

import json
import sys
import time
import os 

try:
    # Attempt to import the colour definitions and SenseHat from the
    # existing monitor_sql module. This module defines the ``colors``
    # dictionary mapping single‑letter codes to RGB tuples.

    # directory where the *symlink* lives
    this_dir = os.path.dirname(__file__)
    sys.path.insert(0, this_dir)

    from monitor import colors  # type: ignore
    from sense_hat import SenseHat  # type: ignore
    SENSE_AVAILABLE = True
except Exception as e:
    print(e)
    # Fallback if ``monitor_sql`` or Sense HAT are not available.
    colors = {
        "r": (255, 0, 0),
        "o": (255, 127, 0),
        "y": (255, 255, 0),
        "g": (0, 255, 0),
        "dg": (0, 106, 78),
        "bl": (0, 0, 0),
        "i": (75, 0, 130),
        "v": (159, 0, 255),
        "b": (0, 0, 255),
        "db": (0, 0, 139),
        "lb": (122, 197, 205),
        "rb": (0, 43, 127),
        "w": (255, 255, 255),
    }
    SENSE_AVAILABLE = False


def load_flags(path: str = "flags.json") -> dict:
    """Load flag data from a JSON file.

    Parameters
    ----------
    path: str
        Path to the JSON file containing flags. Defaults to the
        ``flags.json`` used in the monitor_sql project.

    Returns
    -------
    dict
        Dictionary of flag codes to lists of colour codes.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_flags(flags: dict) -> None:
    """Validate that each flag contains exactly 64 pixels and uses known colours."""
    valid = True
    valid_colors = set(colors.keys())
    for code, pixels in flags.items():
        if len(pixels) != 64:
            print(f"[ERROR] Flag {code} has {len(pixels)} pixels (expected 64).")
            valid = False
        unknown_colours = {c for c in pixels if c not in valid_colors}
        if unknown_colours:
            print(f"[ERROR] Flag {code} contains unknown colours: {sorted(unknown_colours)}")
            valid = False
    if valid:
        print("All flags passed validation.")


def show_flags(flags: dict, delay: float = 1.0) -> None:
    """Cycle through each flag and display it on the Sense HAT if available.

    If the Sense HAT is not available, this function prints the flag
    codes in order instead of attempting to set pixels.

    Parameters
    ----------
    flags: dict
        Dictionary of flag codes to pixel lists.
    delay: float
        Number of seconds to wait between flags when displaying.
    """

    if SENSE_AVAILABLE:
        sense = SenseHat()
        sense.low_light = True
        sense.set_rotation(180)
        for code, pixels in flags.items():
            # Translate single‑letter colour codes to RGB tuples
            rgb_pixels = [colors.get(c, (0, 0, 0)) for c in pixels]
            sense.set_pixels(rgb_pixels)
            print(f"Showing flag: {code}")
            time.sleep(delay)
        sense.clear()
    else:
        print("Sense HAT not detected; skipping display. Flags to loop through:")
        for code in flags.keys():
            print(code)


def main() -> None:
    flags = load_flags()
    validate_flags(flags)
    # Determine delay from command line if provided
    delay = 1.0
    if len(sys.argv) > 1:
        try:
            delay = float(sys.argv[1])
        except ValueError:
            print(f"Invalid delay '{sys.argv[1]}', using default of 1 second.")
    show_flags(flags, delay)


if __name__ == "__main__":
    main()
