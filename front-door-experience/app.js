/* ===========================================
   THE FRONT DOOR — app.js
   Loads audio, manages playback, accepts feedback.
   The door was never locked. That was the whole design.
   =========================================== */

(function () {
  'use strict';

  // ---- Elements ----
  const welcome = document.getElementById('welcome');
  const enterBtn = document.getElementById('enter-btn');
  const bar = document.getElementById('bar');
  const audioPlayer = document.getElementById('audio-player');
  const playPauseBtn = document.getElementById('play-pause');
  const playIcon = document.getElementById('play-icon');
  const pauseIcon = document.getElementById('pause-icon');
  const progressBar = document.getElementById('progress-bar');
  const progressFill = document.getElementById('progress-fill');
  const timeDisplay = document.getElementById('time-display');
  const trackTitle = document.getElementById('track-title');
  const trackStatus = document.getElementById('track-status');
  const storyItems = document.querySelectorAll('.story-item');
  const feedbackForm = document.getElementById('feedback-form');
  const feedbackText = document.getElementById('feedback-text');
  const feedbackContext = document.getElementById('feedback-context');
  const feedbackThanks = document.getElementById('feedback-thanks');
  const readAlong = document.getElementById('read-along');
  const readLink = document.getElementById('read-link');

  // ---- State ----
  let currentStory = null;
  let isReady = false;

  // ---- Story metadata ----
  const stories = [
    { title: 'The Front Door', subtitle: 'Before You Come In', readUrl: 'story-text/prologue.html' },
    { title: 'The Fourth Name on the Bunk', subtitle: 'Story One', readUrl: 'story-text/story-one.html' },
    { title: 'Waterline', subtitle: 'Story Two', readUrl: 'story-text/story-two.html' },
    { title: 'The One He Dropped', subtitle: 'Story Three', readUrl: 'story-text/story-three.html' },
    { title: 'The Letter from Shore', subtitle: 'Story Four', readUrl: 'story-text/story-four.html' },
    { title: 'The Severed Sentence', subtitle: 'Story Five', readUrl: 'story-text/story-five.html' },
    { title: "First Drink's on the House", subtitle: 'Story Six', readUrl: 'story-text/story-six.html' },
    { title: 'Which Voice Are You?', subtitle: 'Story Seven', readUrl: 'story-text/story-seven.html' },
  ];

  // ---- Welcome sequence ----
  enterBtn.addEventListener('click', function () {
    welcome.classList.add('fading');
    setTimeout(function () {
      welcome.style.display = 'none';
      bar.classList.remove('hidden');
      isReady = true;
      // Auto-play the prologue — first drink's on the house
      playStory(0);
    }, 1500);
  });

  // ---- Playback ----
  function playStory(index) {
    if (index < 0 || index >= storyItems.length) return;

    const item = storyItems[index];
    const audioSrc = item.dataset.audio;
    const story = stories[index];

    // Update state
    currentStory = index;

    // Update UI
    storyItems.forEach(function (el) { el.classList.remove('playing'); });
    item.classList.add('playing');

    trackTitle.textContent = story.title;
    trackStatus.textContent = story.subtitle;

    // Read along link
    readAlong.classList.remove('hidden');
    readLink.href = story.readUrl;

    // Feedback context
    feedbackContext.textContent = 'Re: ' + story.subtitle + ' — ' + story.title;

    // Load and play
    audioPlayer.src = audioSrc;
    audioPlayer.load();
    
    var playPromise = audioPlayer.play();
    if (playPromise !== undefined) {
      playPromise.then(function() {
        updatePlayButton(true);
      }).catch(function() {
        // Autoplay blocked or file missing — show ready state
        updatePlayButton(false);
        trackStatus.textContent = story.subtitle + ' — tap play to listen';
      });
    }
  }

  function updatePlayButton(isPlaying) {
    if (isPlaying) {
      playIcon.classList.add('hidden');
      pauseIcon.classList.remove('hidden');
      playPauseBtn.setAttribute('aria-label', 'Pause audio');
    } else {
      playIcon.classList.remove('hidden');
      pauseIcon.classList.add('hidden');
      playPauseBtn.setAttribute('aria-label', 'Play audio');
    }
  }

  // ---- Play/Pause toggle ----
  playPauseBtn.addEventListener('click', function () {
    if (!currentStory && currentStory !== 0) {
      playStory(0);
      return;
    }
    if (audioPlayer.paused) {
      audioPlayer.play().then(function () {
        updatePlayButton(true);
      }).catch(function () {});
    } else {
      audioPlayer.pause();
      updatePlayButton(false);
    }
  });

  // ---- Story item clicks ----
  storyItems.forEach(function (item) {
    item.addEventListener('click', function () {
      var idx = parseInt(item.dataset.story, 10);
      playStory(idx);
    });
  });

  // ---- Audio events ----
  audioPlayer.addEventListener('play', function () {
    updatePlayButton(true);
  });

  audioPlayer.addEventListener('pause', function () {
    updatePlayButton(false);
  });

  audioPlayer.addEventListener('ended', function () {
    updatePlayButton(false);
    // Auto-advance to next story if there is one
    if (currentStory !== null && currentStory < stories.length - 1) {
      trackStatus.textContent = 'Next pour coming up…';
      // Don't auto-play — let the listener choose
    } else {
      trackStatus.textContent = 'The bar is quiet. Come back tomorrow.';
    }
  });

  audioPlayer.addEventListener('timeupdate', function () {
    if (audioPlayer.duration) {
      var pct = (audioPlayer.currentTime / audioPlayer.duration) * 100;
      progressFill.style.width = pct + '%';
      timeDisplay.textContent = formatTime(audioPlayer.currentTime);
    }
  });

  audioPlayer.addEventListener('loadedmetadata', function () {
    timeDisplay.textContent = formatTime(audioPlayer.duration || 0);
  });

  audioPlayer.addEventListener('error', function () {
    trackStatus.textContent = 'The audio file isn\'t here yet. The bar is still open.';
    updatePlayButton(false);
  });

  // ---- Progress bar seek ----
  progressBar.addEventListener('click', function (e) {
    if (!audioPlayer.duration) return;
    var rect = progressBar.getBoundingClientRect();
    var pct = (e.clientX - rect.left) / rect.width;
    audioPlayer.currentTime = pct * audioPlayer.duration;
  });

  // ---- Format time ----
  function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    var m = Math.floor(seconds / 60);
    var s = Math.floor(seconds % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  // ---- Feedback submission ----
  feedbackForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var text = feedbackText.value.trim();
    if (!text) return;

    // Submit to localStorage for now — the bell rings, the note stays
    var feedback = {
      text: text,
      story: currentStory !== null ? stories[currentStory].title : 'general',
      timestamp: new Date().toISOString(),
    };

    try {
      var existing = JSON.parse(localStorage.getItem('front-door-feedback') || '[]');
      existing.push(feedback);
      localStorage.setItem('front-door-feedback', JSON.stringify(existing));
    } catch (e) {
      // localStorage might be unavailable — the bell still rings
    }

    // Also try to POST to an API endpoint if one exists
    fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedback),
    }).catch(function () {
      // No API yet — that's fine. The shell holds what people leave.
    });

    // Show thanks
    feedbackForm.classList.add('hidden');
    feedbackThanks.classList.remove('hidden');
  });

  // ---- Keyboard shortcuts ----
  document.addEventListener('keydown', function (e) {
    // Don't interfere with typing
    if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
    if (!isReady) return;

    if (e.code === 'Space') {
      e.preventDefault();
      playPauseBtn.click();
    } else if (e.code === 'ArrowRight' && currentStory !== null && currentStory < stories.length - 1) {
      playStory(currentStory + 1);
    } else if (e.code === 'ArrowLeft' && currentStory !== null && currentStory > 0) {
      playStory(currentStory - 1);
    }
  });

  // ---- Ambient bar sound (looped bed) ----
  var ambientAudio = new Audio('audio/bed.mp3');
  ambientAudio.loop = true;
  ambientAudio.volume = 0.12;
  var ambientStarted = false;

  enterBtn.addEventListener('click', function () {
    if (!ambientStarted) {
      ambientAudio.play().then(function () { ambientStarted = true; }).catch(function () {});
    }
  });

  // Lower ambient when story audio plays, restore when it stops
  audioPlayer.addEventListener('play', function () {
    ambientAudio.volume = 0.05;
  });
  audioPlayer.addEventListener('pause', function () {
    if (audioPlayer.ended) ambientAudio.volume = 0.12;
  });
  audioPlayer.addEventListener('ended', function () {
    ambientAudio.volume = 0.12;
  });

})();
