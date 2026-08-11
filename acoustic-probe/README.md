# The Acoustic Probe — FV Eileen Telemetry as Music

The ship itself becomes a lead instrument. Engine RPM is bass. Depth is harmony. Sea state is rhythm. Heading is position in space. Speed is tempo.

When Casey is fishing, the music knows.

## Modules

| Module | Purpose |
|--------|---------|
| `telemetry_to_midi.py` | Maps physical vessel data → MIDI patterns |
| `vessel_instrument.py` | The FV Eileen as a playable virtual instrument |
| `telemetry_simulator.py` | Generates realistic vessel telemetry for testing |
| `ship_to_song.py` | Combines vessel state with MMX music generation |

## Mapping Summary

| Telemetry | Musical Parameter |
|-----------|-------------------|
| Engine RPM (0-3000) | Bass fundamental: 55Hz (idle) → 220Hz (full) |
| Depth/Fathoms (0-100) | Harmonic complexity: root → 7ths → chromatic fog |
| Sea State (0-9 Beaufort) | Rhythmic jitter: steady 4/4 → syncopated polyrhythms |
| Heading (0-360°) | Stereo pan position |
| Speed (knots) | Tempo scaling |

## Usage

```bash
# Run the simulator to see telemetry → MIDI mapping
python telemetry_simulator.py

# Generate a song from current vessel state
python ship_to_song.py

# Use as a library
from vessel_instrument import VesselInstrument
from telemetry_to_midi import TelemetryToMIDI

vessel = VesselInstrument()
vessel.update(rpm=1800, depth=40, sea_state=3, heading=180, speed=7.5)
midi = TelemetryToMIDI()
pattern = midi.generate_pattern(vessel.state)
```
