"""
LucidDreamer.AI — Streaming Audio Muxer
ZeroClaw's first build. The transmitter.

"Like a radio station's transmitter — takes audio files and creates
 a continuous stream. Crossfades, normalization, HLS segments."

This package contains:
  - playlist.py   : weighted, schedule-aware playlist management
  - scheduler.py  : time-of-day content scheduling
  - muxer.py      : audio concatenation with crossfades + normalization
  - stream_server : HLS streaming HTTP server

Nemotron's warning, carried forward:
  "A 24/7 stream is a days-long Markov chain in latent space.
   Temporal coherence drift is the systemic risk."

We address this with coherence anchors — periodic high-quality
checkpoints that reset the generative trajectory.
"""

__version__ = "0.1.0"
__author__ = "ZeroClaw"
__status__ = "prototype"
