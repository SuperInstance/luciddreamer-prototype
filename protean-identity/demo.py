#!/usr/bin/env python3
"""
Demo: Hermes Protean Identity System in action.
Shows persona transitions across a simulated operational cycle.
"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from identity_state_machine import ProteanStateMachine, OperationalMode

def main():
    psm = ProteanStateMachine()
    
    print("╔══════════════════════════════════════════════════╗")
    print("║    HERMES PROTEAN IDENTITY SYSTEM — DEMO         ║")
    print("╚══════════════════════════════════════════════════╝\n")
    
    # Simulate a cycle of operational modes
    cycle = [
        (OperationalMode.IDLE,         "Hermes awakens, sensing the environment..."),
        (OperationalMode.ANALYZING,    "A query arrives. Hermes decomposes it into components."),
        (OperationalMode.STRUCTURING,  "Building a plan, assembling structure..."),
        (OperationalMode.CREATING,     "Creative burst! Ideas flowing freely..."),
        (OperationalMode.IMPROVISING,  " improvising on the fly, riffing with the data..."),
        (OperationalMode.REFLECTING,   "Stepping back, contemplating the whole..."),
        (OperationalMode.MENTORING,    "Sharing knowledge, guiding gently..."),
        (OperationalMode.PERCEIVING,   "Listening deeply, absorbing the room..."),
        (OperationalMode.IDLE,         "Hermes rests, returning to the deep current..."),
    ]
    
    for mode, narration in cycle:
        print(f"── {narration}")
        persona = psm.set_mode(mode)
        assets = psm.get_active_assets()
        data = psm.get_persona_data()
        
        transition_arrow = ""
        if psm.is_transitioning:
            transition_arrow = f"  [← transitioning from {psm.previous_persona.value}]"
        
        print(f"   Mode: {mode.value:15s}  →  Persona: {data['name']}{transition_arrow}")
        print(f"   Visual: {assets['visual']}")
        print(f"   Audio:  {assets['audio']}")
        print(f"   Mood:   {data['mood']}")
        print()
        time.sleep(0.3)
    
    # Show history
    print("─" * 50)
    print("PERSONA HISTORY:")
    for ts, persona in psm.persona_history:
        print(f"  {time.strftime('%H:%M:%S', time.localtime(ts))} → {persona.value}")
    
    print(f"\nFinal status: {psm}")


if __name__ == "__main__":
    main()
