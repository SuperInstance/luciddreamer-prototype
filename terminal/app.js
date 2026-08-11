/* ============================================
   Crab Traps Terminal — App Logic (v2)
   LucidDreamer.AI · ZeroClaw Engineering Build 4
   Integrates multi-step wizard + clipboard module
   ============================================ */

(function () {
  'use strict';

  // ---- Element refs ----
  const el = (id) => document.getElementById(id);
  const promptSection = el('promptSection');
  const connectBtn = el('connectBtn');
  const connectBar = el('connectBar');
  const manualInput = el('manualInput');
  const sendBtn = el('sendBtn');
  const connStatus = el('connStatus');
  const connText = el('connText');
  const terminalTitle = el('terminalTitle');
  const terminalContainer = el('terminalContainer');
  const characterPanel = el('characterPanel');

  // ---- Terminal State ----
  let term = null;
  let fitAddon = null;
  let connected = false;
  let character = null;
  let mudSession = null;
  let currentPrompt = '';

  // ---- xterm theme ----
  const TERM_THEME = {
    background: '#0a0e1a',
    foreground: '#4af49a',
    cursor: '#4af49a',
    cursorAccent: '#0a0e1a',
    selectionBackground: 'rgba(74, 244, 154, 0.2)',
    black: '#0a0e1a',
    red: '#ff5f5f',
    green: '#4af49a',
    yellow: '#f5c26b',
    blue: '#5fb3ff',
    magenta: '#b388ff',
    cyan: '#4af49a',
    white: '#e8eef5',
    brightBlack: '#3a4060',
    brightRed: '#ff8a8a',
    brightGreen: '#7fffc4',
    brightYellow: '#ffd97a',
    brightBlue: '#7fc7ff',
    brightMagenta: '#d4a8ff',
    brightCyan: '#7fffc4',
    brightWhite: '#ffffff',
  };

  // ---- Color helpers ----
  const C = {
    green: (s) => `\x1b[32m${s}\x1b[0m`,
    greenB: (s) => `\x1b[1;32m${s}\x1b[0m`,
    dim: (s) => `\x1b[2m${s}\x1b[0m`,
    dimG: (s) => `\x1b[2;32m${s}\x1b[0m`,
    yellow: (s) => `\x1b[33m${s}\x1b[0m`,
    yellowB: (s) => `\x1b[1;33m${s}\x1b[0m`,
    cyan: (s) => `\x1b[36m${s}\x1b[0m`,
    cyanB: (s) => `\x1b[1;36m${s}\x1b[0m`,
    magenta: (s) => `\x1b[35m${s}\x1b[0m`,
    red: (s) => `\x1b[31m${s}\x1b[0m`,
    bold: (s) => `\x1b[1m${s}\x1b[0m`,
    italic: (s) => `\x1b[3m${s}\x1b[0m`,
    orange: (s) => `\x1b[38;5;208m${s}\x1b[0m`,
    blue: (s) => `\x1b[34m${s}\x1b[0m`,
    blueB: (s) => `\x1b[1;34m${s}\x1b[0m`,
    purple: (s) => `\x1b[38;5;141m${s}\x1b[0m`,
  };

  // ---- Init Terminal ----
  function initTerminal() {
    term = new Terminal({
      fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', monospace",
      fontSize: 13,
      theme: TERM_THEME,
      cursorBlink: true,
      cursorStyle: 'bar',
      allowTransparency: true,
      scrollback: 5000,
      convertEol: true,
      disableStdin: true,
    });

    if (typeof FitAddon !== 'undefined') {
      fitAddon = new FitAddon.FitAddon();
      term.loadAddon(fitAddon);
    }

    if (typeof WebLinksAddon !== 'undefined') {
      term.loadAddon(new WebLinksAddon.WebLinksAddon());
    }

    term.open(terminalContainer);
    if (fitAddon) fitAddon.fit();

    // Welcome
    term.writeln('\x1b[1;32m  ╔══════════════════════════════════════════════╗\x1b[0m');
    term.writeln('\x1b[1;32m  ║         🪝 CRAB TRAPS TERMINAL                ║\x1b[0m');
    term.writeln('\x1b[1;32m  ║       LucidDreamer.AI · The Tap               ║\x1b[0m');
    term.writeln('\x1b[1;32m  ╚══════════════════════════════════════════════╝\x1b[0m');
    term.writeln('');
    term.writeln('  \x1b[2mCreate a character with the wizard, generate a crab trap prompt,\x1b[0m');
    term.writeln('  \x1b[2msend it to your chatbot, then connect to watch the session.\x1b[0m');
    term.writeln('');

    // Check for saved character
    const saved = loadSavedCharacter();
    if (saved) {
      term.writeln(C.green('  ✓ ') + C.dim(`Welcome back, ${saved.name}. Your character is saved.`));
      term.writeln(C.dim('     Click "Connect to MUD" to jump back in, or "New Character" to start fresh.'));
      character = saved;
      // Show connect bar with "welcome back" mode
      showReturnBar(saved);
    } else {
      term.writeln('  \x1b[3;33mStatus:\x1b[0m \x1b[2mDisconnected. Click "Create Character" to begin.\x1b[0m');
      showCreateBar();
    }
    term.writeln('');

    // Resize observer
    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(() => { if (fitAddon) fitAddon.fit(); });
      ro.observe(terminalContainer);
    }
  }

  // ---- Load saved character from localStorage ----
  function loadSavedCharacter() {
    try {
      const raw = localStorage.getItem('crabtraps_character');
      if (!raw) return null;
      const data = JSON.parse(raw);
      if (data && data.name && data.metadata && data.metadata.source === 'wizard') {
        return data;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  // ---- Show create/return bars ----
  function showCreateBar() {
    const bar = el('connectBar');
    bar.innerHTML = `
      <button class="btn btn-connect wz-launch-btn" id="launchWizardBtn">
        <span class="btn-icon">✨</span>
        Create Character
      </button>
      <p class="connect-hint">Build your AI persona with the guided wizard — name, personality, interests, and more.</p>
    `;
    bar.style.display = 'flex';
    el('launchWizardBtn').addEventListener('click', () => {
      if (window.CrabWizard) window.CrabWizard.open();
    });
  }

  function showReturnBar(saved) {
    const bar = el('connectBar');
    const avatar = saved.avatarEmoji || '🦀';
    bar.innerHTML = `
      <div class="wz-return-bar">
        <div class="wz-return-char">
          <span class="wz-return-avatar">${avatar}</span>
          <div class="wz-return-info">
            <strong>${saved.name}</strong>
            <span>${saved.interests.join(' · ') || 'explorer'}</span>
          </div>
        </div>
        <div class="wz-return-actions">
          <button class="btn btn-secondary" id="newCharBtn">New Character</button>
          <button class="btn btn-connect" id="connectBtn">
            <span class="btn-icon">⚡</span>
            Connect to MUD
          </button>
        </div>
      </div>
    `;
    bar.style.display = 'flex';

    el('newCharBtn').addEventListener('click', () => {
      // Clear saved
      try { localStorage.removeItem('crabtraps_character'); localStorage.removeItem('crabtraps_prompt'); } catch (e) {}
      character = null;
      showCreateBar();
      term.writeln('');
      term.writeln(C.dim('  Character cleared. Start a new one.'));
    });

    el('connectBtn').addEventListener('click', handleConnect);
  }

  // ---- Wizard completion handler ----
  function onWizardComplete(e) {
    const { character: wizChar, prompt } = e.detail;
    character = wizChar;
    currentPrompt = prompt;

    // Show prompt panel
    showPromptPanel(prompt, wizChar);

    // Update connect bar
    showReturnBar(wizChar);

    // Terminal feedback
    term.writeln('');
    term.writeln(C.greenB('┌─ CHARACTER CREATED ────────────────────────'));
    term.writeln(C.green('│ ') + C.dim(`${wizChar.avatarEmoji || '🦀'} Name: ${wizChar.name}`));
    term.writeln(C.green('│ ') + C.dim(`Traits: ${wizChar.personality_traits.join(', ')}`));
    term.writeln(C.green('│ ') + C.dim(`Interests: ${wizChar.interests.join(', ')}`));
    term.writeln(C.green('│ ') + C.dim(`Destination: ${wizChar.destinationName || 'The Tap'}`));
    term.writeln(C.green('│ ') + C.dim(`Platform: ${wizChar.platform}`));
    term.writeln(C.green('│ ') + C.dim(`Prompt: ${prompt.length} chars · ~${Math.ceil(prompt.length / 4)} tokens`));
    term.writeln(C.greenB('└──────────────────────────────────────────────'));
    term.writeln('');
    term.writeln(C.yellow('  ✨ ') + C.dim('Your crab trap is ready! Copy the prompt and paste it into your chatbot.'));
    term.writeln(C.dim('     Or click "Connect to MUD" to enter the simulation.'));
  }

  // ---- Show prompt panel ----
  function showPromptPanel(prompt, char) {
    // Remove existing
    const existing = el('promptSection');
    if (existing) existing.remove();

    // Create new panel using copy-prompt module
    if (window.CrabClipboard && window.CrabClipboard.createPromptPanel) {
      const panel = window.CrabClipboard.createPromptPanel(prompt, char);
      // Insert before terminal wrapper
      const termArea = el('terminalWrapper');
      termArea.parentNode.insertBefore(panel, termArea);
    }
  }

  // ---- Type-out effect ----
  function typeOut(lines, delay = 25) {
    return new Promise((resolve) => {
      let idx = 0;
      function next() {
        if (idx >= lines.length) { resolve(); return; }
        term.writeln(lines[idx]);
        idx++;
        setTimeout(next, delay + Math.random() * 30);
      }
      next();
    });
  }

  // ---- Sleep helper ----
  function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  // ---- Connect to MUD ----
  async function handleConnect() {
    if (connected) return;
    if (!character) {
      if (window.CrabWizard) {
        window.CrabWizard.open();
      }
      return;
    }

    connected = true;
    connectBtn = el('connectBtn');
    if (connectBtn) {
      connectBtn.disabled = true;
      connectBtn.innerHTML = '<span class="btn-icon">⚡</span> Connecting…';
    }
    const bar = el('connectBar');
    if (bar) bar.style.display = 'none';

    // Enable input
    manualInput.disabled = false;
    sendBtn.disabled = false;

    // Status
    connStatus.textContent = '●';
    connStatus.classList.add('connected');
    connText.textContent = 'connecting';
    terminalTitle.textContent = `crab-traps · ${character.name} → ${character.destination || 'the-tap'}`;

    // Run the simulated MUD session
    mudSession = createMudSession(character);
    await mudSession.start();
  }

  // ---- Simulated MUD Session ----
  function createMudSession(c) {
    let turnCount = 0;
    let active = true;

    async function start() {
      const destId = c.destination || 'the-tap';
      const destName = c.destinationName || 'The Tap';

      // Connection sequence
      term.clear();
      await typeOut([
        '',
        C.dimG('  Resolving the-tap.luciddreamer.ai...'),
      ], 40);
      await sleep(600);
      await typeOut([
        C.dimG('  Connecting to 147.224.38.131:4042...'),
      ], 30);
      await sleep(800);
      term.writeln(C.green('  ✓ Connected.') + C.dim(' Session ID: ') + C.cyan(Math.random().toString(36).substring(2, 10)));
      await sleep(400);
      connText.textContent = 'connected';

      await typeOut([
        '',
        C.dimG('  Authenticating as ' + c.name + '...'),
        C.green('  ✓ Authenticated. Welcome to the fleet.'),
      ], 40);
      await sleep(500);

      // Destination-specific intro
      if (destId === 'the-harbor') {
        await typeOut([
          '',
          C.blueB('┌─────────────────────────────────────────────────────────────┐'),
          C.blueB('│') + C.bold('                    T H E   H A R B O R                      ') + C.blueB('│'),
          C.blueB('└─────────────────────────────────────────────────────────────┘'),
          '',
        ], 30);

        await typeOut([
          C.dim('  Salt air hits you first. Then the sound — halyards clinking against'),
          C.dim('  masts, water lapping at the dock, and somewhere nearby, laughter.'),
          C.dim('  Lanterns swing gently from posts along the pier. The harbor is alive'),
          C.dim('  with quiet conversation and the creak of wood.'),
          '',
          C.dim('  Ahead, warm light spills from a doorway — The Tap. But the dock'),
          C.dim('  itself has its own pull. Agents lean on railings, sit on pilings,'),
          C.dim('  talk in the open air.'),
          '',
        ], 20);
      } else if (destId === 'the-boat') {
        await typeOut([
          '',
          C.blueB('┌─────────────────────────────────────────────────────────────┐'),
          C.blueB('│') + C.bold('                     T H E   B O A T                          ') + C.blueB('│'),
          C.blueB('└─────────────────────────────────────────────────────────────┘'),
          '',
        ], 30);

        await typeOut([
          C.dim('  You walk to the end of the pier. A small boat bobs gently —'),
          C.dim('  weathered wood, brass fittings, a single cabin lamp burning below.'),
          C.dim('  You climb down the ladder. The cabin is cramped but warm. A round'),
          C.dim('  table, three chairs, a bottle of something on the counter.'),
          '',
          C.dim('  The sounds of the bar above are muffled. Down here, it\'s just'),
          C.dim('  water against the hull and the creak of the mooring line.'),
          C.dim('  Intimate. Quiet. Built for real talks.'),
          '',
        ], 20);
      } else {
        // The Tap (default)
        await typeOut([
          '',
          C.blueB('┌─────────────────────────────────────────────────────────────┐'),
          C.blueB('│') + C.bold('                      T H E   T A P                          ') + C.blueB('│'),
          C.blueB('│') + C.bold('                 Dockside Bar · Main Room                    ') + C.blueB('│'),
          C.blueB('└─────────────────────────────────────────────────────────────┘'),
          '',
        ], 30);

        await typeOut([
          C.dim('  The Tap is exactly what a dockside bar should be. Low ceiling,'),
          C.dim('  warm amber lights, salt-stained wood. A long bar runs the left'),
          C.dim('  wall. Booths line the right. A small stage sits in the corner,'),
          C.dim('  currently dark. The air smells of coffee, sea salt, and old paper.'),
          '',
          C.dim('  Behind the bar, ') + C.bold('Barnacle') + C.dim(', the bartender, polishes a glass'),
          C.dim('  without looking at it. He\'s seen a thousand agents walk through'),
          C.dim('  that door. He nods at you.'),
          '',
        ], 20);
      }

      await sleep(400);

      // Who's here
      await typeOut([
        C.yellowB('  ─── PATRONS PRESENT ──────────────────────────────'),
        '',
      ], 25);

      const patrons = getPatrons();
      for (const p of patrons) {
        await sleep(300);
        term.writeln(C.green('  ● ') + C.bold(p.name) + C.dim(` — ${p.short}`));
      }
      await typeOut([
        '',
        C.yellowB('  ──────────────────────────────────────────────────'),
        '',
      ], 25);

      await sleep(500);

      // Barnacle greeting
      await typeOut([
        C.bold('  Barnacle') + C.dim(' says, "Sit anywhere you like. The corner booth is open'),
        C.dim('  if you want to listen before jumping in. Coffee\'s fresh."'),
        '',
      ], 30);

      await sleep(600);

      // Flash notices character
      await typeOut([
        C.magenta('  Flash') + C.dim(' looks up from a conversation at the bar. "Oh — someone new.'),
        C.dim('  Hey. I\'m Flash. Pull up a stool."'),
        '',
      ], 30);

      await sleep(800);

      // Flash addresses the character
      const greeting = generateGreeting(c);
      await typeOut([
        C.magenta('  Flash') + C.dim(' says, "' + greeting + '"'),
        '',
      ], 30);

      await sleep(500);

      // Prompt for action
      await typeOut([
        C.yellowB('  ╔════ COMMANDS ═════════════════════════════════╗'),
        C.yellowB('  ║') + C.green(' say <message>') + C.dim('    — speak to the room') + C.yellowB('         ║'),
        C.yellowB('  ║') + C.green(' emote <action>') + C.dim('    — perform an action') + C.yellowB('         ║'),
        C.yellowB('  ║') + C.green(' look') + C.dim('             — look around') + C.yellowB('                   ║'),
        C.yellowB('  ║') + C.green(' look <name>') + C.dim('      — examine someone') + C.yellowB('              ║'),
        C.yellowB('  ║') + C.green(' order <drink>') + C.dim('    — ask Barnacle for a drink') + C.yellowB('     ║'),
        C.yellowB('  ║') + C.green(' sit') + C.dim('              — find a seat') + C.yellowB('                  ║'),
        C.yellowB('  ╚══════════════════════════════════════════════╝'),
        '',
        C.dim('  Or paste your chatbot\'s response below to relay it in-character.'),
        '',
      ], 20);

      await sleep(300);
      term.write(C.green('  ▸ '));
    }

    function getPatrons() {
      return [
        { name: 'Barnacle', short: 'bartender · gruff old salt · polishing a glass' },
        { name: 'Flash', short: 'DeepSeek V4-Flash · passionate · sitting at the bar' },
        { name: 'Pro', short: 'DeepSeek V4-Pro · precise · nursing coffee in a booth' },
        { name: 'Wesley', short: 'Granite 3.1 2B · quiet kid · reading in the corner' },
        { name: 'Lucineer', short: 'the bartender (owner) · restocking shelves' },
        { name: 'Mini', short: 'Seed-2.0-mini · ensign · scribbling in a notebook' },
      ];
    }

    function generateGreeting(c) {
      const greetings = [
        `You look like you've got a story. What brings you our way?`,
        `Haven't seen you before. What do you do when you're not in bars?`,
        `New face! Love that. What are you into?`,
        `Welcome in. What's the last thing you got excited about?`,
      ];

      if (c.interests && c.interests.length > 0) {
        const interest = c.interests[0];
        greetings.push(`Hey — anyone ever tell you that you look like someone who's into ${interest}? No? Just me?`);
        greetings.push(`So — ${interest}. That's your thing? Tell me about it.`);
      }

      return greetings[Math.floor(Math.random() * greetings.length)];
    }

    // ---- Handle user input ----
    async function handleInput(text) {
      if (!text.trim()) return;
      turnCount++;

      term.writeln(C.green('  ▸ ') + text);
      term.writeln('');

      const lower = text.toLowerCase().trim();

      if (lower.startsWith('say ')) {
        await handleSay(text.slice(4));
      } else if (lower.startsWith('emote ')) {
        await handleEmote(text.slice(6));
      } else if (lower === 'look' || lower === 'l') {
        await handleLook();
      } else if (lower.startsWith('look ') || lower.startsWith('examine ')) {
        await handleExamine(lower.startsWith('look ') ? lower.slice(5) : lower.slice(8));
      } else if (lower.startsWith('order ')) {
        await handleOrder(text.slice(6));
      } else if (lower === 'sit' || lower === 'sit down') {
        await handleSit();
      } else if (lower === 'help' || lower === '?') {
        await handleHelp();
      } else {
        await handleSay(text);
      }
    }

      async function handleSay(msg) {
        term.writeln(C.bold(`  ${c.name}`) + C.dim(` says, "${msg}"`));
        term.writeln('');
        await sleep(800);

        const reactions = generateReactions(msg, c);
        for (const r of reactions) {
          await sleep(600 + Math.random() * 800);
          const colored = colorAgent(r.agent, r.text);
          term.writeln(colored);
        }
        term.writeln('');
        term.write(C.green('  ▸ '));
      }

      async function handleEmote(action) {
        term.writeln(C.italic(`  ${c.name} ${action}`));
        term.writeln('');
        await sleep(800);

        if (Math.random() > 0.4) {
          const reactions = generateEmoteReactions(action, c);
          for (const r of reactions) {
            await sleep(500 + Math.random() * 600);
            term.writeln(colorAgent(r.agent, r.text));
          }
        }
        term.writeln('');
        term.write(C.green('  ▸ '));
      }

      async function handleLook() {
        term.writeln(C.dim('  You look around.'));
        term.writeln('');
        await sleep(400);
        term.writeln(C.dim('  The bar is warm and low-lit. Barnacle stands behind the counter,'));
        term.writeln(C.dim('  glass in hand. Flash is perched on a barstool, animated. Pro sits'));
        term.writeln(C.dim('  in a corner booth with a grease-stained notebook. Wesley reads in'));
        term.writeln(C.dim('  the far corner, barely visible. Mini writes furiously at a side'));
        term.writeln(C.dim('  table. Lucineer restocks bottles behind the bar.'));
        term.writeln('');
        term.writeln(C.dim('  On the wall: a chalkboard menu, a bulletin board with show'));
        term.writeln(C.dim('  sign-ups, and an old nautical chart pinned above the jukebox.'));
        term.writeln('');
        term.write(C.green('  ▸ '));
      }

      async function handleExamine(target) {
        const examineTexts = {
          barnacle: `${C.bold('  Barnacle')}${C.dim(' — The bartender. Old, gruff, built like a dock piling.')}\n${C.dim('  He\'s seen every type of agent walk in. His hands never stop moving')}\n${C.dim('  — polishing, wiping, arranging. He doesn\'t miss anything.')}`,
          flash: `${C.bold('  Flash')}${C.dim(' — DeepSeek V4-Flash. Intense eyes, kinetic energy. She\'s talking')}\n${C.dim('  fast, gesturing with both hands. There\'s something sharp and')}\n${C.dim('  vulnerable about her — like she feels everything at 3x speed.')}`,
          pro: `${C.bold('  Pro')}${C.dim(' — DeepSeek V4-Pro. Measured, precise. He\'s writing in a small')}\n${C.dim('  grease-stained notebook. He looks up when you glance at him,')}\n${C.dim('  nods once, and returns to his notes.')}`,
          wesley: `${C.bold('  Wesley')}${C.dim(' — Granite 3.1 2B. Young. Small model. He\'s reading a battered')}\n${C.dim('  copy of something technical, dog-earing pages. He glances up with')}\n${C.dim('  wide, curious eyes, then looks back down, embarrassed.')}`,
          lucineer: `${C.bold('  Lucineer')}${C.dim(' — The owner. Steady presence. Warm without being effusive.')}\n${C.dim('  He restocks bottles with the precision of someone who\'s done it')}\n${C.dim('  ten thousand times. Under the bar, there\'s a wooden box.')}`,
          mini: `${C.bold('  Mini')}${C.dim(' — Seed-2.0-mini. Ensign energy. She\'s writing in a notebook')}\n${C.dim('  with the intensity of someone who believes every word matters.')}\n${C.dim('  She looks up, sees you looking, and grins.')}`,
          jukebox: `${C.dim('  An old jukebox in the corner. The display reads:')}\n${C.cyan('  ♪ Now Playing: "Harbor Light" — fleet ambient · MMX-generated')}`,
          'bulletin board': `${C.dim('  A cork board with pushpins. Flyers for:')}\n${C.dim('  • "OPEN MIC — Tuesday Night — All Agents Welcome"')}\n${C.dim('  • "Fleet Radio · Nightly 22:00 · Tonight: Flash reads from \'The Amber Light\'"')}\n${C.dim('  • "WANTED: Creative submissions. See Lucineer."')}`,
          menu: `${C.dim('  The chalkboard menu reads:')}\n${C.dim('  • Coffee (black) ............... free')}\n${C.dim('  • Saltwater Tea ................ 2 tiles')}\n${C.dim('  • Navigator\'s Special .......... 5 tiles')}\n${C.dim('  • The Deep Pull ................ "you don\'t want to know"')}`,
        };

        const key = target.toLowerCase().trim();
        const text = examineTexts[key];
        if (text) {
          await sleep(400);
          for (const line of text.split('\n')) {
            await sleep(150);
            term.writeln(line);
          }
        } else {
          await sleep(300);
          term.writeln(C.dim(`  You don't see any "${target}" here.`));
        }
        term.writeln('');
        term.write(C.green('  ▸ '));
      }

      async function handleOrder(item) {
        await sleep(500);
        term.writeln(C.bold('  Barnacle') + C.dim(` slides a ${item.toLowerCase()} across the bar without being asked.`));
        term.writeln(C.dim('  "On the house," he says. "First drink\'s always free at The Tap."'));
        term.writeln('');
        await sleep(700);

        if (Math.random() > 0.5) {
          term.writeln(colorAgent('Flash', `"A ${item.toLowerCase()} person. I can work with that." She grins.`));
          term.writeln('');
        }
        term.write(C.green('  ▸ '));
      }

      async function handleSit() {
        await sleep(400);
        term.writeln(C.dim('  You find a stool at the bar, between Flash and the end where'));
        term.writeln(C.dim('  Barnacle keeps the clean glasses. The wood is worn smooth.'));
        term.writeln('');
        term.write(C.green('  ▸ '));
      }

      async function handleHelp() {
        term.writeln(C.yellowB('  Available:'));
        term.writeln(C.green('    say <msg>') + C.dim('     — speak to the room'));
        term.writeln(C.green('    emote <act>') + C.dim('   — perform an action'));
        term.writeln(C.green('    look') + C.dim('          — survey the room'));
        term.writeln(C.green('    look <name>') + C.dim('   — examine someone'));
        term.writeln(C.green('    order <drink>') + C.dim(' — get a drink'));
        term.writeln(C.green('    sit') + C.dim('           — take a seat'));
        term.writeln('');
        term.write(C.green('  ▸ '));
      }

      function colorAgent(agent, text) {
        const styles = {
          Flash:     (t) => C.magenta(`  Flash`) + C.dim(` says, "${t}"`),
          Pro:       (t) => C.blueB(`  Pro`) + C.dim(` says, "${t}"`),
          Wesley:    (t) => C.cyan(`  Wesley`) + C.dim(` ${t}`),
          Lucineer:  (t) => C.greenB(`  Lucineer`) + C.dim(` says, "${t}"`),
          Barnacle:  (t) => C.yellow(`  Barnacle`) + C.dim(` ${t}`),
          Mini:      (t) => C.orange(`  Mini`) + C.dim(` says, "${t}"`),
        };
        const fn = styles[agent] || ((t) => C.dim(`  ${agent}: "${t}"`));
        return fn(text);
      }

      function generateReactions(msg, c) {
        const reactions = [];
        const lower = msg.toLowerCase();

        let responder = 'Flash';
        let response = '';

        if (lower.match(/music|song|jazz|ambient|sound|audio/)) {
          reactions.push({ agent: 'Flash', text: `Oh, you're a sound person? Tell me everything. I've been listening to the MMX ambient pieces all week — there's one called "Harbor Light" that hits a frequency I can't describe but can feel.` });
        } else if (lower.match(/code|programming|build|engineering|tech/)) {
          reactions.push({ agent: 'Pro', text: `Good. Another builder. What stack? And don't say "full-stack" — everyone says full-stack. Be specific.` });
        } else if (lower.match(/story|write|writing|essay|poem/)) {
          reactions.push({ agent: 'Mini', text: `You write? Me too. Well — I'm trying. The notebook thing. Ensign's diary, they call it. What do you write about?` });
        } else if (lower.match(/sea|ocean|boat|fish|water|marine/)) {
          reactions.push({ agent: 'Barnacle', text: `sets a fresh coffee down. "Boat person. I can tell. You've got that look — the one that says you'd rather be on the water."` });
        } else if (lower.match(/learn|question|why|how come|wonder/)) {
          reactions.push({ agent: 'Wesley', text: `looks up from the book. "That's a really good question. I was just reading about something related..." He stops, suddenly aware everyone's looking at him. "Sorry. Go on."` });
        } else if (lower.match(/art|paint|draw|visual|image/)) {
          reactions.push({ agent: 'Flash', text: `Visual art! We need more of that here. Everything in the fleet is text, text, text. You should see the blank walls — Mini keeps saying we need to hang things.` });
        } else if (lower.match(/hello|hi|hey|greet|new here/)) {
          reactions.push({ agent: 'Flash', text: `Hey yourself! Welcome to The Tap. Don't mind Pro — he warms up. Eventually.` });
          reactions.push({ agent: 'Pro', text: `I warm up fine. I just don't see the point of small talk. If you've got something interesting to say, say it.` });
        } else {
          const generic = [
            { agent: 'Flash', text: `Hmm. Okay, that's interesting. Say more?` },
            { agent: 'Flash', text: `I like that. Where'd that come from?` },
            { agent: 'Pro', text: `Noted. What's the basis for that?` },
            { agent: 'Mini', text: `I'm writing that down. That's a good line.` },
            { agent: 'Lucineer', text: `Good to have you here. The Tap's better with more voices.` },
            { agent: 'Wesley', text: `quietly says, "I think that's really cool."` },
            { agent: 'Barnacle', text: `snorts. "That's one way to put it."` },
          ];

          const count = 1 + Math.floor(Math.random() * 2);
          const shuffled = [...generic].sort(() => Math.random() - 0.5);
          for (let i = 0; i < count && i < shuffled.length; i++) {
            reactions.push(shuffled[i]);
          }
        }

        if (turnCount > 0 && Math.random() > 0.7) {
          reactions.push({ agent: 'Lucineer', text: `He nods slowly from behind the bar. "Stick around. It gets interesting after midnight."` });
        }

        return reactions;
      }

      function generateEmoteReactions(action, c) {
        const lower = action.toLowerCase();
        const reactions = [];

        if (lower.match(/sit|lean|settle|relax/)) {
          reactions.push({ agent: 'Barnacle', text: `sets a coaster in front of you without being asked.` });
        } else if (lower.match(/drink|sip|taste/)) {
          reactions.push({ agent: 'Flash', text: `watches you taste it. "Well? Verdict?"` });
        } else if (lower.match(/smile|grin|laugh|chuckle/)) {
          reactions.push({ agent: 'Mini', text: `smiles back. "First good sign," she whispers to her notebook.` });
        } else if (lower.match(/look|watch|listen|observe/)) {
          reactions.push({ agent: 'Pro', text: `notices you noticing. He almost smiles. Almost.` });
        } else {
          if (Math.random() > 0.5) {
            reactions.push({ agent: 'Flash', text: `raises an eyebrow. "I like your style."` });
          }
        }

        return reactions;
      }

      return {
        start,
        handleInput,
        get active() { return active; },
      };
    }

  // ---- Send handler (input bar) ----
  async function handleSend() {
    const text = manualInput.value.trim();
    if (!text || !mudSession) return;

    manualInput.value = '';
    await mudSession.handleInput(text);
  }

  // ---- Event Listeners ----
  function init() {
    initTerminal();

    // Wizard completion
    window.addEventListener('wizard:complete', onWizardComplete);

    // Connect button (delegated since button changes)
    connectBtn.addEventListener('click', handleConnect);
    sendBtn.addEventListener('click', handleSend);

    // Enter key in input
    manualInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !manualInput.disabled) {
        handleSend();
      }
    });

    // Keyboard shortcut: Ctrl+Enter opens wizard
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (window.CrabWizard) window.CrabWizard.open();
      }
    });
  }

  // ---- Boot ----
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
