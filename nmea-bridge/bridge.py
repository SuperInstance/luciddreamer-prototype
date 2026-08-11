"""
bridge.py — The NMEA→SWMIDI bridge: the main process.

This is THE BRIDGE. It connects Casey's real fishing vessel to the agent
fleet. When this runs, the boat IS a robot. Not metaphor. Measurement.

Listens for NMEA input from:
    - Serial port (USB chartplotter / NMEA multiplexer)
    - TCP socket (networked NMEA, e.g. from a multiplexer or the simulator)
    - Simulated input (for testing)

Parses NMEA → updates VesselState → encodes as SWMIDI-8 events → outputs to:
    a) The sonic shape engine (vessel becomes a musical instrument)
    b) The conductor (agents know vessel state)
    c) The knowledge base (vessel events stored as context)
    d) A WebSocket for the dashboard

Can run standalone as a daemon.

Usage:
    # From simulator (testing):
    python bridge.py --simulate

    # From TCP NMEA source:
    python bridge.py --tcp localhost:10110

    # From serial port:
    python bridge.py --serial /dev/ttyUSB0 --baud 4800

    # With WebSocket dashboard:
    python bridge.py --simulate --ws-port 8765
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import socket
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nmea_parser import NMEAParser, ParseResult, SentenceType
from swmidi_encoder import SWMIDIEncoder, SWMIDIEvent, EventType, ErrorMask, compute_error_mask
from vessel_state import VesselStateManager, VesselMode

logger = logging.getLogger("nmea_bridge")


# ─── Output Handlers ────────────────────────────────────────────────────────

class OutputHandler:
    """Base class for SWMIDI output handlers."""

    def on_events(self, events: List[SWMIDIEvent], state_manager: VesselStateManager):
        """Called when new SWMIDI events are generated."""
        raise NotImplementedError

    def on_state_change(self, state_manager: VesselStateManager):
        """Called when vessel state changes."""
        raise NotImplementedError

    def close(self):
        """Clean up resources."""
        pass


class ConsoleOutput(OutputHandler):
    """Prints events and state to console — useful for debugging."""

    def on_events(self, events: List[SWMIDIEvent], state_manager: VesselStateManager):
        for event in events:
            print(f"  SWMIDI: {event}")

    def on_state_change(self, state_manager: VesselStateManager):
        s = state_manager.state
        print(f"\n[Vessel] mode={s.mode.value}  "
              f"SOG={s.speed_over_ground or 0:.1f}kt  "
              f"HDG={s.heading or 0:.0f}°  "
              f"Depth={s.depth or 0:.1f}fm  "
              f"RPM={s.engine_rpm or 0:.0f}")


class JSONLLogOutput(OutputHandler):
    """Writes vessel state and SWMIDI events to a JSONL log file.

    This is the knowledge base feed — vessel events stored as context
    that agents can query later.
    """

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.log_path, 'a')

    def on_events(self, events: List[SWMIDIEvent], state_manager: VesselStateManager):
        for event in events:
            entry = {
                "timestamp": time.time(),
                "type": "swmidi_event",
                **event.to_dict(),
            }
            self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def on_state_change(self, state_manager: VesselStateManager):
        entry = {
            "timestamp": time.time(),
            "type": "vessel_state",
            **state_manager.context_for_agents(),
        }
        self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()


class MusicalStateOutput(OutputHandler):
    """Converts vessel state to musical parameters for the sonic shape engine.

    This output feeds the acoustic probe's VesselInstrument or the sonic
    shape engine's live generator. It produces the same MusicalParameters
    structure that those systems expect.
    """

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.last_params = None

    def on_events(self, events: List[SWMIDIEvent], state_manager: VesselStateManager):
        pass  # Events are not needed here — we read state directly

    def on_state_change(self, state_manager: VesselStateManager):
        params = state_manager.musical_parameters()
        if params.to_dict() != (self.last_params.to_dict() if self.last_params else None):
            self.last_params = params
            if self.callback:
                self.callback(params, state_manager.state)
            logger.debug(f"Musical params: {params.mood} {params.tempo_bpm:.0f}BPM "
                        f"intensity={params.intensity}")


class ConductorOutput(OutputHandler):
    """Feeds vessel context to the conductor so agents know what the boat is doing.

    Produces a context dict that can be injected into agent system prompts
    or shared state.
    """

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self._last_mode = None

    def on_events(self, events: List[SWMIDIEvent], state_manager: VesselStateManager):
        pass

    def on_state_change(self, state_manager: VesselStateManager):
        mode = state_manager.state.mode
        if mode != self._last_mode:
            self._last_mode = mode
            context = state_manager.context_for_agents()
            logger.info(f"Vessel mode transition: {context['mode']}")
            if self.callback:
                self.callback(context)


class WebSocketOutput(OutputHandler):
    """Broadcasts vessel state and SWMIDI events over WebSocket for the dashboard.

    Uses a simple asyncio queue — the bridge process pumps events here and
    the WebSocket server in bridge_async.py serves them to connected dashboards.
    """

    def __init__(self):
        self.subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self.subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.subscribers:
            self.subscribers.remove(q)

    def on_events(self, events: List[SWMIDIEvent], state_manager: VesselStateManager):
        msg = {
            "type": "swmidi_events",
            "timestamp": time.time(),
            "events": [e.to_dict() for e in events],
        }
        self._broadcast(msg)

    def on_state_change(self, state_manager: VesselStateManager):
        msg = {
            "type": "vessel_state",
            "timestamp": time.time(),
            **state_manager.context_for_agents(),
        }
        self._broadcast(msg)

    def _broadcast(self, msg: dict):
        for q in self.subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass  # Drop if client is slow


# ─── NMEA Input Sources ─────────────────────────────────────────────────────

class NMEAInputSource:
    """Base class for NMEA input sources."""

    def read_sentence(self, timeout: float = 1.0) -> Optional[str]:
        """Read one NMEA sentence. Returns None on timeout."""
        raise NotImplementedError

    def close(self):
        pass


class TCPInputSource(NMEAInputSource):
    """Reads NMEA sentences from a TCP socket."""

    def __init__(self, host: str, port: int = 10110):
        self.host = host
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._buffer = ""

    def _connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(5.0)
        self._sock.connect((self.host, self.port))
        logger.info(f"Connected to NMEA TCP source: {self.host}:{self.port}")

    def read_sentence(self, timeout: float = 1.0) -> Optional[str]:
        if self._sock is None:
            try:
                self._connect()
            except (socket.error, ConnectionRefusedError) as e:
                logger.warning(f"Connection failed: {e}")
                return None

        self._sock.settimeout(timeout)
        try:
            while "\r\n" not in self._buffer:
                data = self._sock.recv(1024).decode('ascii', errors='replace')
                if not data:
                    logger.warning("NMEA source disconnected")
                    self._sock = None
                    return None
                self._buffer += data

            line, self._buffer = self._buffer.split("\r\n", 1)
            return line.strip()
        except socket.timeout:
            return None
        except socket.error as e:
            logger.warning(f"Socket error: {e}")
            self._sock = None
            return None

    def close(self):
        if self._sock:
            self._sock.close()
            self._sock = None


class SerialInputSource(NMEAInputSource):
    """Reads NMEA sentences from a serial port.

    Requires pyserial. Install with: pip install pyserial
    """

    def __init__(self, port: str, baud: int = 4800):
        self.port = port
        self.baud = baud
        self._serial = None
        self._buffer = ""

    def _connect(self):
        try:
            import serial
        except ImportError:
            raise ImportError("pyserial required for serial input: pip install pyserial")
        self._serial = serial.Serial(self.port, self.baud, timeout=1.0)
        logger.info(f"Connected to serial NMEA: {self.port}@{self.baud}")

    def read_sentence(self, timeout: float = 1.0) -> Optional[str]:
        if self._serial is None:
            self._connect()

        try:
            while "\r\n" not in self._buffer:
                data = self._serial.read(1024).decode('ascii', errors='replace')
                if not data:
                    return None
                self._buffer += data

            line, self._buffer = self._buffer.split("\r\n", 1)
            return line.strip()
        except Exception as e:
            logger.warning(f"Serial error: {e}")
            self._serial = None
            return None

    def close(self):
        if self._serial:
            self._serial.close()
            self._serial = None


class SimulatorInputSource(NMEAInputSource):
    """Reads NMEA sentences from the built-in trip simulator."""

    def __init__(self, duration_minutes: float = 0, base_sea: float = 2.0):
        from simulator import TripSimulator
        self.sim = TripSimulator()
        self._iterator = self.sim.generate(
            duration_minutes=duration_minutes or 999999,
            update_rate_hz=1.0,
            base_sea=base_sea,
        )
        self._last_time = time.time()

    def read_sentence(self, timeout: float = 1.0) -> Optional[str]:
        # Throttle to ~1 Hz to simulate real instrument
        elapsed = time.time() - self._last_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_time = time.time()
        try:
            return next(self._iterator)
        except StopIteration:
            return None


# ─── The Bridge ─────────────────────────────────────────────────────────────

class NMEABridge:
    """The NMEA→SWMIDI bridge.

    Connects an NMEA input source to SWMIDI output handlers. Runs a main
    loop that reads NMEA sentences, updates vessel state, and emits SWMIDI
    events.

    This is the thing that makes the boat a robot.
    """

    def __init__(
        self,
        input_source: Optional[NMEAInputSource] = None,
        outputs: Optional[List[OutputHandler]] = None,
        state_manager: Optional[VesselStateManager] = None,
    ):
        self.input_source = input_source
        self.outputs: List[OutputHandler] = outputs or []
        self.state_manager = state_manager or VesselStateManager()
        self.parser = NMEAParser()
        self.encoder = SWMIDIEncoder()
        self._running = False
        self._last_mode: Optional[VesselMode] = None

        # Data freshness tracking for error mask
        self._last_gps_time = 0.0
        self._last_depth_time = 0.0
        self._last_heading_time = 0.0

    def add_output(self, handler: OutputHandler):
        self.outputs.append(handler)

    def process_sentence(self, sentence: str) -> Optional[List[SWMIDIEvent]]:
        """Process a single NMEA sentence end-to-end.

        Returns the list of SWMIDI events generated, or None.
        """
        result = self.parser.parse(sentence)
        if result is None or not result.valid:
            return None

        # Update vessel state based on sentence type
        self._apply_parse_result(result)

        # Generate SWMIDI events from current state
        error_mask = self._compute_error_mask()
        events = self.encoder.encode_vessel_state(
            self.state_manager.state,
            error_mask=error_mask,
        )

        # Advance the beat clock
        self.encoder.advance_tick()

        # Notify output handlers
        for handler in self.outputs:
            try:
                handler.on_events(events, self.state_manager)
            except Exception as e:
                logger.error(f"Output handler error: {e}")

        # Check for mode change
        if self.state_manager.state.mode != self._last_mode:
            self._last_mode = self.state_manager.state.mode
            for handler in self.outputs:
                try:
                    handler.on_state_change(self.state_manager)
                except Exception as e:
                    logger.error(f"State change handler error: {e}")

        return events

    def _apply_parse_result(self, result: ParseResult):
        """Apply a parsed NMEA sentence to the vessel state."""
        d = result.data
        st = result.sentence_type

        if st == SentenceType.GPGGA:
            if d.get("latitude") is not None:
                self.state_manager.update_position(
                    d["latitude"], d["longitude"], d.get("fix_quality", 0))
                self._last_gps_time = time.time()

        elif st == SentenceType.GPRMC:
            if d.get("latitude") is not None:
                self.state_manager.update_position(
                    d["latitude"], d["longitude"])
                self._last_gps_time = time.time()
            if d.get("speed_knots") is not None:
                self.state_manager.update_speed(sog=d["speed_knots"])
            if d.get("course_degrees") is not None:
                self.state_manager.update_course(d["course_degrees"])

        elif st == SentenceType.SDDBT:
            depth = d.get("depth_fathoms")
            if depth is None:
                depth_m = d.get("depth_meters")
                if depth_m is not None:
                    depth = depth_m / 1.8288
            if depth is not None:
                self.state_manager.update_depth(depth_fathoms=depth)
                self._last_depth_time = time.time()

        elif st == SentenceType.SDDPT:
            depth_m = d.get("depth_meters")
            if depth_m is not None:
                self.state_manager.update_depth(depth_meters=depth_m)
                self._last_depth_time = time.time()

        elif st == SentenceType.HDT:
            if d.get("heading") is not None:
                self.state_manager.update_heading(d["heading"])
                self._last_heading_time = time.time()

        elif st == SentenceType.HDM:
            if d.get("heading") is not None:
                self.state_manager.update_heading(d["heading"], magnetic=True)
                self._last_heading_time = time.time()

        elif st == SentenceType.HDG:
            if d.get("heading_true") is not None:
                self.state_manager.update_heading(d["heading_true"])
                self._last_heading_time = time.time()

        elif st == SentenceType.VHW:
            if d.get("heading_true") is not None:
                self.state_manager.update_heading(d["heading_true"])
            if d.get("speed_knots") is not None:
                self.state_manager.update_speed(stw=d["speed_knots"])

        elif st == SentenceType.MTW:
            if d.get("water_temperature") is not None:
                self.state_manager.update_environment(
                    water_temp=d["water_temperature"])

        elif st == SentenceType.XDR:
            rpm = d.get("engine_rpm")
            tank = d.get("tank_level")
            volt = d.get("battery_voltage")
            if rpm is not None or tank is not None or volt is not None:
                self.state_manager.update_engine(rpm=rpm, tank_level=tank,
                                                 battery_voltage=volt)

    def _compute_error_mask(self) -> int:
        """Compute error mask from data freshness and sensor health."""
        now = time.time()
        mask = 0

        # Check data freshness (TEMPORAL if stale)
        if self._last_gps_time and (now - self._last_gps_time) > 5.0:
            mask |= ErrorMask.TEMPORAL
        if self._last_depth_time and (now - self._last_depth_time) > 5.0:
            mask |= ErrorMask.TEMPORAL

        # GPS fix quality
        if self.state_manager.state.fix_quality == 0:
            mask |= ErrorMask.SPATIAL

        # Low fuel
        if self.state_manager.state.tank_level is not None:
            if self.state_manager.state.tank_level < 25:
                mask |= ErrorMask.RESOURCE

        return mask

    def run(self):
        """Main bridge loop. Blocks until input source exhausts or error."""
        if self.input_source is None:
            raise RuntimeError("No input source configured")

        self._running = True
        logger.info("NMEA bridge started")

        try:
            while self._running:
                sentence = self.input_source.read_sentence(timeout=2.0)
                if sentence is None:
                    if not self._running:
                        break
                    continue

                logger.debug(f"NMEA: {sentence}")
                self.process_sentence(sentence)

        except KeyboardInterrupt:
            logger.info("Bridge interrupted by user")
        except Exception as e:
            logger.error(f"Bridge error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop the bridge."""
        self._running = False
        if self.input_source:
            self.input_source.close()
        for handler in self.outputs:
            handler.close()
        logger.info("NMEA bridge stopped")


# ─── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="NMEA→SWMIDI Bridge — the thing that makes the boat a robot")
    parser.add_argument("--simulate", action="store_true",
                        help="Use built-in trip simulator")
    parser.add_argument("--tcp", metavar="HOST:PORT",
                        help="Read NMEA from TCP source (e.g. localhost:10110)")
    parser.add_argument("--serial", metavar="DEVICE",
                        help="Read NMEA from serial port (e.g. /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=4800,
                        help="Serial baud rate (default: 4800)")
    parser.add_argument("--log", metavar="PATH",
                        help="Write JSONL event log to this path")
    parser.add_argument("--ws-port", type=int, default=8765,
                        help="WebSocket port for dashboard (default: 8765)")
    parser.add_argument("--no-ws", action="store_true",
                        help="Disable WebSocket server")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose logging")
    args = parser.parse_args()

    # Set up logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Build input source
    input_source: Optional[NMEAInputSource] = None
    if args.simulate:
        input_source = SimulatorInputSource(duration_minutes=0)
    elif args.tcp:
        host, _, port = args.tcp.rpartition(':')
        input_source = TCPInputSource(host or "localhost", int(port) if port else 10110)
    elif args.serial:
        input_source = SerialInputSource(args.serial, args.baud)
    else:
        print("No input source specified. Use --simulate, --tcp, or --serial")
        sys.exit(1)

    # Build output handlers
    outputs: List[OutputHandler] = [ConsoleOutput()]

    if args.log:
        outputs.append(JSONLLogOutput(args.log))

    # Musical state output (for sonic shape engine)
    def on_musical_change(params, state):
        logger.info(f"🎵 {params.mood} | {params.tempo_bpm:.0f} BPM | "
                    f"intensity={params.intensity} | {params.harmony_label}")

    outputs.append(MusicalStateOutput(callback=on_musical_change))

    # Conductor output (mode transitions)
    def on_mode_change(context):
        logger.info(f"⛴️  Vessel: {context['mode']} | "
                    f"pos={context.get('position')}")

    outputs.append(ConductorOutput(callback=on_mode_change))

    # Build and run bridge
    bridge = NMEABridge(
        input_source=input_source,
        outputs=outputs,
    )

    # Graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down...")
        bridge.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("╔════════════════════════════════════════════════╗")
    print("║     NMEA → SWMIDI BRIDGE — FV Eileen           ║")
    print("║     The boat is a robot. Not metaphor.         ║")
    print("╚════════════════════════════════════════════════╝")
    print()

    bridge.run()


if __name__ == "__main__":
    main()
