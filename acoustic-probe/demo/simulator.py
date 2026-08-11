#!/usr/bin/env python3
"""
simulator.py — Runs a 5-minute simulated fishing trip for the FV Eileen.

Outputs telemetry as JSON every 5 seconds to stdout and optionally to a file.
The trip goes through all phases: harbor → depart → transit → fish → return.

Usage:
    python3 simulator.py                    # Print JSON to stdout
    python3 simulator.py --output telemetry.jsonl  # Also write to file
    python3 simulator.py --speed 2          # 2x speed (2.5 min real-time)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


# ─── Vessel Phases ──────────────────────────────────────────────────────────

PHASES = [
    # (name, start_fraction, end_fraction, description)
    ("departing",  0.00, 0.15, "Leaving harbor — engine rising, harbor clearing"),
    ("transit",    0.15, 0.40, "Steady cruise to fishing grounds"),
    ("fishing",    0.40, 0.70, "On the grounds — gear working, deep water"),
    ("transit",    0.70, 0.90, "Steaming back toward harbor"),
    ("returning",  0.90, 1.00, "Approaching harbor — slowing down"),
]


# ─── Telemetry State ────────────────────────────────────────────────────────

@dataclass
class Telemetry:
    timestamp: float           # Unix timestamp
    elapsed: float             # Seconds since trip start
    phase: str                 # Current trip phase
    phase_description: str     # Human-readable phase info
    rpm: float                 # Engine RPM (600-2800)
    speed_knots: float         # Speed over ground (0-10)
    depth_fathoms: float       # Water depth (2-80)
    sea_state: float           # Beaufort 0-9
    heading: float             # Compass degrees 0-360
    latitude: float            # Approximate position
    longitude: float           # Approximate position
    position_label: str        # Human-readable location
    trip_progress: float       # 0.0 to 1.0

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Simulator ──────────────────────────────────────────────────────────────

class FishingTripSimulator:
    """Simulates a 5-minute fishing trip with realistic telemetry patterns."""

    # Harbor and grounds positions (Kodiak area)
    HARBOR = (57.79, -152.40)
    GROUNDS = (57.55, -151.80)

    def __init__(
        self,
        duration_seconds: int = 300,
        step_seconds: int = 5,
        seed: int = 42,
    ):
        self.duration = duration_seconds
        self.step = step_seconds
        self.rng = random.Random(seed)
        self._sea_state = 3.0
        self._sea_trend = 0.0

    def run(self):
        """Generator yielding Telemetry objects every step_seconds."""
        total_steps = self.duration // self.step
        start_time = time.time()

        for step_num in range(total_steps + 1):
            elapsed = step_num * self.step
            progress = elapsed / self.duration

            phase, phase_desc = self._get_phase(progress)
            self._update_sea_state()

            tele = self._generate_telemetry(
                progress, phase, phase_desc, elapsed, start_time
            )
            yield tele

            if step_num < total_steps:
                time.sleep(self.step)

    def _get_phase(self, progress: float) -> tuple:
        for name, start, end, desc in PHASES:
            if start <= progress < end:
                return name, desc
        return "returning", PHASES[-1][3]

    def _phase_progress(self, progress: float) -> float:
        """How far into the current phase (0-1)."""
        for name, start, end, _ in PHASES:
            if start <= progress < end:
                if end == start:
                    return 1.0
                return (progress - start) / (end - start)
        return 1.0

    def _update_sea_state(self):
        """Slowly varying sea state with occasional gusts."""
        if self.rng.random() < 0.05:
            self._sea_trend = self.rng.uniform(-0.3, 0.3)
        target = 3.0 + self._sea_trend
        self._sea_state += (target - self._sea_state) * 0.02
        self._sea_state = max(0.5, min(8.0, self._sea_state))
        if self.rng.random() < 0.02:
            self._sea_state = max(0.5, min(8.0, self._sea_state + self.rng.uniform(-0.5, 0.8)))

    def _generate_telemetry(
        self, progress, phase, phase_desc, elapsed, start_time
    ) -> Telemetry:
        pp = self._phase_progress(progress)
        jitter = lambda amt: self.rng.uniform(-amt, amt)

        # Position interpolation
        if phase == "departing":
            lat = self._lerp(self.HARBOR[0], self.HARBOR[0] + 0.02, pp)
            lon = self._lerp(self.HARBOR[1], self.HARBOR[1] + 0.05, pp)
            pos_label = "Leaving Kodiak Harbor"
        elif phase == "transit" and progress < 0.50:
            lat = self._lerp(self.HARBOR[0] + 0.02, self.GROUNDS[0], pp)
            lon = self._lerp(self.HARBOR[1] + 0.05, self.GROUNDS[1], pp)
            pos_label = "Transiting — Shelikof Strait"
        elif phase == "fishing":
            lat = self.GROUNDS[0] + jitter(0.005)
            lon = self.GROUNDS[1] + jitter(0.005)
            pos_label = "Fishing grounds — near Shell Bank"
        elif phase == "transit":
            lat = self._lerp(self.GROUNDS[0], self.HARBOR[0] + 0.02, pp)
            lon = self._lerp(self.GROUNDS[1], self.HARBOR[1] + 0.05, pp)
            pos_label = "Transiting — returning"
        else:  # returning
            lat = self._lerp(self.HARBOR[0] + 0.02, self.HARBOR[0], pp)
            lon = self._lerp(self.HARBOR[1] + 0.05, self.HARBOR[1], pp)
            pos_label = "Approaching Kodiak Harbor"

        # Phase-specific telemetry
        if phase == "departing":
            rpm = 600 + 1200 * pp + jitter(60)
            speed = 1.0 + 5.0 * pp + jitter(0.3)
            depth = 3 + 20 * pp + jitter(2)
            heading = 180 + jitter(8)
        elif phase == "transit" and progress < 0.50:
            rpm = 1800 + jitter(100)
            speed = 7.0 + jitter(0.5)
            depth = 25 + 30 * pp + jitter(3)
            heading = 200 + jitter(5)
        elif phase == "fishing":
            # Cyclic RPM: gear going out and in
            cycle = math.sin(elapsed * 0.15) * 0.5 + 0.5
            gear_cycle = math.sin(elapsed * 0.08) * 0.5 + 0.5
            rpm = 850 + cycle * 600 + jitter(80)
            speed = 2.0 + gear_cycle * 1.5 + jitter(0.4)
            depth = 55 + 20 * math.sin(elapsed * 0.05) + jitter(3)
            heading = (45 + elapsed * 2) % 360 + jitter(3)
        elif phase == "transit":
            rpm = 1700 + jitter(100)
            speed = 6.5 + jitter(0.5)
            depth = 55 - 35 * pp + jitter(3)
            heading = 20 + jitter(5)
        else:  # returning
            rpm = 1200 - 500 * pp + jitter(60)
            speed = 5.0 - 3.0 * pp + jitter(0.3)
            depth = max(3, 20 - 17 * pp) + jitter(2)
            heading = 350 + jitter(5)

        return Telemetry(
            timestamp=start_time + elapsed,
            elapsed=elapsed,
            phase=phase,
            phase_description=phase_desc,
            rpm=round(rpm, 1),
            speed_knots=round(speed, 2),
            depth_fathoms=round(depth, 1),
            sea_state=round(self._sea_state, 1),
            heading=round(heading % 360, 1),
            latitude=round(lat, 5),
            longitude=round(lon, 5),
            position_label=pos_label,
            trip_progress=round(progress, 3),
        )

    @staticmethod
    def _lerp(a, b, t):
        return a + (b - a) * t


# ─── Shared State File ──────────────────────────────────────────────────────

SHARED_STATE_FILE = os.path.join(os.path.dirname(__file__), "telemetry.json")


def write_shared_state(tele: Telemetry):
    """Write current telemetry to a shared JSON file for the web UI to read."""
    with open(SHARED_STATE_FILE, "w") as f:
        json.dump(tele.to_dict(), f, indent=2)


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="FV Eileen — 5-minute fishing trip simulator"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSONL file for full telemetry log",
        default=None,
    )
    parser.add_argument(
        "--speed", "-s", type=float, default=1.0,
        help="Time speed multiplier (2 = twice as fast)",
    )
    parser.add_argument(
        "--duration", "-d", type=int, default=300,
        help="Trip duration in seconds (default: 300 = 5 minutes)",
    )
    parser.add_argument(
        "--step", type=int, default=5,
        help="Telemetry interval in seconds (default: 5)",
    )
    args = parser.parse_args()

    duration = int(args.duration / args.speed)
    step = max(1, int(args.step / args.speed))

    sim = FishingTripSimulator(
        duration_seconds=duration,
        step_seconds=step,
    )

    output_file = None
    if args.output:
        output_file = open(args.output, "w")

    print(f"FV Eileen — Fishing Trip Simulator", file=sys.stderr)
    print(f"  Duration: {duration}s ({duration/60:.1f} min at {args.speed}x speed)", file=sys.stderr)
    print(f"  Step: every {step}s", file=sys.stderr)
    print(f"  Output: {args.output or 'stdout only'}", file=sys.stderr)
    print(f"  Shared state: {SHARED_STATE_FILE}", file=sys.stderr)
    print(file=sys.stderr)

    try:
        for tele in sim.run():
            line = json.dumps(tele.to_dict())
            print(line)
            sys.stdout.flush()

            if output_file:
                output_file.write(line + "\n")
                output_file.flush()

            write_shared_state(tele)

    except KeyboardInterrupt:
        print("\n[Simulator stopped by user]", file=sys.stderr)
    finally:
        if output_file:
            output_file.close()

    print("[Simulator finished]", file=sys.stderr)


if __name__ == "__main__":
    main()
