# NMEA → SWMIDI Bridge

**The thing that makes the boat a robot. Not metaphor. Measurement.**

Connects real NMEA 0183 vessel instruments to the SWMIDI-8 wire format,
the sonic shape engine, the conductor, and the agent fleet.

---

## What it does

```
                    ┌──────────────┐
  NMEA 0183 ──────▶ │  nmea_parser │ ──▶ parsed sentences
  (serial/TCP/sim)  └──────────────┘
                                              ┌────────────────┐
                    ┌──────────────┐          │ swmidi_encoder │ ──▶ 8-byte events
                    │ vessel_state │ ◀──────▶ │                │
                    └──────────────┘          └────────────────┘
                         │  │  │                      │
           ┌─────────────┘  │  └────────────┐         │
           ▼                ▼               ▼         ▼
    Sonic Shape      Conductor       Knowledge Base   Dashboard
    (music)          (agent ctx)     (JSONL log)      (WebSocket)
```

Each NMEA reading from the boat's instruments becomes an 8-byte SWMIDI event
on the shared beat clock. The vessel becomes a musical instrument. Agents
know what the boat is doing. Every reading is stored.

## SWMIDI-8 Event Format

```
Byte 0: Status     — event type (GPS=0x01, DEPTH=0x02, HEADING=0x03, ...)
Byte 1: Pitch      — normalized value (0-255)
Byte 2: Velocity   — confidence/quality (0-255)
Byte 3: ErrorMask  — 8-bit friction bitfield (0x00 = flow)
Byte 4: Tick       — beat clock position (96 PPQ)
Byte 5: Reserved   — sub-type
Byte 6: Data MSB   — extended data high byte
Byte 7: Data LSB   — extended data low byte
```

ErrorMask bitfield mirrors slackwater-rust:
```
bit 0: SPATIAL     bit 4: RESOURCE
bit 1: TEMPORAL    bit 5: TOPOLOGY
bit 2: SEMANTIC    bit 6: AUTHORITY
bit 3: SAFETY      bit 7: CONSISTENCY
```

## Modules

| File | Description |
|------|-------------|
| `nmea_parser.py` | Parses GPGGA, GPRMC, SDDBT, SDDPT, HDT, HDM, HDG, MTW, VHW, XDR |
| `swmidi_encoder.py` | Encodes vessel state as SWMIDI-8 events |
| `vessel_state.py` | Maintains vessel state, computes derived modes + musical params |
| `bridge.py` | Main bridge process — NMEA in → SWMIDI out |
| `simulator.py` | Simulates a full fishing trip (harbor → transit → fish → return) |
| `dashboard.html` | Real-time visualization (WebSocket) |
| `tests/` | 51 tests covering all modules |

## Quick Start

```bash
# Run with the built-in simulator (prints to console):
python3 bridge.py --simulate

# Connect to a TCP NMEA source:
python3 bridge.py --tcp localhost:10110

# Connect to a serial port:
python3 bridge.py --serial /dev/ttyUSB0 --baud 4800

# With JSONL logging:
python3 bridge.py --simulate --log /var/log/nmea-bridge.jsonl

# Run just the simulator on standard NMEA port:
python3 simulator.py --port 10110 --duration 30

# Run tests:
python3 -m pytest tests/ -v
```

## Vessel Modes (auto-detected)

| Mode | Condition | Mood |
|------|-----------|------|
| DOCKED | speed < 0.5 kt, depth < 5 fm | restful |
| DEPARTING | speed 0.5-4 kt, heading out | optimistic |
| TRANSIT | speed > 4 kt, depth > 20 fm | steadfast |
| FISHING | speed < 2 kt, depth > 5 fm, depth changing | focused |
| HAULING | gear up | — |
| RETURNING | speed 0.5-4, heading to port | weary |
| ANCHORED | speed < 0.5, depth > 5 fm, no engine | patient |

## Integration Points

- **Acoustic Probe**: `VesselStateManager.musical_parameters()` returns the same
  `MusicalParameters` structure used by the acoustic-probe's `VesselInstrument`
- **Sonic Shape Engine**: Musical mood, tempo, and intensity feed the confidence-to-music pipeline
- **Conductor**: `context_for_agents()` returns a dict for agent system prompts
- **Knowledge Base**: JSONL log provides searchable event history
- **Dashboard**: WebSocket broadcast for real-time monitoring
