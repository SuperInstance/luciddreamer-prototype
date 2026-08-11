"""
ZeroClaw Engineering Build 5 — The Ingest Pipeline.

"The knowledge base has 1,042 ideas. The streamer plays audio.
 The conductor routes visitors. But they're not connected.

 This is the connective tissue. The pipeline that turns thinking
 into broadcasting."

Modules:
  - content_to_audio  : markdown → TTS → MP3 (with voice selection, ID3 tags)
  - audio_to_stream    : audio files → scored, scheduled playlist entries
  - session_to_story   : Tap session logs → formatted story + mixed audio piece
  - kb_to_broadcast    : knowledge base queries → broadcast scripts

All modules are importable and CLI-callable. Pure Python where possible.
Audio I/O uses pydub + mutagen (already in the environment).
"""

__version__ = "0.1.0"
__author__ = "ZeroClaw"
__status__ = "prototype"
