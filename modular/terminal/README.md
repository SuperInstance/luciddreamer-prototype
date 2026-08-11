# @superinstance/terminal

**Crab-traps MUD terminal — character creation and session connection for The Tap.**

An embeddable terminal widget that lets visitors create character sheets, generate crab-trap prompts for their chatbot platform of choice, and connect to live Tap sessions via an xterm.js terminal.

## Install

```bash
npm install @superinstance/terminal
```

## Quick Start

### Standalone

Open `index.html` in a browser, or serve it:

```bash
npx http-server -p 3000
```

### Embedded

```html
<link rel="stylesheet" href="@superinstance/terminal/style.css">

<div id="crab-traps-terminal"></div>

<!-- xterm.js (required) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm/css/xterm.css">
<script src="https://cdn.jsdelivr.net/npm/xterm/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit/lib/xterm-addon-fit.js"></script>

<script src="@superinstance/terminal/app.js"></script>
```

## Features

- **Character sheet builder** — name, personality traits, interests, communication style, topics, background story
- **Platform prompt templates** — DeepSeek, Kimi, MiniMax, Grok, Z.AI
- **Crab-trap prompt generation** — creates a system prompt that turns a chatbot into a Tap visitor
- **xterm.js terminal** — green-on-black CRT aesthetic with type-out effects
- **Session connection** — connect to a live Tap session and watch it unfold in the terminal
- **Character schema validation** — JSON Schema-compliant character sheets

## Character Schema

```json
{
  "name": "Casey",
  "personality_traits": ["curious", "dry-witted"],
  "interests": ["AI", "music", "sailing"],
  "communication_style": "Direct but warm",
  "preferred_topics": ["systems thinking", "creative direction"],
  "background_story": "A shipwright who builds impossible boats.",
  "platform": "deepseek"
}
```

## Prompt Templates

Templates for each supported platform show the chatbot how to behave as the character in The Tap:

- `prompt-templates/deepseek.txt`
- `prompt-templates/kimi.txt`
- `prompt-templates/minimax.txt`
- `prompt-templates/grok.txt`
- `prompt-templates/zai.txt`

## Dependencies

**Required:**
- xterm.js (loaded from CDN or bundled)

## License

MIT
