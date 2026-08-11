"""
telemetry_simulator.py — Simulates FV Eileen's telemetry for testing.

Generates realistic fishing vessel patterns:
- Leaving harbor (low RPM, shallow, heading out)
- Transit (high RPM, medium depth, steady course)
- Fishing (variable RPM, deep, slow speed, gear working)
- Return (moderate RPM, shallow, heading back)

Sea state varies by time and weather simulation.

Usage:
    sim = TelemetrySimulator()
    for state in sim.run_fishing_trip(duration_hours=8):
        print(state)
"""

from __future__ import annotations
import math
import random
import time
from dataclasses import dataclass, field
from typing import Iterator, Optional, List

from vessel_instrument import VesselState, VesselMode


# ─── Simulation Parameters ──────────────────────────────────────────────────

# Kodiak Island area approximate bounds
KODIAK_HARBOR = (57.79, -152.40)
KODIAK_FISHING_GROUNDS = (57.55, -151.80)  # Shell Bank area-ish

# Engine characteristics (Detroit Diesel 8V-71 typical for fishing vessels)
IDLE_RPM = 600
CRUISE_RPM = 1800
MAX_RPM = 2800
TROLL_RPM = 900  # Slow while fishing

# Trip phases (fraction of total duration)
PHASE_DOCKED = 0.0      # Start
PHASE_DEPART = 0.05     # First 5% — leaving harbor
PHASE_TRANSIT_OUT = 0.20  # 5-20% — steaming to grounds
PHASE_FISHING = 0.65    # 20-65% — fishing
PHASE_TRANSIT_IN = 0.90  # 65-90% — steaming back
PHASE_RETURN = 1.0      # 90-100% — approaching harbor


# ─── Weather Simulation ─────────────────────────────────────────────────────

@dataclass
class WeatherState:
    """Simple weather model for sea state simulation."""
    base_sea_state: float = 2.0
    trend: float = 0.0          # Is it getting rougher or calmer?
    gust_timer: float = 0.0     # Count down to next gust change
    current_sea_state: float = 2.0

    def update(self, dt_hours: float):
        """Advance weather by dt_hours."""
        # Slowly drift the trend
        if random.random() < 0.1 * dt_hours:
            self.trend = random.uniform(-0.5, 0.5)

        # Move sea state toward base + trend
        target = self.base_sea_state + self.trend
        self.current_sea_state += (target - self.current_sea_state) * 0.1 * dt_hours

        # Random gusts
        self.gust_timer -= dt_hours
        if self.gust_timer <= 0:
            self.gust_timer = random.uniform(0.5, 3.0)  # hours
            gust = random.uniform(-1.0, 1.5)
            self.current_sea_state = max(0.0, min(9.0, self.current_sea_state + gust))

        self.current_sea_state = max(0.0, min(9.0, self.current_sea_state))


# ─── Simulator ──────────────────────────────────────────────────────────────

class TelemetrySimulator:
    """Simulates realistic FV Eileen telemetry over time."""

    def __init__(
        self,
        start_position: tuple = KODIAK_HARBOR,
        fishing_grounds: tuple = KODIAK_FISHING_GROUNDS,
        seed: Optional[int] = None,
    ):
        self.start_pos = start_position
        self.fishing_pos = fishing_grounds
        self.weather = WeatherState()
        self._rng = random.Random(seed)

        # Compute trip distance for navigation
        self.trip_distance_nm = self._haversine_nm(
            start_position[0], start_position[1],
            fishing_grounds[0], fishing_grounds[1]
        )

    def run_fishing_trip(
        self,
        duration_hours: float = 8.0,
        step_minutes: float = 5.0,
    ) -> Iterator[VesselState]:
        """Simulate a complete fishing trip.

        Yields VesselState objects at each time step.
        """
        total_steps = int(duration_hours * 60 / step_minutes)
        dt_hours = step_minutes / 60.0

        for step in range(total_steps):
            progress = step / total_steps
            elapsed_hours = step * dt_hours

            # Determine phase
            phase = self._get_phase(progress)

            # Update weather
            self.weather.update(dt_hours)

            # Generate state for this phase
            state = self._generate_state(phase, progress, elapsed_hours)
            yield state

    def run_phase(
        self,
        phase: VesselMode,
        duration_hours: float = 1.0,
        step_minutes: float = 2.0,
        start_state: Optional[VesselState] = None,
    ) -> Iterator[VesselState]:
        """Run a single phase in detail (e.g., just fishing)."""
        total_steps = int(duration_hours * 60 / step_minutes)
        dt_hours = step_minutes / 60.0

        current = start_state or VesselState()
        current.mode = phase

        for step in range(total_steps):
            self.weather.update(dt_hours)
            state = self._generate_detailed_phase(phase, step, total_steps, current, dt_hours)
            yield state
            current = state

    def _get_phase(self, progress: float) -> VesselMode:
        """Determine vessel mode based on trip progress."""
        if progress < PHASE_DEPART:
            return VesselMode.DOCKED
        elif progress < PHASE_TRANSIT_OUT:
            return VesselMode.DEPARTING
        elif progress < PHASE_FISHING:
            return VesselMode.TRANSIT
        elif progress < PHASE_TRANSIT_IN:
            return VesselMode.FISHING
        elif progress < PHASE_RETURN:
            return VesselMode.TRANSIT
        else:
            return VesselMode.RETURNING

    def _generate_state(
        self, phase: VesselMode, progress: float, elapsed_hours: float
    ) -> VesselState:
        """Generate a realistic vessel state for the given phase."""
        sea = self.weather.current_sea_state

        if phase == VesselMode.DOCKED:
            return VesselState(
                rpm=IDLE_RPM + self._jitter(50),
                depth=2 + self._jitter(1),
                sea_state=max(0, sea - 1),  # Harbor is calmer
                heading=self._bearing(self.start_pos, self.start_pos) + self._jitter(10),
                speed=0.3 + self._jitter(0.2),
                latitude=self.start_pos[0] + self._jitter(0.001),
                longitude=self.start_pos[1] + self._jitter(0.001),
                mode=phase,
            )

        elif phase == VesselMode.DEPARTING:
            # Leaving harbor: RPM rising, heading out, speed increasing
            local_progress = (progress - PHASE_DEPART) / (PHASE_TRANSIT_OUT - PHASE_DEPART)
            rpm = IDLE_RPM + (CRUISE_RPM - IDLE_RPM) * local_progress + self._jitter(100)
            heading = self._bearing(self.start_pos, self.fishing_pos) + self._jitter(5)
            speed = 2.0 + 4.0 * local_progress + self._jitter(0.5)

            return VesselState(
                rpm=rpm,
                depth=2 + 15 * local_progress + self._jitter(2),
                sea_state=sea,
                heading=heading,
                speed=speed,
                latitude=self._lerp(self.start_pos[0], self.fishing_pos[0], local_progress * 0.3) + self._jitter(0.001),
                longitude=self._lerp(self.start_pos[1], self.fishing_pos[1], local_progress * 0.3) + self._jitter(0.001),
                mode=phase,
            )

        elif phase == VesselMode.TRANSIT:
            # Steaming to/from grounds
            is_outbound = progress < PHASE_FISHING
            if is_outbound:
                local_progress = (progress - PHASE_TRANSIT_OUT) / (PHASE_FISHING - PHASE_TRANSIT_OUT)
                start, end = self.start_pos, self.fishing_pos
            else:
                local_progress = (progress - PHASE_TRANSIT_IN) / (PHASE_RETURN - PHASE_TRANSIT_IN)
                start, end = self.fishing_pos, self.start_pos

            return VesselState(
                rpm=CRUISE_RPM + self._jitter(150),
                depth=15 + 40 * min(1.0, local_progress) + self._jitter(5),
                sea_state=sea,
                heading=self._bearing(start, end) + self._jitter(8),
                speed=7.0 + self._jitter(1.0),
                latitude=self._lerp(start[0], end[0], local_progress) + self._jitter(0.002),
                longitude=self._lerp(start[1], end[1], local_progress) + self._jitter(0.002),
                mode=phase,
            )

        elif phase == VesselMode.FISHING:
            # On the grounds: slow, deep water, RPM varying with gear
            # Occasionally haul (RPM spike, speed drop)
            hauling = self._rng.random() < 0.15
            fishing_spot_offset_lat = self._jitter(0.01)
            fishing_spot_offset_lon = self._jitter(0.01)

            if hauling:
                rpm = TROLL_RPM + 800 + self._jitter(200)  # Winch pulling
                speed = 0.5 + self._jitter(0.5)
            else:
                rpm = TROLL_RPM + self._jitter(100)  # Trawling/trolling
                speed = 2.5 + self._jitter(0.8)

            return VesselState(
                rpm=rpm,
                depth=45 + 30 * abs(math.sin(elapsed_hours * 0.5)) + self._jitter(5),
                sea_state=sea,
                heading=self._rng.uniform(0, 360),  # Varies while fishing
                speed=speed,
                latitude=self.fishing_pos[0] + fishing_spot_offset_lat,
                longitude=self.fishing_pos[1] + fishing_spot_offset_lon,
                mode=VesselMode.HAULING if hauling else VesselMode.FISHING,
            )

        elif phase == VesselMode.RETURNING:
            local_progress = (progress - PHASE_RETURN) / (1.0 - PHASE_RETURN)
            rpm = CRUISE_RPM - 400 * local_progress + self._jitter(100)
            heading = self._bearing(self.fishing_pos, self.start_pos) + self._jitter(5)

            return VesselState(
                rpm=rpm,
                depth=max(2, 20 - 18 * local_progress) + self._jitter(2),
                sea_state=sea,
                heading=heading,
                speed=6.0 - 3.0 * local_progress + self._jitter(0.5),
                latitude=self._lerp(self.fishing_pos[0], self.start_pos[0], local_progress) + self._jitter(0.001),
                longitude=self._lerp(self.fishing_pos[1], self.start_pos[1], local_progress) + self._jitter(0.001),
                mode=phase,
            )

        return VesselState()

    def _generate_detailed_phase(
        self,
        phase: VesselMode,
        step: int,
        total_steps: int,
        current: VesselState,
        dt_hours: float,
    ) -> VesselState:
        """Generate detailed within-phase telemetry with smooth transitions."""
        progress = step / total_steps
        sea = self.weather.current_sea_state

        # Gradual RPM changes (engines don't change instantly)
        target_rpm = current.rpm
        if phase == VesselMode.FISHING:
            # Cyclic RPM pattern — trawling with periodic hauls
            cycle = math.sin(step * 0.1) * 0.5 + 0.5
            target_rpm = TROLL_RPM + cycle * 1000
        elif phase == VesselMode.TRANSIT:
            target_rpm = CRUISE_RPM

        rpm = current.rpm + (target_rpm - current.rpm) * 0.1

        # Gradual heading changes
        heading_drift = self._jitter(2)
        heading = (current.heading + heading_drift) % 360.0

        return VesselState(
            rpm=max(0, rpm),
            depth=current.depth + self._jitter(2),
            sea_state=sea,
            heading=heading,
            speed=max(0, current.speed + self._jitter(0.3)),
            latitude=current.latitude + self._jitter(0.002),
            longitude=current.longitude + self._jitter(0.002),
            mode=phase,
        )

    # ── Utilities ──

    def _jitter(self, amount: float) -> float:
        """Random noise."""
        return self._rng.uniform(-amount, amount)

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    @staticmethod
    def _bearing(start: tuple, end: tuple) -> float:
        """Compass bearing from start to end (degrees)."""
        lat1, lon1 = math.radians(start[0]), math.radians(start[1])
        lat2, lon2 = math.radians(end[0]), math.radians(end[1])
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    @staticmethod
    def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Distance in nautical miles."""
        R = 3440.065  # Earth radius in nm
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── Replay Support ─────────────────────────────────────────────────────────

def replay_telemetry(records: List[dict]) -> Iterator[VesselState]:
    """Replay historical AIS/telemetry data.

    Args:
        records: List of dicts with vessel state keys and timestamps.
    """
    for record in sorted(records, key=lambda r: r.get("timestamp", 0)):
        state = VesselState(
            rpm=record.get("rpm", 0),
            depth=record.get("depth", 0),
            sea_state=record.get("sea_state", 0),
            heading=record.get("heading", 0),
            speed=record.get("speed", 0),
            latitude=record.get("latitude", 0),
            longitude=record.get("longitude", 0),
            timestamp=record.get("timestamp", time.time()),
        )
        mode_str = record.get("mode", "")
        try:
            state.mode = VesselMode(mode_str)
        except ValueError:
            pass
        yield state


# ─── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sim = TelemetrySimulator(seed=42)

    print("═══ FV Eileen — Telemetry Simulation ═══")
    print(f"  Trip: Kodiak Harbor → Fishing Grounds")
    print(f"  Distance: {sim.trip_distance_nm:.1f} nm")
    print(f"  Duration: 8 hours, 5-min steps")
    print(f"  {'─' * 70}")

    for i, state in enumerate(sim.run_fishing_trip(duration_hours=8, step_minutes=30)):
        sea_bar = "🌊" * int(state.sea_state) if state.sea_state > 0 else "📭"
        print(
            f"  [{state.mode.value:12s}] "
            f"RPM:{state.rpm:5.0f} "
            f"SPD:{state.speed:4.1f}kt "
            f"HDG:{state.heading:5.0f}° "
            f"DEP:{state.depth:5.0f}f "
            f"SEA:{state.sea_state:.1f} {sea_bar}"
        )

    print(f"  {'─' * 70}")
    print("  Trip complete.")
