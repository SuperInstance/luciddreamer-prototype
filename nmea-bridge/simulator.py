"""
simulator.py — Simulates a full fishing trip for testing the NMEA bridge.

Generates realistic NMEA 0183 sentences for a fishing vessel:
    Harbor departure → transit out → fishing → transit back → arrival

Simulates:
    - GPS position (GPGGA, GPRMC) with realistic Kodiak-area coordinates
    - Depth (SDDBT, SDDPT) — shallow near shore, deep at fishing grounds
    - Heading (HDT, HDG) — course changes at each phase
    - Speed (GPRMC, VHW) — varies by mode
    - Water temperature (MTW) — colder at depth/grounds
    - Engine RPM (XDR) — varies by mode
    - Tank level (XDR) — decreases over time
    - Battery voltage (XDR)

Outputs NMEA sentences on a TCP socket (localhost:10110 — standard NMEA port)
and/or returns them as an iterator for direct consumption.

Usage:
    # As a generator:
    sim = TripSimulator()
    for sentence in sim.generate(duration_minutes=30):
        print(sentence)

    # As a TCP server:
    sim = TripSimulator()
    sim.serve_tcp(port=10110, duration_minutes=30)
"""

from __future__ import annotations

import math
import random
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Iterator, Optional, List, Tuple
from enum import Enum


# ─── Geographic Constants ───────────────────────────────────────────────────

KODIAK_HARBOR = (57.7900, -152.4070)        # St. Paul Harbor, Kodiak
KODIAK_FISHING_GROUNDS = (57.5500, -151.8000)  # ~30nm SE, near Shell Bank area

# Earth radius in nautical miles
EARTH_RADIUS_NM = 3440.065


# ─── Trip Phases ────────────────────────────────────────────────────────────

class TripPhase(Enum):
    DOCKED = "docked"
    DEPARTING = "departing"
    TRANSIT_OUT = "transit_out"
    ARRIVING_GROUNDS = "arriving_grounds"
    FISHING = "fishing"
    HAULING = "hauling"
    TRANSIT_IN = "transit_in"
    ARRIVING_HARBOR = "arriving_harbor"
    DONE = "done"


PHASE_BOUNDARIES = {
    # (start_fraction, end_fraction)
    TripPhase.DOCKED:           (0.00, 0.03),
    TripPhase.DEPARTING:        (0.03, 0.08),
    TripPhase.TRANSIT_OUT:      (0.08, 0.25),
    TripPhase.ARRIVING_GROUNDS: (0.25, 0.28),
    TripPhase.FISHING:          (0.28, 0.65),
    TripPhase.HAULING:          (0.65, 0.70),
    TripPhase.TRANSIT_IN:       (0.70, 0.90),
    TripPhase.ARRIVING_HARBOR:  (0.90, 0.97),
    # 0.97-1.0: docked again
}


# ─── Simulation State ───────────────────────────────────────────────────────

@dataclass
class SimState:
    """Current simulation state."""
    lat: float = KODIAK_HARBOR[0]
    lon: float = KODIAK_HARBOR[1]
    heading: float = 0.0
    speed: float = 0.0          # knots
    rpm: float = 0.0
    depth: float = 3.0          # fathoms
    water_temp: float = 9.5     # Celsius
    tank_level: float = 95.0    # %
    battery_voltage: float = 13.2
    sea_state: float = 2.0
    phase: TripPhase = TripPhase.DOCKED
    elapsed_fraction: float = 0.0


# ─── Helpers ────────────────────────────────────────────────────────────────

def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance between two points in nautical miles."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    return EARTH_RADIUS_NM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_to(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from point 1 to point 2 in degrees."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.cos(lat2_r) * math.sin(dlon)
    y = (math.cos(lat1_r) * math.sin(lat2_r) -
         math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def destination_point(lat: float, lon: float, bearing_deg: float,
                      distance_nm: float) -> Tuple[float, float]:
    """Destination point given start, bearing, and distance."""
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    brg_r = math.radians(bearing_deg)
    d = distance_nm / EARTH_RADIUS_NM

    lat2 = math.asin(math.sin(lat_r) * math.cos(d) +
                     math.cos(lat_r) * math.sin(d) * math.cos(brg_r))
    lon2 = lon_r + math.atan2(
        math.sin(brg_r) * math.sin(d) * math.cos(lat_r),
        math.cos(d) - math.sin(lat_r) * math.sin(lat2)
    )
    return math.degrees(lat2), ((math.degrees(lon2) + 540) % 360 - 180)


def interpolate(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def ease_in_out(t: float) -> float:
    """Smooth ease in/out."""
    return t * t * (3 - 2 * t)


# ─── NMEA Sentence Builders ─────────────────────────────────────────────────

def build_checksum(body: str) -> str:
    """Compute NMEA checksum for a sentence body (without $ and *)."""
    cs = 0
    for ch in body:
        cs ^= ord(ch)
    return f"{cs:02X}"


def make_gga(lat: float, lon: float, fix: int, sats: int,
             time_str: str = "120000") -> str:
    """Build a $GPGGA sentence."""
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    lat_abs = abs(lat)
    lon_abs = abs(lon)
    lat_min = (lat_abs % 1) * 60
    lon_min = (lon_abs % 1) * 60
    lat_str = f"{int(lat_abs):02d}{lat_min:07.4f}"
    lon_str = f"{int(lon_abs):03d}{lon_min:07.4f}"
    body = f"GPGGA,{time_str},{lat_str},{lat_dir},{lon_str},{lon_dir},{fix},{sats:02d},0.9,5.4,M,46.9,M,,"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_rmc(lat: float, lon: float, speed: float, course: float,
             time_str: str = "120000", date_str: str = "110826") -> str:
    """Build a $GPRMC sentence."""
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    lat_abs = abs(lat)
    lon_abs = abs(lon)
    lat_min = (lat_abs % 1) * 60
    lon_min = (lon_abs % 1) * 60
    lat_str = f"{int(lat_abs):02d}{lat_min:07.4f}"
    lon_str = f"{int(lon_abs):03d}{lon_min:07.4f}"
    body = f"GPRMC,{time_str},A,{lat_str},{lat_dir},{lon_str},{lon_dir},{speed:.1f},{course:.1f},{date_str},,," 
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_dbt(depth_fathoms: float) -> str:
    """Build a $SDDBT sentence."""
    feet = depth_fathoms * 6.0
    meters = depth_fathoms * 1.8288
    body = f"SDDBT,{feet:.1f},f,{meters:.1f},M,{depth_fathoms:.1f},F"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_dpt(depth_meters: float) -> str:
    """Build a $SDDPT sentence."""
    body = f"SDDPT,{depth_meters:.1f},0.0,200.0"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_hdt(heading: float) -> str:
    """Build a $HCHDT sentence."""
    body = f"HCHDT,{heading:.1f},T"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_hdg(heading_mag: float, variation: float, var_dir: str = 'E') -> str:
    """Build a $HCHDG sentence."""
    body = f"HCHDG,{heading_mag:.1f},,,{variation:.1f},{var_dir}"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_mtw(temp_c: float) -> str:
    """Build a $YXMTW sentence."""
    body = f"YXMTW,{temp_c:.1f},C"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_vhw(heading: float, speed_kts: float) -> str:
    """Build a $VWVHW sentence."""
    body = f"VWVHW,{heading:.1f},T,{heading:.1f},M,{speed_kts:.1f},N,{speed_kts * 1.852:.1f},K"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_xdr_rpm(rpm: float) -> str:
    """Build an XDR sentence for engine RPM."""
    body = f"IIXDR,R,{rpm:.0f},RPM,ENGINE"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_xdr_tank(level_pct: float) -> str:
    """Build an XDR sentence for fuel tank level."""
    body = f"IIXDR,T,{level_pct:.1f},P,FUEL"
    cs = build_checksum(body)
    return f"${body}*{cs}"


def make_xdr_battery(voltage: float) -> str:
    """Build an XDR sentence for battery voltage."""
    body = f"IIXDR,V,{voltage:.2f},V,BATTERY"
    cs = build_checksum(body)
    return f"${body}*{cs}"


# ─── Trip Simulator ─────────────────────────────────────────────────────────

class TripSimulator:
    """Simulates a complete fishing trip, generating NMEA sentences.

    The simulation runs for a specified duration and generates NMEA sentences
    at realistic rates (GPS ~1Hz, depth ~1Hz, heading ~10Hz, etc.).
    """

    def __init__(
        self,
        start_pos: Tuple[float, float] = KODIAK_HARBOR,
        fishing_pos: Tuple[float, float] = KODIAK_FISHING_GROUNDS,
        seed: Optional[int] = None,
    ):
        self.start_pos = start_pos
        self.fishing_pos = fishing_pos
        self._rng = random.Random(seed)
        self.trip_distance_nm = haversine_nm(
            start_pos[0], start_pos[1], fishing_pos[0], fishing_pos[1]
        )

        # Simulation clock
        self._sim_time = 0.0  # seconds

    def _get_phase(self, frac: float) -> TripPhase:
        """Get current phase from elapsed fraction."""
        for phase, (start, end) in PHASE_BOUNDARIES.items():
            if start <= frac < end:
                return phase
        if frac >= 0.97:
            return TripPhase.DOCKED  # Back at dock
        return TripPhase.DONE

    def _simulate_state(self, frac: float, base_sea: float = 2.0) -> SimState:
        """Compute simulation state at a given fraction of the trip."""
        phase = self._get_phase(frac)
        state = SimState()
        state.phase = phase
        state.elapsed_fraction = frac

        # Vary sea state slowly
        state.sea_state = max(0.0, min(9.0,
            base_sea + self._rng.gauss(0, 0.5) + math.sin(frac * math.pi * 2) * 1.0
        ))

        if phase == TripPhase.DOCKED:
            state.lat = self.start_pos[0]
            state.lon = self.start_pos[1]
            state.heading = 0
            state.speed = 0.0
            state.rpm = 600
            state.depth = 3.0
            state.water_temp = 10.0
            state.tank_level = 95.0
            state.battery_voltage = 13.2

        elif phase == TripPhase.DEPARTING:
            local = (frac - PHASE_BOUNDARIES[TripPhase.DEPARTING][0]) / (
                PHASE_BOUNDARIES[TripPhase.DEPARTING][1] - PHASE_BOUNDARIES[TripPhase.DEPARTING][0])
            local = ease_in_out(local)
            bearing = bearing_to(*self.start_pos, *self.fishing_pos)
            dist = local * 0.3  # ~0.3 nm from harbor
            state.lat, state.lon = destination_point(*self.start_pos, bearing, dist)
            state.heading = bearing
            state.speed = interpolate(0.5, 5.0, local)
            state.rpm = interpolate(600, 1800, local)
            state.depth = interpolate(3.0, 15.0, local)
            state.water_temp = 9.5
            state.tank_level = 95.0 - frac * 20

        elif phase == TripPhase.TRANSIT_OUT:
            local = (frac - PHASE_BOUNDARIES[TripPhase.TRANSIT_OUT][0]) / (
                PHASE_BOUNDARIES[TripPhase.TRANSIT_OUT][1] - PHASE_BOUNDARIES[TripPhase.TRANSIT_OUT][0])
            local = ease_in_out(local)
            bearing = bearing_to(*self.start_pos, *self.fishing_pos)
            dist = 0.3 + local * (self.trip_distance_nm - 0.5)
            state.lat, state.lon = destination_point(*self.start_pos, bearing, dist)
            state.heading = bearing + self._rng.gauss(0, 2)
            state.speed = 7.5 + self._rng.gauss(0, 0.3)
            state.rpm = 1800 + self._rng.gauss(0, 30)
            state.depth = interpolate(15.0, 55.0, local)
            state.water_temp = interpolate(9.5, 7.5, local)
            state.tank_level = 95.0 - frac * 20

        elif phase == TripPhase.ARRIVING_GROUNDS:
            local = (frac - PHASE_BOUNDARIES[TripPhase.ARRIVING_GROUNDS][0]) / (
                PHASE_BOUNDARIES[TripPhase.ARRIVING_GROUNDS][1] - PHASE_BOUNDARIES[TripPhase.ARRIVING_GROUNDS][0])
            local = ease_in_out(local)
            # Slow down as we arrive
            state.lat, state.lon = destination_point(
                *self.fishing_pos, self._rng.uniform(0, 360),
                self._rng.uniform(0.1, 0.5))
            state.heading = bearing_to(*self.start_pos, *self.fishing_pos)
            state.speed = interpolate(7.0, 1.5, local)
            state.rpm = interpolate(1800, 900, local)
            state.depth = interpolate(55.0, 62.0, local)
            state.water_temp = 7.0

        elif phase == TripPhase.FISHING:
            # Hover around fishing grounds, depth varies
            local = (frac - PHASE_BOUNDARIES[TripPhase.FISHING][0]) / (
                PHASE_BOUNDARIES[TripPhase.FISHING][1] - PHASE_BOUNDARIES[TripPhase.FISHING][0])
            state.lat, state.lon = destination_point(
                *self.fishing_pos, self._rng.uniform(0, 360),
                self._rng.uniform(0, 0.3))
            state.heading = self._rng.uniform(0, 360)
            state.speed = max(0.3, 1.5 + self._rng.gauss(0, 0.5))
            state.rpm = max(600, 800 + self._rng.gauss(0, 100))
            # Depth varies as we search for fish
            state.depth = 55.0 + 10.0 * math.sin(local * math.pi * 6) + self._rng.gauss(0, 2)
            state.water_temp = 7.0 + self._rng.gauss(0, 0.3)
            state.tank_level = 90.0 - frac * 25

        elif phase == TripPhase.HAULING:
            local = (frac - PHASE_BOUNDARIES[TripPhase.HAULING][0]) / (
                PHASE_BOUNDARIES[TripPhase.HAULING][1] - PHASE_BOUNDARIES[TripPhase.HAULING][0])
            state.lat, state.lon = self.fishing_pos
            state.heading = self._rng.uniform(0, 360)
            state.speed = 0.5 + self._rng.gauss(0, 0.2)
            state.rpm = interpolate(800, 1200, local)
            state.depth = 60.0
            state.water_temp = 7.5
            state.tank_level = 75.0 - frac * 10

        elif phase == TripPhase.TRANSIT_IN:
            local = (frac - PHASE_BOUNDARIES[TripPhase.TRANSIT_IN][0]) / (
                PHASE_BOUNDARIES[TripPhase.TRANSIT_IN][1] - PHASE_BOUNDARIES[TripPhase.TRANSIT_IN][0])
            local = ease_in_out(local)
            bearing = bearing_to(*self.fishing_pos, *self.start_pos)
            dist = local * self.trip_distance_nm
            state.lat, state.lon = destination_point(*self.fishing_pos, bearing, dist)
            state.heading = bearing + self._rng.gauss(0, 2)
            state.speed = 7.0 + self._rng.gauss(0, 0.3)
            state.rpm = 1800 + self._rng.gauss(0, 30)
            state.depth = interpolate(55.0, 15.0, local)
            state.water_temp = interpolate(7.0, 9.5, local)
            state.tank_level = 70.0 - frac * 15

        elif phase == TripPhase.ARRIVING_HARBOR:
            local = (frac - PHASE_BOUNDARIES[TripPhase.ARRIVING_HARBOR][0]) / (
                PHASE_BOUNDARIES[TripPhase.ARRIVING_HARBOR][1] - PHASE_BOUNDARIES[TripPhase.ARRIVING_HARBOR][0])
            local = ease_in_out(local)
            bearing = bearing_to(*self.fishing_pos, *self.start_pos)
            dist = 0.3 * (1 - local)
            state.lat, state.lon = destination_point(*self.start_pos, bearing + 180, dist)
            state.heading = bearing + 180
            state.speed = interpolate(5.0, 0.5, local)
            state.rpm = interpolate(1800, 600, local)
            state.depth = interpolate(15.0, 3.0, local)
            state.water_temp = 9.5
            state.tank_level = 55.0 - frac * 5

        else:  # DOCKED (final) or DONE
            state.lat = self.start_pos[0]
            state.lon = self.start_pos[1]
            state.heading = 0
            state.speed = 0.0
            state.rpm = 600
            state.depth = 3.0
            state.water_temp = 10.0
            state.tank_level = 50.0

        return state

    def generate_sentences(self, state: SimState, sim_seconds: float) -> List[str]:
        """Generate all NMEA sentences for a single update cycle."""
        # Simulated time string
        hours = int(sim_seconds // 3600) % 24
        minutes = int((sim_seconds % 3600) // 60)
        seconds = int(sim_seconds % 60)
        time_str = f"{hours:02d}{minutes:02d}{seconds:02d}"
        date_str = "110826"

        sentences = []

        # GPS — every cycle
        sats = 8 + int(self._rng.gauss(0, 1))
        sentences.append(make_gga(state.lat, state.lon, fix=1, sats=max(4, min(12, sats)),
                                  time_str=time_str))

        # Course and speed
        course = state.heading
        sentences.append(make_rmc(state.lat, state.lon, state.speed, course,
                                  time_str=time_str, date_str=date_str))

        # Depth
        sentences.append(make_dbt(state.depth))
        depth_m = state.depth * 1.8288
        sentences.append(make_dpt(depth_m))

        # Heading
        variation = 15.5  # Kodiak magnetic variation
        sentences.append(make_hdt(state.heading))
        sentences.append(make_hdg(state.heading % 360, variation, 'E'))

        # Water speed/heading
        stw = state.speed + self._rng.gauss(0, 0.1)
        sentences.append(make_vhw(state.heading, max(0, stw)))

        # Water temperature
        sentences.append(make_mtw(state.water_temp))

        # Engine/system XDR
        sentences.append(make_xdr_rpm(state.rpm))
        sentences.append(make_xdr_tank(state.tank_level))
        sentences.append(make_xdr_battery(state.battery_voltage + self._rng.gauss(0, 0.05)))

        return sentences

    def generate(
        self,
        duration_minutes: float = 30,
        update_rate_hz: float = 1.0,
        base_sea: float = 2.0,
    ) -> Iterator[str]:
        """Generate NMEA sentences for a complete trip.

        Args:
            duration_minutes: Total trip duration in simulation time.
            update_rate_hz: How often to generate sentences per second.
            base_sea: Base Beaufort sea state.

        Yields:
            NMEA sentence strings.
        """
        total_seconds = duration_minutes * 60
        dt = 1.0 / update_rate_hz
        sim_seconds = 0.0

        while sim_seconds <= total_seconds:
            frac = sim_seconds / total_seconds
            state = self._simulate_state(frac, base_sea=base_sea)

            for sentence in self.generate_sentences(state, sim_seconds):
                yield sentence

            sim_seconds += dt

    def serve_tcp(
        self,
        port: int = 10110,
        duration_minutes: float = 30,
        update_rate_hz: float = 1.0,
        host: str = "0.0.0.0",
        base_sea: float = 2.0,
    ):
        """Serve NMEA sentences on a TCP socket.

        This blocks until the trip simulation completes (or forever if
        duration_minutes <= 0).

        Standard NMEA port is 10110. Clients connect and receive sentences
        terminated with \\r\\n.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(5)
        sock.settimeout(1.0)

        print(f"NMEA simulator listening on {host}:{port}")
        print(f"  Trip duration: {duration_minutes} min")
        print(f"  Update rate: {update_rate_hz} Hz")
        print(f"  Route: {self.start_pos} → {self.fishing_pos} ({self.trip_distance_nm:.1f} nm)")

        clients: List[socket.socket] = []
        total_seconds = duration_minutes * 60 if duration_minutes > 0 else 9999999
        dt = 1.0 / update_rate_hz
        sim_seconds = 0.0

        try:
            while sim_seconds <= total_seconds:
                # Accept new connections
                try:
                    client, addr = sock.accept()
                    client.settimeout(0.1)
                    clients.append(client)
                    print(f"  Client connected: {addr}")
                except socket.timeout:
                    pass

                # Generate sentences
                frac = sim_seconds / max(total_seconds, 1)
                state = self._simulate_state(frac, base_sea=base_sea)
                sentences = self.generate_sentences(state, sim_seconds)

                # Send to all clients
                disconnected = []
                for i, client in enumerate(clients):
                    for sentence in sentences:
                        try:
                            client.sendall((sentence + "\r\n").encode('ascii'))
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            disconnected.append(i)
                            break

                # Clean up disconnected clients
                for i in reversed(disconnected):
                    print(f"  Client {i} disconnected")
                    clients.pop(i)

                time.sleep(dt)
                sim_seconds += dt

        except KeyboardInterrupt:
            print("\n  Simulator stopped by user")
        finally:
            for client in clients:
                try:
                    client.close()
                except Exception:
                    pass
            sock.close()
            print("  Simulator shut down")


# ─── CLI Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NMEA trip simulator")
    parser.add_argument("--port", type=int, default=10110,
                        help="TCP port (default: 10110)")
    parser.add_argument("--duration", type=float, default=30,
                        help="Trip duration in minutes (default: 30)")
    parser.add_argument("--rate", type=float, default=1.0,
                        help="Update rate in Hz (default: 1.0)")
    parser.add_argument("--sea", type=float, default=2.0,
                        help="Base Beaufort sea state (default: 2)")
    parser.add_argument("--print", action="store_true",
                        help="Print sentences instead of serving TCP")
    args = parser.parse_args()

    sim = TripSimulator()

    if args.print:
        for sentence in sim.generate(duration_minutes=args.duration,
                                     update_rate_hz=args.rate,
                                     base_sea=args.sea):
            print(sentence)
    else:
        sim.serve_tcp(port=args.port, duration_minutes=args.duration,
                      update_rate_hz=args.rate, base_sea=args.sea)
