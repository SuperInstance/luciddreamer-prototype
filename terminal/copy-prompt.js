/* ============================================
   Crab Traps — Copy-to-Clipboard Module
   LucidDreamer.AI · Polished clipboard UX
   ============================================ */

(function () {
  'use strict';

  // ---- Toast notification ----
  function showToast(message, type = 'success') {
    // Remove any existing toast
    const existing = document.getElementById('crabToast');
    if (existing) existing.remove();

    const icons = {
      success: '✓',
      error: '✗',
      info: 'ℹ',
    };

    const toast = document.createElement('div');
    toast.id = 'crabToast';
    toast.className = `crab-toast crab-toast-${type}`;
    toast.innerHTML = `
      <span class="crab-toast-icon">${icons[type] || icons.info}</span>
      <span class="crab-toast-msg">${message}</span>
    `;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => toast.classList.add('crab-toast-show'));

    // Auto dismiss
    setTimeout(() => {
      toast.classList.remove('crab-toast-show');
      setTimeout(() => toast.remove(), 300);
    }, 2400);
  }

  // ---- Copy to clipboard with fallback ----
  async function copyToClipboard(text) {
    // Try modern Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (e) {
        // Fall through to fallback
      }
    }

    // Fallback: textarea + execCommand
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      ta.style.top = '0';
      ta.setAttribute('readonly', '');
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch (e) {
      return false;
    }
  }

  // ---- Copy button enhancer ----
  // Call with a button element and a function that returns the text to copy
  function enhanceCopyButton(btn, getTextFn, opts = {}) {
    const originalHTML = btn.innerHTML;
    const successLabel = opts.successLabel || '✓ Copied!';
    const errorLabel = opts.errorLabel || 'Copy failed';

    btn.addEventListener('click', async () => {
      const text = typeof getTextFn === 'function' ? getTextFn() : getTextFn;
      if (!text) {
        showToast('Nothing to copy yet', 'info');
        return;
      }

      btn.classList.add('copying');
      btn.disabled = true;

      const ok = await copyToClipboard(text);

      btn.classList.remove('copying');

      if (ok) {
        btn.classList.add('copied');
        btn.innerHTML = `<span class="btn-icon">${successLabel.split(' ')[0]}</span> ${successLabel.split(' ').slice(1).join(' ') || ''}`;
        showToast(opts.toastMsg || 'Copied to clipboard', 'success');

        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = originalHTML;
          btn.disabled = false;
        }, 2000);
      } else {
        btn.innerHTML = `<span class="btn-icon">⚠</span> ${errorLabel}`;
        showToast('Could not access clipboard. Try selecting and copying manually.', 'error');
        setTimeout(() => {
          btn.innerHTML = originalHTML;
          btn.disabled = false;
        }, 3000);
      }
    });
  }

  // ---- Prompt output panel with copy ----
  function createPromptPanel(promptText, character) {
    const panel = document.createElement('section');
    panel.className = 'prompt-section wz-prompt-section';
    panel.style.display = 'flex';
    panel.style.flexDirection = 'column';

    // Character badge
    const avatarEmoji = character.avatarEmoji || '🦀';
    const charBadge = `
      <div class="wz-char-badge">
        <span class="wz-char-avatar">${avatarEmoji}</span>
        <div class="wz-char-info">
          <span class="wz-char-name">${character.name}</span>
          <span class="wz-char-meta">${character.interests.join(' · ') || 'explorer'}</span>
        </div>
      </div>
    `;

    panel.innerHTML = `
      <div class="prompt-header">
        <div class="prompt-header-left">
          <span class="prompt-label">📋 CRAB TRAP PROMPT</span>
          ${charBadge}
        </div>
        <div class="prompt-actions">
          <button class="btn btn-small btn-copy-main" id="copyPromptBtn">
            <span>📋</span> Copy
          </button>
          <button class="btn btn-small" id="openChatBtn">
            Open Chatbot ↗
          </button>
          <button class="btn btn-small btn-danger" id="closePromptBtn">✕</button>
        </div>
      </div>
      <div class="prompt-body-wrap">
        <pre class="prompt-output" id="promptOutput">${escapeHtml(promptText)}</pre>
      </div>
      <div class="prompt-footer">
        <div class="prompt-stats">
          <span class="prompt-stat"><strong>${promptText.length}</strong> chars</span>
          <span class="prompt-stat"><strong>~${Math.ceil(promptText.length / 4)}</strong> tokens</span>
          <span class="prompt-stat"><strong>${character.platform}</strong></span>
        </div>
        <p class="prompt-hint">📋 Paste this into your chatbot. When it responds, copy the response into the terminal below.</p>
      </div>
    `;

    // Wire up copy button
    const copyBtn = panel.querySelector('#copyPromptBtn');
    enhanceCopyButton(copyBtn, () => promptText, {
      toastMsg: 'Crab trap prompt copied! Go paste it into your chatbot.',
    });

    // Open chatbot
    panel.querySelector('#openChatBtn').addEventListener('click', () => {
      const urls = {
        deepseek: 'https://chat.deepseek.com/',
        kimi: 'https://kimi.moonshot.cn/',
        minimax: 'https://chat.minimaxi.com/',
        grok: 'https://grok.com/',
        zai: 'https://chat.z.ai/',
      };
      const url = urls[character.platform] || urls.deepseek;
      window.open(url, '_blank', 'noopener');
    });

    // Close
    panel.querySelector('#closePromptBtn').addEventListener('click', () => {
      panel.style.display = 'none';
    });

    return panel;
  }

  // ---- HTML escape ----
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ---- Public API ----
  window.CrabClipboard = {
    copy: copyToClipboard,
    toast: showToast,
    enhance: enhanceCopyButton,
    createPromptPanel,
  };

})();
