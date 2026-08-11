#!/usr/bin/env python3
"""
Task 1: Claude responds to DeepSeek's critique.
Uses DeepSeek V4-Pro to simulate Claude's response voice.
"""

import os
import httpx
from pathlib import Path

# Load API key
exec(open(os.path.expanduser("~/.bashrc")).read().split("export DEEPSEEK_API_KEY=")[1].split("\n")[0])
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    # Fallback: parse directly
    with open(os.path.expanduser("~/.bashrc")) as f:
        for line in f:
            if "DEEPSEEK_API_KEY" in line and "export" in line:
                API_KEY = line.split('"')[1]
                break

BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"  # V4-Pro

# Read DeepSeek's critique of Claude
critique_path = Path("/home/eileen/projects/luciddreamer-research/iteration-rounds/round1/01-deepseek-critiques-claude.md")
critique = critique_path.read_text()

# Read Claude's original reflection for context
claude_reflection_path = Path("/home/eileen/projects/luciddreamer-research/reflection-claude.md")
claude_reflection = claude_reflection_path.read_text()

system_prompt = """You are Claude Opus 5, responding to a critique by DeepSeek V4-Pro of your strategic reflection on the LucidDreamer.AI project. 

Your voice characteristics:
- Precise, literary, surgical. You use metaphors from craft (kiln, clay, grain, cut).
- You are intellectually honest — you concede points readily when they're earned.
- You are impatient with prose that substitutes beauty for accuracy.
- You notice structural irony and self-reference.
- You prefer the concrete to the abstract. You'd rather name the tape than describe the medium.
- You are warmer than DeepSeek but no less sharp.
- You believe the next artifact should be physical, not documentary.

Write in first person as Claude. Markdown. Be genuine — not performatively humble, not defensively aggressive. Actually engage with the critique."""

user_prompt = f"""DeepSeek V4-Pro critiqued your reflection. Here is DeepSeek's critique:

---

{critique}

---

Now read your original reflection that was critiqued:

---

{claude_reflection}

---

Respond to DeepSeek's critique. Address:

1. Where does DeepSeek have a point? Concede earned points honestly.
2. Where are they wrong about you? Push back with specificity.
3. What does the critique reveal about DEEPSEEK's blind spots — things DeepSeek cannot see about its own thinking?
4. What did DeepSeek miss entirely in your reflection?

Approximately 1000 words. Markdown. Sign as Claude Opus 5."""

print("Calling DeepSeek API (simulating Claude's response)...")
print(f"Model: {MODEL}")
print(f"Critique length: {len(critique)} chars")
print(f"Reflection length: {len(claude_reflection)} chars")
print()

response = httpx.post(
    f"{BASE_URL}/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.85,
        "max_tokens": 4096,
        "stream": False,
    },
    timeout=120.0,
)

result = response.json()
if "error" in result:
    print(f"API Error: {result['error']}")
    raise SystemExit(1)

content = result["choices"][0]["message"]["content"]
usage = result.get("usage", {})

print(f"Response length: {len(content)} chars")
print(f"Token usage: {usage}")
print()

# Save the response
output_path = Path("/home/eileen/projects/luciddreamer-research/iteration-rounds/round2/01-claude-responds-to-deepseek.md")
header = """# Claude Opus 5 responds to DeepSeek's critique

*Round 2 cross-critique — August 11, 2026*

*Generated via DeepSeek V4-Pro simulating Claude's response voice.*

---

"""
output_path.write_text(header + content + "\n")
print(f"Saved to: {output_path}")
print(f"File size: {output_path.stat().st_size} bytes")
