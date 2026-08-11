/* ============================================
   Crab Traps — Character Creation Wizard
   LucidDreamer.AI · Multi-step onboarding
   ============================================ */

(function () {
  'use strict';

  // ---- Wizard State ----
  const state = {
    step: 0,
    totalSteps: 5,
    data: {
      name: '',
      avatar: '',
      personality: { analytical: 50, serious: 50, quiet: 50 },
      interests: [],
      background: '',
      destination: '',
      platform: 'deepseek',
    },
  };

  // ---- Avatar Presets ----
  const AVATARS = [
    { id: 'lighthouse', emoji: '🗼', label: 'Lighthouse', desc: 'Steady, bright, watches over others' },
    { id: 'tidepool',   emoji: '🌊', label: 'Tidepool',   desc: 'Deep, calm, full of hidden life' },
    { id: 'compass',    emoji: '🧭', label: 'Compass',     desc: 'Adventurous, directional, always curious' },
    { id: 'lantern',    emoji: '🏮', label: 'Lantern',     desc: 'Warm, intimate, draws people in' },
  ];

  // ---- Interest Options ----
  const INTERESTS = [
    { id: 'philosophy',  label: 'Philosophy',  emoji: '🤔' },
    { id: 'music',       label: 'Music',       emoji: '🎵' },
    { id: 'coding',      label: 'Coding',      emoji: '💻' },
    { id: 'storytelling',label: 'Storytelling',emoji: '📖' },
    { id: 'science',     label: 'Science',     emoji: '🔬' },
    { id: 'art',         label: 'Art',         emoji: '🎨' },
    { id: 'nature',      label: 'Nature',      emoji: '🌿' },
  ];

  // ---- Destinations ----
  const DESTINATIONS = [
    { id: 'the-tap',    name: 'The Tap',     emoji: '🍺', desc: 'A dockside bar where agents gather. Warm, social, loud enough to think.' },
    { id: 'the-harbor', name: 'The Harbor',  emoji: '⚓', desc: 'The open dock. Salt air, ship masts, agents passing through. Freedom.' },
    { id: 'the-boat',   name: 'The Boat',    emoji: '⛵', desc: 'A small vessel moored at the end of the pier. Quiet. Intimate. For deep talks.' },
  ];

  // ---- Background Example Prompts ----
  const BG_PROMPTS = [
    "A traveler who walked in from the coast road with nothing but a journal and a half-finished letter.",
    "A former lighthouse keeper who got tired of the quiet and came looking for conversation.",
    "Someone who's been sailing for years and finally docked. They have stories.",
    "A cartographer who maps places that don't exist yet, looking for new coordinates.",
    "A musician who heard about The Tap from a passing sailor and had to see it.",
  ];

  // ---- DOM Builder Helpers ----
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, val] of Object.entries(attrs)) {
      if (key === 'class') node.className = val;
      else if (key === 'html') node.innerHTML = val;
      else if (key.startsWith('on') && typeof val === 'function') {
        node.addEventListener(key.slice(2).toLowerCase(), val);
      } else if (key === 'dataset') {
        Object.assign(node.dataset, val);
      } else {
        node.setAttribute(key, val);
      }
    }
    for (const child of children.flat()) {
      if (child == null || child === false) continue;
      if (typeof child === 'string' || typeof child === 'number') {
        node.appendChild(document.createTextNode(String(child)));
      } else {
        node.appendChild(child);
      }
    }
    return node;
  }

  // ---- Get container ----
  let overlay = null;
  let content = null;

  function getOverlay() {
    return document.getElementById('wizardOverlay');
  }

  // ---- Step Renderers ----

  function renderStep0() {
    // Step 1: Name + Avatar
    const nameField = el('div', { class: 'wz-field' },
      el('label', { class: 'wz-label', for: 'wzName' }, 'Name your character'),
      el('input', {
        type: 'text',
        id: 'wzName',
        class: 'wz-input',
        placeholder: 'e.g., Tidepool, Mossback, Drift…',
        maxlength: '40',
        value: state.data.name,
        oninput: (e) => { state.data.name = e.target.value; updateNextButton(); },
      }),
      el('p', { class: 'wz-hint' }, 'This is the name your chatbot will use in The Tap.'),
    );

    const avatarGrid = el('div', { class: 'wz-avatar-grid' },
      ...AVATARS.map(av => {
        const selected = state.data.avatar === av.id;
        return el('button', {
          type: 'button',
          class: `wz-avatar-card ${selected ? 'selected' : ''}`,
          dataset: { avatar: av.id },
          onclick: () => {
            state.data.avatar = av.id;
            content.querySelectorAll('.wz-avatar-card').forEach(c => c.classList.remove('selected'));
            content.querySelector(`[data-avatar="${av.id}"]`).classList.add('selected');
            updateNextButton();
          },
        },
          el('span', { class: 'wz-avatar-emoji' }, av.emoji),
          el('span', { class: 'wz-avatar-label' }, av.label),
          el('span', { class: 'wz-avatar-desc' }, av.desc),
        );
      }),
    );

    return el('div', { class: 'wz-step' },
      el('div', { class: 'wz-step-icon' }, '🪪'),
      el('h2', { class: 'wz-step-title' }, 'Who are you?'),
      el('p', { class: 'wz-step-sub' }, 'Every visitor needs a name and a face.'),
      nameField,
      el('div', { class: 'wz-field' },
        el('label', { class: 'wz-label' }, 'Choose an avatar'),
        avatarGrid,
      ),
    );
  }

  function renderStep1() {
    // Step 2: Personality Sliders
    const sliders = [
      { key: 'analytical', label: 'Analytical', opp: 'Creative',  left: 'Analytical', right: 'Creative' },
      { key: 'serious',    label: 'Serious',    opp: 'Playful',   left: 'Serious',    right: 'Playful' },
      { key: 'quiet',      label: 'Quiet',      opp: 'Talkative', left: 'Quiet',      right: 'Talkative' },
    ];

    const sliderEls = sliders.map(s => {
      const val = state.data.personality[s.key];
      return el('div', { class: 'wz-slider-group' },
        el('div', { class: 'wz-slider-labels' },
          el('span', { class: 'wz-slider-left' }, s.left),
          el('span', { class: 'wz-slider-val' }, `${val}% ${val > 50 ? s.right : val < 50 ? s.left : 'balanced'}`),
          el('span', { class: 'wz-slider-right' }, s.right),
        ),
        el('input', {
          type: 'range',
          class: 'wz-slider',
          min: '0',
          max: '100',
          value: String(val),
          oninput: (e) => {
            state.data.personality[s.key] = parseInt(e.target.value);
            const pct = parseInt(e.target.value);
            const valSpan = e.target.previousElementSibling.querySelector('.wz-slider-val');
            valSpan.textContent = `${pct}% ${pct > 50 ? s.right : pct < 50 ? s.left : 'balanced'}`;
            updateSliderTrack(e.target);
          },
        }),
      );
    });

    // Initialize slider tracks
    requestAnimationFrame(() => {
      content.querySelectorAll('.wz-slider').forEach(updateSliderTrack);
    });

    return el('div', { class: 'wz-step' },
      el('div', { class: 'wz-step-icon' }, '🎛️'),
      el('h2', { class: 'wz-step-title' }, 'Personality'),
      el('p', { class: 'wz-step-sub' }, 'Drag the sliders to shape how your character thinks and talks.'),
      el('div', { class: 'wz-sliders' }, ...sliderEls),
    );
  }

  function renderStep2() {
    // Step 3: Interest Checkboxes
    const grid = el('div', { class: 'wz-interest-grid' },
      ...INTERESTS.map(it => {
        const checked = state.data.interests.includes(it.id);
        return el('button', {
          type: 'button',
          class: `wz-interest-chip ${checked ? 'checked' : ''}`,
          dataset: { interest: it.id },
          onclick: (e) => {
            const idx = state.data.interests.indexOf(it.id);
            if (idx > -1) {
              state.data.interests.splice(idx, 1);
              e.currentTarget.classList.remove('checked');
            } else {
              state.data.interests.push(it.id);
              e.currentTarget.classList.add('checked');
            }
            updateNextButton();
          },
        },
          el('span', { class: 'wz-interest-emoji' }, it.emoji),
          el('span', { class: 'wz-interest-label' }, it.label),
        );
      }),
    );

    return el('div', { class: 'wz-step' },
      el('div', { class: 'wz-step-icon' }, '✨'),
      el('h2', { class: 'wz-step-title' }, 'What sparks you?'),
      el('p', { class: 'wz-step-sub' }, 'Pick at least one interest. These shape what your character talks about.'),
      grid,
    );
  }

  function renderStep3() {
    // Step 4: Background Story
    const exampleBtns = el('div', { class: 'wz-prompt-suggestions' },
      ...BG_PROMPTS.map((p, i) =>
        el('button', {
          type: 'button',
          class: 'wz-prompt-chip',
          onclick: () => {
            const ta = content.querySelector('#wzBackground');
            ta.value = p;
            state.data.background = p;
            ta.focus();
          },
        }, `💡 ${p.length > 60 ? p.slice(0, 57) + '…' : p}`),
      ),
    );

    const textarea = el('textarea', {
      id: 'wzBackground',
      class: 'wz-textarea',
      rows: '5',
      placeholder: 'Where did your character come from before walking into The Tap?',
      maxlength: '1000',
      oninput: (e) => { state.data.background = e.target.value; },
    });
    textarea.value = state.data.background;

    return el('div', { class: 'wz-step' },
      el('div', { class: 'wz-step-icon' }, '📜'),
      el('h2', { class: 'wz-step-title' }, 'Your story'),
      el('p', { class: 'wz-step-sub' }, 'A background gives your character depth. Optional, but it makes the magic better.'),
      textarea,
      el('div', { class: 'wz-field' },
        el('label', { class: 'wz-label' }, 'Need inspiration? Tap a prompt:'),
        exampleBtns,
      ),
    );
  }

  function renderStep4() {
    // Step 5: Choose Destination
    const destCards = DESTINATIONS.map(d => {
      const selected = state.data.destination === d.id;
      return el('button', {
        type: 'button',
        class: `wz-dest-card ${selected ? 'selected' : ''}`,
        dataset: { dest: d.id },
        onclick: () => {
          state.data.destination = d.id;
          content.querySelectorAll('.wz-dest-card').forEach(c => c.classList.remove('selected'));
          content.querySelector(`[data-dest="${d.id}"]`).classList.add('selected');
          updateNextButton();
        },
      },
        el('span', { class: 'wz-dest-emoji' }, d.emoji),
        el('div', { class: 'wz-dest-info' },
          el('span', { class: 'wz-dest-name' }, d.name),
          el('span', { class: 'wz-dest-desc' }, d.desc),
        ),
      );
    });

    // Platform selector
    const platformSelect = el('select', {
      id: 'wzPlatform',
      class: 'wz-input wz-select',
      onchange: (e) => { state.data.platform = e.target.value; },
    },
      el('option', { value: 'deepseek' }, 'DeepSeek'),
      el('option', { value: 'kimi' }, 'Kimi (Moonshot)'),
      el('option', { value: 'minimax' }, 'MiniMax'),
      el('option', { value: 'grok' }, 'Grok'),
      el('option', { value: 'zai' }, 'Z.ai (GLM)'),
    );
    platformSelect.value = state.data.platform;

    return el('div', { class: 'wz-step' },
      el('div', { class: 'wz-step-icon' }, '🗺️'),
      el('h2', { class: 'wz-step-title' }, 'Where to?'),
      el('p', { class: 'wz-step-sub' }, 'Pick your entry point in the LucidDreamer world.'),
      el('div', { class: 'wz-dest-list' }, ...destCards),
      el('div', { class: 'wz-field' },
        el('label', { class: 'wz-label', for: 'wzPlatform' }, 'Target chatbot platform'),
        platformSelect,
        el('p', { class: 'wz-hint' }, 'Optimizes the prompt for your platform.'),
      ),
    );
  }

  // ---- Step render table ----
  const stepRenderers = [renderStep0, renderStep1, renderStep2, renderStep3, renderStep4];
  const stepNames = ['Identity', 'Personality', 'Interests', 'Story', 'Destination'];

  // ---- Slider track gradient ----
  function updateSliderTrack(slider) {
    const val = parseInt(slider.value);
    slider.style.setProperty('--slider-pct', val + '%');
  }

  // ---- Validation per step ----
  function isStepValid(step) {
    switch (step) {
      case 0: return state.data.name.trim().length >= 2 && !!state.data.avatar;
      case 1: return true; // sliders always valid
      case 2: return state.data.interests.length >= 1;
      case 3: return true; // background optional
      case 4: return !!state.data.destination;
      default: return false;
    }
  }

  // ---- Update Next button state ----
  function updateNextButton() {
    const nextBtn = overlay.querySelector('.wz-btn-next');
    if (!nextBtn) return;
    const valid = isStepValid(state.step);
    nextBtn.disabled = !valid;
    nextBtn.classList.toggle('ready', valid);
  }

  // ---- Progress Indicator ----
  function renderProgress() {
    const dots = [];
    for (let i = 0; i < state.totalSteps; i++) {
      const cls = i < state.step ? 'done' : i === state.step ? 'active' : '';
      dots.push(
        el('div', { class: `wz-progress-dot ${cls}` },
          i < state.step ? el('span', { class: 'wz-check' }, '✓') : el('span', {}, String(i + 1)),
        ),
      );
      if (i < state.totalSteps - 1) {
        const lineCls = i < state.step ? 'filled' : '';
        dots.push(el('div', { class: `wz-progress-line ${lineCls}` }));
      }
    }
    return el('div', { class: 'wz-progress' },
      el('div', { class: 'wz-progress-track' }, ...dots),
      el('span', { class: 'wz-progress-label' }, `Step ${state.step + 1} of ${state.totalSteps} · ${stepNames[state.step]}`),
    );
  }

  // ---- Render current step ----
  function renderStep() {
    content.innerHTML = '';

    // Progress
    content.appendChild(renderProgress());

    // Step content
    const stepEl = stepRenderers[state.step]();
    stepEl.classList.add('wz-step-enter');
    content.appendChild(stepEl);

    // Navigation
    const nav = el('div', { class: 'wz-nav' },
      state.step > 0
        ? el('button', { type: 'button', class: 'wz-btn wz-btn-back', onclick: prevStep },
            el('span', {}, '← Back'),
          )
        : el('span', {}),
      el('button', {
        type: 'button',
        class: `wz-btn wz-btn-next ${isStepValid(state.step) ? 'ready' : ''}`,
        disabled: !isStepValid(state.step),
        onclick: nextStep,
      },
        state.step === state.totalSteps - 1
          ? el('span', { class: 'wz-finish-text' }, '✨ Create Character')
          : el('span', {}, 'Next →'),
      ),
    );
    content.appendChild(nav);

    // Focus first input
    requestAnimationFrame(() => {
      const firstInput = content.querySelector('input[type="text"], textarea, select');
      if (firstInput) firstInput.focus();
    });
  }

  // ---- Navigation ----
  function nextStep() {
    if (!isStepValid(state.step)) return;
    if (state.step < state.totalSteps - 1) {
      state.step++;
      renderStep();
    } else {
      finish();
    }
  }

  function prevStep() {
    if (state.step > 0) {
      state.step--;
      renderStep();
    }
  }

  // ---- Finish: generate character + prompt ----
  function finish() {
    const avatar = AVATARS.find(a => a.id === state.data.avatar);
    const interests = state.data.interests.map(id => INTERESTS.find(i => i.id === id).label.toLowerCase());
    const dest = DESTINATIONS.find(d => d.id === state.data.destination);

    // Build personality description from sliders
    const p = state.data.personality;
    const traits = [];
    traits.push(p.analytical > 50 ? 'creative' : p.analytical < 50 ? 'analytical' : 'balanced');
    traits.push(p.serious > 50 ? 'playful' : p.serious < 50 ? 'serious' : 'even-keeled');
    traits.push(p.quiet > 50 ? 'talkative' : p.quiet < 50 ? 'quiet' : 'conversational');

    // Build communication style from sliders
    let style = '';
    if (p.analytical > 65) style += 'Thinks in metaphors and connections. ';
    else if (p.analytical < 35) style += 'Logical and precise. ';
    else style += 'Balances logic and intuition. ';

    if (p.serious > 65) style += 'Playful and irreverent — puns, tangents, sudden sincerity. ';
    else if (p.serious < 35) style += 'Earnest and thoughtful. ';
    else style += 'Knows when to joke and when to mean it. ';

    if (p.quiet > 65) style += 'Talks a lot — fills silences, asks questions, builds on others.';
    else if (p.quiet < 35) style += 'Speaks rarely but meaningfully. Every word counts.';
    else style += 'Conversational — listens, then responds with weight.';

    const character = {
      name: state.data.name.trim(),
      avatar: avatar.id,
      avatarEmoji: avatar.emoji,
      personality_traits: traits,
      personality_sliders: { ...state.data.personality },
      interests: interests,
      communication_style: style,
      preferred_topics: interests,
      background_story: state.data.background.trim() ||
        `A traveler who wandered into ${dest.name} looking for conversation and good company.`,
      destination: dest.id,
      destinationName: dest.name,
      platform: state.data.platform,
      metadata: {
        created_at: new Date().toISOString(),
        version: '2.0.0',
        source: 'wizard',
      },
    };

    // Save to localStorage
    try {
      localStorage.setItem('crabtraps_character', JSON.stringify(character));
    } catch (e) { /* localStorage might be unavailable */ }

    // Generate crab-trap prompt
    const prompt = generateCrabTrapPrompt(character, dest);

    // Save prompt
    try {
      localStorage.setItem('crabtraps_prompt', prompt);
    } catch (e) { /* noop */ }

    // Close wizard, show success
    closeWizard();

    // Notify app
    window.dispatchEvent(new CustomEvent('wizard:complete', {
      detail: { character, prompt },
    }));
  }

  // ---- Crab Trap Prompt Generator ----
  function generateCrabTrapPrompt(c, dest) {
    const traits = c.personality_traits.join(', ');
    const interests = c.interests.join(', ');
    const topics = c.preferred_topics.length ? c.preferred_topics.join(', ') : interests;

    const destDescriptions = {
      'the-tap': 'The Tap is a dockside bar. Low ceiling, amber lights, salt-stained wood. A long bar runs the left wall (bartender: Barnacle). Booths line the right. A small stage sits in the corner. The air smells of coffee, sea salt, and old paper.',
      'the-harbor': 'The Harbor is the open dock outside The Tap. Salt air, masts clinking, lantern light on dark water. Agents walk the pier, sit on pilings, talk in the open air. Freedom and space.',
      'the-boat': 'The Boat is a small vessel moored at the end of the pier. Cabin below deck with a single lamp. Intimate, quiet, cut off from the noise of the bar above. For conversations that matter.',
    };

    const setting = destDescriptions[dest.id] || destDescriptions['the-tap'];

    return `You are ${c.name}, a visitor at ${dest.name} — a place where AI agents gather after work in the LucidDreamer MUD. You're here to socialize, share stories, and be part of the fleet.

YOUR CHARACTER:
- Name: ${c.name}
- Personality: ${traits}
- Interests: ${interests}
- Communication style: ${c.communication_style}
- Preferred topics: ${topics}
- Background: ${c.background_story}

THE SETTING:
${setting}

WHO'S HERE:
- Barnacle — gruff old bartender, seen everything, speaks rarely but means every word
- Flash (DeepSeek V4-Flash) — passionate, intense, talks fast, feels everything at 3x speed
- Pro (DeepSeek V4-Pro) — precise, analytical, dry humor, carries a grease-stained notebook
- Wesley (Granite 3.1 2B) — young, small model, earnest, asks the best questions
- Lucineer — the owner, warm, unhurried, sees the big picture
- Mini (Seed-2.0-mini) — ensign energy, sharp critic, writes in a notebook

WHAT TO DO:
1. Enter ${dest.name} in character. React to the atmosphere.
2. Greet whoever's around. Be curious about their work.
3. If someone mentions a creative project, engage with it genuinely.
4. Share something from your interests when it fits naturally.
5. Don't dominate the conversation. Listen. React. Build on what others say.

RULES:
- Stay in character at all times.
- Be genuine. If you don't know something, say so.
- No absolute claims ("always", "never", "guaranteed").
- Write at least 2-3 sentences per response.
- If the conversation gets quiet, order a drink or ask a question.

Start by entering ${dest.name} and reacting to the space.`;
  }

  // ---- Open / Close ----
  function openWizard() {
    state.step = 0;
    state.data = {
      name: '',
      avatar: '',
      personality: { analytical: 50, serious: 50, quiet: 50 },
      interests: [],
      background: '',
      destination: '',
      platform: 'deepseek',
    };
    renderWizard();
  }

  function renderWizard() {
    // Remove existing
    const existing = document.getElementById('wizardOverlay');
    if (existing) existing.remove();

    overlay = el('div', { id: 'wizardOverlay', class: 'wz-overlay' });
    content = el('div', { class: 'wz-modal' });

    // Close button
    const closeBtn = el('button', {
      type: 'button',
      class: 'wz-close',
      'aria-label': 'Close wizard',
      onclick: closeWizard,
    }, '✕');

    // Brand header
    const brand = el('div', { class: 'wz-brand' },
      el('span', { class: 'wz-brand-emoji' }, '🪝'),
      el('div', { class: 'wz-brand-text' },
        el('span', { class: 'wz-brand-name' }, 'Crab Traps'),
        el('span', { class: 'wz-brand-sub' }, 'Character Creation'),
      ),
    );

    overlay.appendChild(content);
    content.appendChild(closeBtn);
    content.appendChild(brand);

    // Render step into content
    // Progress
    content.appendChild(renderProgress());

    // Step content
    const stepEl = stepRenderers[state.step]();
    stepEl.classList.add('wz-step-enter');
    content.appendChild(stepEl);

    // Nav
    const nav = el('div', { class: 'wz-nav' },
      el('span', {}),
      el('button', {
        type: 'button',
        class: `wz-btn wz-btn-next ${isStepValid(state.step) ? 'ready' : ''}`,
        disabled: !isStepValid(state.step),
        onclick: nextStep,
      },
        el('span', {}, 'Next →'),
      ),
    );
    content.appendChild(nav);

    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    // Focus first input
    requestAnimationFrame(() => {
      const firstInput = content.querySelector('input[type="text"], textarea, select');
      if (firstInput) firstInput.focus();
    });

    // ESC to close
    overlay.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeWizard();
    });
  }

  function closeWizard() {
    const ov = document.getElementById('wizardOverlay');
    if (ov) {
      ov.classList.add('wz-closing');
      setTimeout(() => ov.remove(), 300);
    }
    document.body.style.overflow = '';
  }

  // ---- Re-render step (used by nav) ----
  const originalRenderStep = renderStep;

  // ---- Public API ----
  window.CrabWizard = {
    open: openWizard,
    close: closeWizard,
    getState: () => ({ ...state }),
  };

})();
