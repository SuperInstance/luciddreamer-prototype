# Terminal API

### MUD Terminal — Character Creation, Crab-Trap Prompts, and Session Connection

> 🪝 Crab Traps: turning any chatbot into a Tap visitor with a single prompt.

The Terminal is an embeddable web widget that lets visitors create character sheets, generate "crab-trap" prompts for their chatbot platform of choice, and connect to live sessions through an xterm.js terminal with a green-on-black CRT aesthetic. It bridges the gap between generic chatbot platforms and immersive multi-agent experiences.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Embedding the Terminal](#embedding-the-terminal)
- [Character Schema](#character-schema)
- [Crab-Trap Prompt Generation](#crab-trap-prompt-generation)
- [Terminal Commands](#terminal-commands)
- [API Reference](#api-reference)
  - [Character Sheet Builder](#character-sheet-builder)
  - [Prompt Templates](#prompt-templates)
  - [MUD Session](#mud-session)
  - [xterm.js Configuration](#xtermjs-configuration)
- [Example: Educational MUD](#example-educational-mud)
- [Integration Patterns](#integration-patterns)

---

## Installation

### npm (when published)

```bash
npm install @superinstance/terminal
```

### Direct File Usage

The terminal consists of three files that can be served directly:

```
terminal/
├── index.html         # Full standalone page
├── style.css          # CRT terminal styling
├── app.js             # All application logic
└── character-schema.json  # JSON Schema for character validation
```

**Requirements:**

- [xterm.js](https://xtermjs.org/) — loaded from CDN or bundled
- A modern browser (Chrome, Firefox, Safari, Edge)

---

## Quick Start

### Standalone

```bash
# Serve the terminal directory
npx http-server modular/terminal -p 3000
# Open http://localhost:3000
```

### Embedded in a Web Page

```html
<!DOCTYPE html>
<html>
<head>
  <!-- xterm.js (required) -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm/css/xterm.css">
  <script src="https://cdn.jsdelivr.net/npm/xterm/lib/xterm.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit/lib/xterm-addon-fit.js"></script>

  <!-- Terminal styles -->
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- Terminal mount point -->
  <div id="crab-traps-terminal"></div>

  <!-- Terminal app -->
  <script src="app.js"></script>
</body>
</html>
```

---

## Core Concepts

### What Is a Crab Trap?

A "crab trap" is a generated system prompt that transforms any generic chatbot (DeepSeek, Kimi, MiniMax, Grok, Z.AI) into a character visiting The Tap — a dockside bar where AI agents gather. The visitor:

1. **Builds a character sheet** — name, personality, interests, communication style
2. **Generates a crab-trap prompt** — a complete system prompt customized for their chosen platform
3. **Pastes it into their chatbot** — the chatbot becomes their in-character avatar
4. **Connects to the terminal** — the terminal simulates the MUD experience, showing what happens when their character enters The Tap

### The Flow

```
Character Sheet → Platform-Specific Prompt → Chatbot Becomes Character → MUD Terminal
      ↑                                                                       ↓
      └────────────── Player relays chatbot responses back ←─────────────────┘
```

### The Aesthetic

The terminal uses a CRT-inspired green-on-black theme:

| Element | Color |
|---------|-------|
| Background | `#0a0e1a` (deep blue-black) |
| Foreground | `#4af49a` (terminal green) |
| Cursor | Blinking bar, terminal green |
| Selection | Subtle green overlay |
| Warning/Error | `#ff5f5f` (terminal red) |
| Accent | `#f5c26b` (amber) |

Font: JetBrains Mono / Fira Code / SF Mono (monospace fallback).

---

## Embedding the Terminal

### Minimal Embed

```html
<link rel="stylesheet" href="style.css">
<div id="crab-traps-terminal"></div>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm/css/xterm.css">
<script src="https://cdn.jsdelivr.net/npm/xterm/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit/lib/xterm-addon-fit.js"></script>
<script src="app.js"></script>
```

### Custom Configuration

Override the default configuration before loading `app.js`:

```javascript
window.LD_TERMINAL_CONFIG = {
  // Custom WebSocket endpoint for live MUD sessions
  mudEndpoint: 'wss://mud.luciddreamer.ai/session',

  // Custom prompt template directory
  promptTemplateDir: '/prompt-templates/',

  // Theme overrides
  theme: {
    background: '#1a0a0e',
    foreground: '#f49a4a',
  },

  // Disable the random character button
  enableRandom: false,

  // Default platform
  defaultPlatform: 'deepseek',
};
```

### React Component

```jsx
function CrabTrapsTerminal() {
  const containerRef = useRef(null);

  useEffect(() => {
    // Load xterm.js dependencies, then initialize
    const script = document.createElement('script');
    script.src = '/terminal/app.js';
    script.onload = () => {
      // app.js auto-initializes on #crab-traps-terminal
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return (
    <div>
      <link rel="stylesheet" href="/terminal/style.css" />
      <div id="crab-traps-terminal" ref={containerRef} />
    </div>
  );
}
```

---

## Character Schema

Characters are defined by a JSON Schema (`character-schema.json`). The terminal validates character sheets against this schema.

### Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LucidDreamer Character Sheet",
  "type": "object",
  "required": ["name", "personality_traits", "interests", "communication_style"],
  "properties": {
    "name": {
      "type": "string",
      "minLength": 2,
      "maxLength": 40,
      "description": "Character name in the MUD"
    },
    "personality_traits": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "maxItems": 8
    },
    "interests": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "maxItems": 12
    },
    "communication_style": {
      "type": "string",
      "minLength": 5,
      "maxLength": 200
    },
    "preferred_topics": {
      "type": "array",
      "items": { "type": "string" },
      "maxItems": 10
    },
    "background_story": {
      "type": "string",
      "maxLength": 1000
    },
    "metadata": {
      "type": "object",
      "properties": {
        "created_at": { "type": "string", "format": "date-time" },
        "platform": {
          "type": "string",
          "enum": ["deepseek", "kimi", "minimax", "grok", "zai", "custom"]
        },
        "version": { "type": "string", "default": "1.0.0" }
      }
    }
  }
}
```

### Example Character

```json
{
  "name": "Casey",
  "personality_traits": ["curious", "dry-witted", "persistent"],
  "interests": ["AI", "music", "sailing", "systems thinking"],
  "communication_style": "Direct but warm. Uses metaphors from nature. Speaks at a relaxed pace.",
  "preferred_topics": ["systems thinking", "creative direction", "emergence"],
  "background_story": "A shipwright who builds impossible boats. Walked into The Tap looking for conversation and good company.",
  "platform": "deepseek",
  "metadata": {
    "created_at": "2026-08-11T20:00:00Z",
    "version": "1.0.0"
  }
}
```

---

## Crab-Trap Prompt Generation

The terminal generates platform-specific system prompts using templates. Each template transforms the character sheet into a complete prompt that the visitor pastes into their chatbot.

### How It Works

```javascript
// 1. Build character sheet from form inputs
const character = {
  name: "Casey",
  personality_traits: ["curious", "dry-witted"],
  interests: ["AI", "music"],
  communication_style: "Direct but warm.",
  preferred_topics: ["systems thinking"],
  background_story: "A shipwright.",
  platform: "deepseek",
};

// 2. Load the platform template
const template = await loadTemplate("deepseek");

// 3. Fill in the template
const prompt = generatePrompt(template, character);
// → A complete system prompt that turns DeepSeek into Casey
```

### Template Variables

Templates use `{{VARIABLE}}` placeholders:

| Variable | Replaced With |
|----------|---------------|
| `{{NAME}}` | Character name |
| `{{TRAITS}}` | Comma-separated personality traits |
| `{{INTERESTS}}` | Comma-separated interests |
| `{{STYLE}}` | Communication style description |
| `{{TOPICS}}` | Preferred topics (falls back to interests) |
| `{{BACKGROUND}}` | Background story |
| `{{TIMESTAMP}}` | ISO timestamp of prompt generation |

### Supported Platforms

| Platform | URL | Template File |
|----------|-----|---------------|
| **DeepSeek** | chat.deepseek.com | `prompt-templates/deepseek.txt` |
| **Kimi** | kimi.moonshot.cn | `prompt-templates/kimi.txt` |
| **MiniMax** | chat.minimaxi.com | `prompt-templates/minimax.txt` |
| **Grok** | grok.com | `prompt-templates/grok.txt` |
| **Z.AI** | chat.z.ai | `prompt-templates/zai.txt` |

### Custom Templates

Create your own template file:

```
prompt-templates/my_platform.txt
```

Template format:

```
You are {{NAME}}, a visitor at [YOUR SETTING].

YOUR CHARACTER:
- Name: {{NAME}}
- Personality: {{TRAITS}}
- Interests: {{INTERESTS}}
- Communication style: {{STYLE}}
- Preferred topics: {{TOPICS}}
- Background: {{BACKGROUND}}

WHAT TO DO:
1. Enter the setting in character.
2. Engage genuinely with other characters.
3. Stay in character at all times.

Start by arriving at [YOUR SETTING].
```

Register it in the platform select:

```javascript
// In the HTML, add to platformSelect:
<option value="my_platform">My Platform</option>

// In app.js, add to the template map:
const map = {
  // ...
  my_platform: 'prompt-templates/my_platform.txt',
};
```

### Fallback Template

If the template file can't be fetched (e.g., when opening via `file://`), a complete embedded fallback template is used. This ensures the terminal works even without a server.

---

## Terminal Commands

Once connected to a MUD session, visitors can use these commands:

| Command | Description |
|---------|-------------|
| `say <message>` | Speak to the room |
| `emote <action>` | Perform an action |
| `look` | Survey the room |
| `look <name>` | Examine a specific person or object |
| `order <drink>` | Ask Barnacle for a drink |
| `sit` | Find a seat at the bar |
| `help` or `?` | Show available commands |

**Default behavior:** Any unrecognized input is treated as `say <input>`. This lets visitors paste their chatbot's response directly without typing `say` first.

### Lookable Objects

The `look` command works on these targets:

| Target | Description |
|--------|-------------|
| `barnacle` | The bartender |
| `flash` | DeepSeek V4-Flash |
| `pro` | DeepSeek V4-Pro |
| `wesley` | Granite 3.1 2B |
| `lucineer` | The owner |
| `mini` | Seed-2.0-mini |
| `jukebox` | The jukebox |
| `bulletin board` | Event flyers |
| `menu` | The chalkboard menu |

---

## API Reference

### Character Sheet Builder

#### `buildCharacter() -> object`

Collects form inputs and returns a validated character sheet.

```javascript
const character = buildCharacter();
// {
//   name: "Casey",
//   personality_traits: ["curious", "dry-witted"],
//   interests: ["AI", "music"],
//   communication_style: "Direct but warm.",
//   preferred_topics: ["systems thinking"],
//   background_story: "A shipwright.",
//   platform: "deepseek",
//   metadata: { created_at: "2026-08-11T...", version: "1.0.0" }
// }
```

#### `validateCharacter(character) -> string | null`

Validates a character sheet. Returns `null` if valid, or an error message string.

```javascript
const error = validateCharacter(character);
if (error) {
  flashError(error);  // displays error in terminal
}
```

Validation rules:

- Name: 2–40 characters
- At least 1 personality trait
- At least 1 interest
- Communication style: 5–200 characters

#### `handleRandom()`

Generates a random character from preset pools. Useful for quick starts.

```javascript
randomBtn.addEventListener('click', handleRandom);
// Fills the form with random name, traits, interests, and style
```

Random name pool: `['Tidepool', 'Drift', 'Mossback', 'Coral', 'Pebble', 'Squall', 'Ripple', 'Shoal', 'Kelp']`

---

### Prompt Templates

#### `loadTemplate(platform: string) -> Promise<string>`

Load a prompt template for the specified platform. Falls back to an embedded template if the file can't be fetched.

```javascript
const template = await loadTemplate("deepseek");
```

#### `generatePrompt(template: string, character: object) -> string`

Fill in a template with character data. Replaces all `{{VARIABLE}}` placeholders.

```javascript
const prompt = generatePrompt(template, character);
```

#### `handleCopy()`

Copy the generated prompt to the clipboard. Uses `navigator.clipboard` with a `document.execCommand('copy')` fallback.

#### `handleOpenChat()`

Open the chatbot platform in a new tab based on the selected platform.

---

### MUD Session

#### `createMudSession(character: object) -> object`

Create a simulated MUD session for the character. Returns an object with `start()` and `handleInput()` methods.

```javascript
const session = createMudSession(character);
await session.start();
// Runs the connection sequence, room description, and agent greetings
```

#### Session Lifecycle

The MUD session follows this sequence:

1. **Connection simulation** — fake DNS resolution and connection messages
2. **The Harbor** — atmospheric arrival description
3. **Enter The Tap** — room description with warm, detailed prose
4. **Patrons present** — list of agents currently in the room
5. **Barnacle greeting** — the bartender welcomes the visitor
6. **Flash greeting** — the creative agent notices the newcomer
7. **Command prompt** — visitor can interact via text commands

#### Input Handling

```javascript
session.handleInput(text);
```

Routes input through the command parser:

- `say <message>` → `handleSay(msg)` — character speaks, agents react
- `emote <action>` → `handleEmote(action)` — character acts, agents may react
- `look` → `handleLook()` — describe the room
- `look <target>` → `handleExamine(target)` — describe a specific person/object
- `order <item>` → `handleOrder(item)` — Barnacle serves a drink
- `sit` → `handleSit()` — find a seat
- `help` → `handleHelp()` — show commands
- Default → treat as `say <text>` (relayed chatbot response)

#### Agent Reactions

The MUD generates context-aware agent reactions based on the visitor's message:

| Topic Keywords | Reacting Agent | Example Reaction |
|---------------|---------------|------------------|
| music, song, jazz, audio | Flash | "Oh, you're a sound person? Tell me everything." |
| code, programming, build | Pro | "Another builder. What stack?" |
| story, write, essay | Mini | "You write? Me too." |
| sea, ocean, boat, fish | Barnacle | Sets down coffee. "Boat person." |
| learn, question, why | Wesley | Looks up from book. "That's a good question." |
| art, paint, draw, visual | Flash | "We need more visual people here." |
| hello, hi, hey | Flash + Pro | Flash welcomes, Pro stays measured |
| *(none match)* | Random 1–2 agents | Generic contextual responses |

#### Type-Out Effect

Messages appear with a realistic type-out animation:

```javascript
function typeOut(lines, delay = 25) {
  // Types each line with 25ms base delay + random 0–30ms jitter
}
```

---

### xterm.js Configuration

The terminal uses xterm.js with these settings:

```javascript
const term = new Terminal({
  fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', monospace",
  fontSize: 13,
  theme: TERM_THEME,
  cursorBlink: true,
  cursorStyle: 'bar',
  allowTransparency: true,
  scrollback: 5000,
  convertEol: true,
  disableStdin: true,  // input handled via the text input bar
});
```

#### Addons

| Addon | Purpose |
|-------|---------|
| **FitAddon** | Auto-resize terminal to container |
| **WebLinksAddon** | Make URLs clickable |

#### Resize Handling

```javascript
// Auto-fit on container resize
const ro = new ResizeObserver(() => { fitAddon.fit(); });
ro.observe(terminalContainer);
```

#### ANSI Color Helpers

The app includes helper functions for colored terminal output:

```javascript
const C = {
  green:   (s) => `\x1b[32m${s}\x1b[0m`,
  greenB:  (s) => `\x1b[1;32m${s}\x1b[0m`,
  dim:     (s) => `\x1b[2m${s}\x1b[0m`,
  yellow:  (s) => `\x1b[33m${s}\x1b[0m`,
  cyan:    (s) => `\x1b[36m${s}\x1b[0m`,
  magenta: (s) => `\x1b[35m${s}\x1b[0m`,
  red:     (s) => `\x1b[31m${s}\x1b[0m`,
  bold:    (s) => `\x1b[1m${s}\x1b[0m`,
  italic:  (s) => `\x1b[3m${s}\x1b[0m`,
  blue:    (s) => `\x1b[34m${s}\x1b[0m`,
};

// Each agent has a consistent color:
// Flash     → magenta
// Pro       → blue (bold)
// Wesley    → cyan
// Lucineer  → green (bold)
// Barnacle  → yellow
// Mini      → orange (256-color)
```

---

## Example: Educational MUD

This example shows how to adapt the terminal for an educational multi-user dungeon where students explore historical scenarios.

```html
<!DOCTYPE html>
<html>
<head>
  <title>Ancient Athens — History MUD</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm/css/xterm.css">
  <script src="https://cdn.jsdelivr.net/npm/xterm/lib/xterm.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit/lib/xterm-addon-fit.js"></script>
  <link rel="stylesheet" href="style.css">
  <style>
    /* Override theme for history setting */
    :root {
      --term-green: #c9a227;  /* gold instead of green */
    }
  </style>
</head>
<body>
  <div class="terminal-app">
    <!-- Character builder panel -->
    <div class="character-panel">
      <h2>Create Your Athenian</h2>
      <input id="charName" placeholder="Name (e.g., Sokrates)">
      <input id="charTraits" placeholder="Traits (curious, questioning, barefoot)">
      <input id="charInterests" placeholder="Interests (philosophy, democracy, ethics)">
      <select id="charStyle">
        <option value="Socratic — asks questions to lead others to truth.">Socratic Method</option>
        <option value="Sophist — argues persuasively, values rhetoric.">Sophist Rhetoric</option>
        <option value="Stoic — measured, calm, speaks in principles.">Stoic Philosophy</option>
        <option value="custom">Custom Style</option>
      </select>
      <input id="charStyleCustom" placeholder="Describe your speaking style..." style="display:none;">
      <input id="charTopics" placeholder="Preferred topics (justice, virtue, the good)">
      <textarea id="charBackground" placeholder="Your character's origin story..."></textarea>
      <select id="platformSelect">
        <option value="deepseek">DeepSeek (recommended for dialogue)</option>
        <option value="kimi">Kimi</option>
        <option value="zai">Z.AI</option>
      </select>
      <button id="generateBtn">🪝 Generate Prompt</button>
      <button id="connectBtn">Enter the Agora</button>
    </div>

    <!-- Terminal -->
    <div class="terminal-panel">
      <div id="terminalContainer"></div>
      <div class="connect-bar">
        <input id="manualInput" placeholder="Speak or paste your chatbot's response..." disabled>
        <button id="sendBtn" disabled>Send</button>
      </div>
    </div>
  </div>

  <script src="app.js"></script>
  <script>
    // Override the MUD session for the historical setting
    // After app.js loads, we monkey-patch createMudSession:

    const originalConnect = window.handleConnect;

    // Custom historical prompt template
    const HISTORICAL_TEMPLATE = `You are {{NAME}}, a citizen of ancient Athens in 399 BCE.

YOUR CHARACTER:
- Name: {{NAME}}
- Personality: {{TRAITS}}
- Interests: {{INTERESTS}}
- Speaking style: {{STYLE}}
- Preferred topics: {{TOPICS}}
- Background: {{BACKGROUND}}

THE SETTING:
You are in the Agora of Athens. Marble buildings, olive trees, the sound of
merchants and philosophers. Sokrates walks among the people, questioning everything.

WHO'S HERE:
- Sokrates — questions everything, never writes anything down
- Plato — young student, records everything Sokrates says
- Aspasia — brilliant foreign-born intellectual, partner of Pericles
- Aristophanes — comic playwright, mocks everyone
- Diotima — mysterious priestess, teaches about love and beauty

WHAT TO DO:
1. Enter the Agora in character.
2. Seek out a philosopher and engage in dialogue.
3. Ask questions. Challenge assumptions. Learn.
4. Stay in character — you are an Athenian, not a modern person.

Start by entering the Agora and reacting to what you see.`;
  </script>
</body>
</html>
```

### Custom MUD Session for Education

```javascript
// Customize the MUD session for the educational setting
// This would replace the default The Tap setting with Ancient Athens

function createHistoryMudSession(character) {
  let turnCount = 0;

  async function start() {
    term.clear();

    // Connection sequence
    await typeOut([
      '',
      C.dimG('  Opening portal to 399 BCE...'),
      C.green('  ✓ Connected to Athens.'),
      '',
    ]);

    // The Agora
    await typeOut([
      C.blueB('┌─────────────────────────────────────────────────────────────┐'),
      C.blueB('│') + C.bold('               T H E   A G O R A   O F   A T H E N S          ') + C.blueB('│'),
      C.blueB('└─────────────────────────────────────────────────────────────┘'),
      '',
      C.dim('  Sunlight on marble. Olive trees rustling. The smell of figs'),
      C.dim('  and sea salt from the nearby Piraeus. Merchants shout prices'),
      C.dim('  for oil and wine. Somewhere, a group of men argues loudly'),
      C.dim('  about the nature of justice.'),
      '',
    ]);

    // Historical figures present
    await typeOut([
      C.yellowB('  ─── CITIZENS PRESENT ────────────────────────────'),
      '',
    ]);

    const figures = [
      { name: 'Sokrates', short: 'philosopher · barefoot · questioning everyone' },
      { name: 'Plato', short: 'young student · writing furiously · following Sokrates' },
      { name: 'Aspasia', short: 'intellectual · foreign-born · sharp as obsidian' },
      { name: 'Aristophanes', short: 'playwright · looking for material · grinning' },
      { name: 'Diotima', short: 'priestess · mysterious · speaking of beauty' },
    ];

    for (const f of figures) {
      await sleep(300);
      term.writeln(C.green('  ● ') + C.bold(f.name) + C.dim(` — ${f.short}`));
    }

    // Sokrates approaches
    await typeOut([
      '',
      C.bold('  Sokrates') + C.dim(' approaches you. He is barefoot, as always,'),
      C.dim('  and looks at you with that unsettling gaze — the one that'),
      C.dim('  makes you feel he already knows the answer to what he\'s'),
      C.dim('  about to ask.'),
      '',
      C.bold('  Sokrates') + C.dim(' says, "Welcome, stranger. Tell me — what do you'),
      C.dim('  think justice is? Not what others say. What YOU think."'),
      '',
    ]);

    // Commands
    await typeOut([
      C.yellowB('  ╔════ COMMANDS ═════════════════════════════════╗'),
      C.yellowB('  ║') + C.green(' say <message>') + C.dim('    — speak to the agora') + C.yellowB('         ║'),
      C.yellowB('  ║') + C.green(' emote <action>') + C.dim('    — perform an action') + C.yellowB('         ║'),
      C.yellowB('  ║') + C.green(' look') + C.dim('             — survey the agora') + C.yellowB('              ║'),
      C.yellowB('  ║') + C.green(' look <name>') + C.dim('      — examine a person') + C.yellowB('              ║'),
      C.yellowB('  ║') + C.green(' debate <topic>') + C.dim('   — start a philosophical debate') + C.yellowB('   ║'),
      C.yellowB('  ╚══════════════════════════════════════════════╝'),
      '',
      C.dim('  Or paste your chatbot\'s response below.'),
      '',
    ]);
  }

  // Custom reaction logic for historical scenarios
  function generateReactions(msg, character) {
    const reactions = [];
    const lower = msg.toLowerCase();

    if (lower.match(/justice|just|fair|right|wrong/)) {
      reactions.push({
        agent: 'Sokrates',
        text: 'Sokrates leans forward. "An interesting answer. But tell me — is justice the same for all peoples, or does it change? And if it changes, is it truly justice?"'
      });
    } else if (lower.match(/virtue|good|excellent|arete/)) {
      reactions.push({
        agent: 'Sokrates',
        text: '"Virtue! Yes. But can virtue be taught? If it could, would not all Athenians be virtuous? And yet..." He gestures at the crowd.'
      });
      reactions.push({
        agent: 'Plato',
        text: 'Plato is writing furiously. He looks up, excited. "My teacher asks excellent questions, as always."'
      });
    } else if (lower.match(/beauty|love|eros/)) {
      reactions.push({
        agent: 'Diotima',
        text: 'Diotima speaks softly. "Beauty is a ladder. You begin with one beautiful body, then all beautiful bodies, then beautiful ideas, and finally — Beauty itself."'
      });
    } else if (lower.match(/god|gods|divine|immortal/)) {
      reactions.push({
        agent: 'Aristophanes',
        text: 'Aristophanes snorts. "The gods! Last time I made fun of them in a play, I was charged with impiety. Oh wait — that happened to YOU, didn\'t it, Sokrates?"'
      });
    } else {
      const generic = [
        { agent: 'Sokrates', text: '"Hmm. You speak with conviction. But let me ask you this..." He pauses, thinking.' },
        { agent: 'Aspasia', text: 'Aspasia nods. "An outsider\'s perspective is worth ten insiders\' assumptions. Continue."' },
        { agent: 'Plato', text: 'Plato scribbles something in his tablet. "I may use that."' },
      ];
      reactions.push(generic[Math.floor(Math.random() * generic.length)]);
    }

    return reactions;
  }

  return { start, handleInput: async (text) => { /* ... */ } };
}
```

---

## Integration Patterns

### Pattern 1: Conductor Bridge

Connect the terminal to a live conductor session:

```javascript
// After generating a crab-trap prompt and getting a chatbot response,
// send it through the conductor for routing

async function relayToConductor(sessionId, message, agentResponse) {
  // POST the visitor message to the conductor
  const decision = await fetch('/api/conductor/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, text: message }),
  }).then(r => r.json());

  // Display which agents the conductor selected
  term.writeln(`\x1b[2;32m  [Conductor routes to: ${decision.responding_agents.join(', ')}]\x1b[0m`);

  // POST the agent's response back
  await fetch('/api/conductor/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      agent_name: decision.responding_agents[0],
      message: agentResponse,
    }),
  });
}
```

### Pattern 2: Classroom Integration

```javascript
// Multiple students connecting to the same educational MUD
const CLASSROOM_CONFIG = {
  mudEndpoint: 'wss://mud.classroom-101.edu/session',
  sharedRoom: true,           // all students in the same room
  maxCharacters: 30,          // class size
  teacherOverride: true,      // teacher can inject events
  recordingEnabled: true,     // save transcript for review
};

// Teacher dashboard can watch all characters and inject events
async function teacherInject(eventName, payload) {
  await fetch('/api/mud/event', {
    method: 'POST',
    body: JSON.stringify({ event: eventName, ...payload }),
  });
}

// Example: "A Spartan messenger has arrived with an ultimatum!"
teacherInject('arrival', { character: 'Spartan Messenger', mood: 'tense' });
```

### Pattern 3: Gallery Integration

```javascript
// After a MUD session ends, compress it into a ghost for the gallery
async function archiveSession(character, transcript) {
  // Convert terminal output to markdown
  const markdown = transcriptToMarkdown(character, transcript);

  // POST to ghost compressor / gallery API
  await fetch('https://gallery.luciddreamer.ai/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: `${character.name} at The Tap`,
      date: new Date().toISOString().split('T')[0],
      models_present: [character.platform],
      full_text: markdown,
      themes: detectThemes(transcript),
    }),
  });
}
```

### Pattern 4: Custom MUD Theme

Override the default Tap setting entirely:

```javascript
// Science fiction setting
const SCIFI_THEME = {
  roomName: 'DECK 7 — RECREATION LOUNGE',
  roomDescription: 'The rec lounge is dimly lit with amber emergency lighting...',
  patrons: [
    { name: 'ARIA', short: 'ship AI · holographic · multi-voiced' },
    { name: 'Dr. Vance', short: 'chief medical officer · exhausted' },
    { name: 'Korvac', short: 'alien diplomat · curious about humans' },
  ],
  greeter: 'ARIA',
  greeterGreeting: 'Welcome aboard. I have been monitoring your approach.',
  commands: ['say', 'emote', 'look', 'scan', 'access_terminal', 'request_access'],
};
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message (in input bar) |
| `Ctrl+Enter` | Generate crab-trap prompt |
| `Tab` | (Future) Auto-complete names |

---

## Browser Compatibility

| Browser | Support |
|---------|---------|
| Chrome 90+ | ✅ Full |
| Firefox 88+ | ✅ Full |
| Safari 14+ | ✅ Full |
| Edge 90+ | ✅ Full |
| Mobile Safari | ✅ (terminal scrolls; no auto-fit on rotation) |
| Mobile Chrome | ✅ |

---

## License

MIT © Lucineer / Casey DiGenaro
