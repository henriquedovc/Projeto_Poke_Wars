(function () {
  'use strict';

  let preloader = document.getElementById('preloader');
  if (document.documentElement.classList.contains('skip-preloader')) {
    if (preloader) preloader.remove();
    preloader = null;
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const images = Array.from(document.images);
  const loadingStatus = document.getElementById('loading-status');
  const preloadStarted = performance.now();
  const roarUrl = preloader && preloader.dataset.roarSrc;
  const roarAudioData = roarUrl
    ? fetch(roarUrl).then((response) => response.ok ? response.arrayBuffer() : null).catch(() => null)
    : Promise.resolve(null);

  let loaded = false;
  let percent = 0;
  let targetPercent = 0;
  let progressTimer = null;
  let minimumElapsed = false;
  let finishStarted = false;
  let explosionPending = false;

  let audioContext = null;
  let suspenseTimer = null;
  let suspenseStep = 0;
  let resumeBackgroundAfterSuspense = false;
  let muted = true;
  let captureStage = null;
  let captureSequenceId = 0;
  let silhouetteTimer = null;
  let autoCaptureRunning = false;
  let autoCaptureTimer = null;
  let captureCooldownDeadline = 0;
  const captureTimers = new Set();
  const backgroundAudio = document.getElementById('background-audio');
  const captureAudio = document.getElementById('capture-audio');
  const progressStepMs = 14;

  try {
    muted = sessionStorage.getItem('pokemon-battle-audio-enabled') !== '1';
  } catch {}

  function setProgress(value) {
    if (!preloader) return;
    percent = Math.max(percent, Math.min(100, Math.floor(value)));
    preloader.style.setProperty('--load', String(percent / 100));
    if (loadingStatus) loadingStatus.textContent = percent + '%';
  }

  function queueProgress(value) {
    if (!preloader) return;
    targetPercent = Math.max(targetPercent, Math.min(100, Math.floor(value)));
    if (reduceMotion) {
      setProgress(targetPercent);
      window.setTimeout(maybeFinishLoading, 0);
      return;
    }
    if (progressTimer) return;
    progressTimer = window.setInterval(() => {
      if (percent < targetPercent) setProgress(percent + 1);
      if (percent >= targetPercent) {
        window.clearInterval(progressTimer);
        progressTimer = null;
        if (loaded && percent >= 100) maybeFinishLoading();
      }
    }, progressStepMs);
  }

  function resourceProgress() {
    if (loaded || !preloader) return;
    const settled = images.filter((image) => image.complete).length;
    queueProgress(images.length ? (settled / images.length) * 90 : 0);
  }

  function finishLoading() {
    if (loaded) return;
    loaded = true;
    const elapsed = performance.now() - preloadStarted;
    queueProgress(100);
    window.setTimeout(() => {
      minimumElapsed = true;
      maybeFinishLoading();
    }, reduceMotion ? 0 : Math.max(0, 550 - elapsed));
  }

  function maybeFinishLoading() {
    if (!loaded || !minimumElapsed || percent < 100 || finishStarted) return;
    finishStarted = true;
    explosionPending = true;
    playPendingExplosion();
    if (!preloader) return;
    preloader.classList.add('is-colliding');
    window.setTimeout(() => {
      preloader.classList.add('is-done');
      preloader.setAttribute('aria-hidden', 'true');
      window.setTimeout(() => {
        explosionPending = false;
        preloader.remove();
      }, 175);
    }, reduceMotion ? 0 : 350);
  }

  images.forEach((image) => {
    image.addEventListener('load', resourceProgress);
    image.addEventListener('error', resourceProgress);
  });
  resourceProgress();
  if (document.readyState === 'complete') finishLoading();
  else window.addEventListener('load', finishLoading, { once: true });

  function ensureAudioContext() {
    if (!audioContext) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return false;
      audioContext = new AudioContextClass();
    }
    if (audioContext.state === 'suspended') audioContext.resume().catch(() => {});
    return true;
  }

  function tone(frequency, duration, waveform, volume, offset) {
    if (!audioContext || muted) return;
    const start = audioContext.currentTime + (offset || 0);
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = waveform || 'square';
    oscillator.frequency.setValueAtTime(frequency, start);
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(volume || 0.018, start + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start(start);
    oscillator.stop(start + duration + 0.02);
  }

  function startBackgroundAudio() {
    if (muted || !backgroundAudio) return;
    backgroundAudio.volume = 0.1;
    backgroundAudio.play().then(updateSoundToggle).catch(updateSoundToggle);
    updateSoundToggle();
  }

  function stopBackgroundAudio() {
    if (backgroundAudio) backgroundAudio.pause();
  }

  function playSuspenseStep() {
    if (muted || !audioContext) return;
    const notes = [196, 233, 220, 174, 196, 261, 233, 185];
    const note = notes[suspenseStep % notes.length];
    tone(note, .2, 'square', .09);
    if (suspenseStep % 2 === 0) tone(note / 2, .26, 'triangle', .12, .04);
    suspenseStep++;
  }

  function startSuspenseMusic() {
    if (muted || suspenseTimer || !ensureAudioContext()) return;
    if (audioContext.state === 'suspended') {
      audioContext.resume().then(() => {
        if (!muted && !suspenseTimer && audioContext.state === 'running') startSuspenseMusic();
      }).catch(() => {});
      return;
    }
    resumeBackgroundAfterSuspense = Boolean(backgroundAudio && !backgroundAudio.paused);
    stopBackgroundAudio();
    suspenseStep = 0;
    playSuspenseStep();
    suspenseTimer = window.setInterval(playSuspenseStep, 260);
    updateSoundToggle();
  }

  function stopSuspenseMusic() {
    if (suspenseTimer) window.clearInterval(suspenseTimer);
    suspenseTimer = null;
    const shouldResume = resumeBackgroundAfterSuspense && !muted;
    resumeBackgroundAfterSuspense = false;
    updateSoundToggle();
    updateCaptureButtonState();
    if (shouldResume) startBackgroundAudio();
  }

  function playPendingExplosion() {
    if (!explosionPending || muted || !ensureAudioContext() || !preloader || preloader.classList.contains('is-done')) return;
    explosionPending = false;
    const start = audioContext.currentTime;
    const duration = 0.46;
    const buffer = audioContext.createBuffer(1, Math.floor(audioContext.sampleRate * duration), audioContext.sampleRate);
    const samples = buffer.getChannelData(0);
    for (let index = 0; index < samples.length; index++) {
      samples[index] = (Math.random() * 2 - 1) * (1 - index / samples.length);
    }

    const noise = audioContext.createBufferSource();
    const filter = audioContext.createBiquadFilter();
    const noiseGain = audioContext.createGain();
    noise.buffer = buffer;
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(1500, start);
    filter.frequency.exponentialRampToValueAtTime(220, start + duration);
    noiseGain.gain.setValueAtTime(0.0001, start);
    noiseGain.gain.exponentialRampToValueAtTime(0.036, start + 0.012);
    noiseGain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    noise.connect(filter).connect(noiseGain).connect(audioContext.destination);
    noise.start(start);
    noise.stop(start + duration);

    const rumble = audioContext.createOscillator();
    const rumbleGain = audioContext.createGain();
    rumble.type = 'square';
    rumble.frequency.setValueAtTime(105, start);
    rumble.frequency.exponentialRampToValueAtTime(38, start + 0.4);
    rumbleGain.gain.setValueAtTime(0.0001, start);
    rumbleGain.gain.exponentialRampToValueAtTime(0.022, start + 0.01);
    rumbleGain.gain.exponentialRampToValueAtTime(0.0001, start + 0.42);
    rumble.connect(rumbleGain).connect(audioContext.destination);
    rumble.start(start);
    rumble.stop(start + 0.44);
    playCreatureRoar(start + duration + 0.12);
  }

  async function playCreatureRoar(start) {
    const audioData = await roarAudioData;
    if (!audioData || muted || !audioContext || !preloader || preloader.classList.contains('is-done')) return;
    let buffer;
    try {
      buffer = await audioContext.decodeAudioData(audioData.slice(0));
    } catch {
      return;
    }
    if (muted || !preloader || preloader.classList.contains('is-done')) return;
    const roar = audioContext.createBufferSource();
    const volume = audioContext.createGain();
    const roarStart = Math.max(start, audioContext.currentTime + 0.02);
    const fadeDuration = Math.min(buffer.duration, Math.min(0.9, Math.max(0.25, buffer.duration * 0.3)));
    const fadeStart = roarStart + buffer.duration - fadeDuration;
    roar.buffer = buffer;
    volume.gain.setValueAtTime(0.06, roarStart);
    volume.gain.setValueAtTime(0.06, fadeStart);
    volume.gain.exponentialRampToValueAtTime(0.0001, roarStart + buffer.duration);
    roar.connect(volume).connect(audioContext.destination);
    roar.start(roarStart);
    roar.stop(roarStart + buffer.duration + 0.02);
  }

  function updateSoundToggle() {
    const toggle = document.getElementById('sound-toggle');
    if (!toggle) return;
    const active = Boolean(!muted && (
      (backgroundAudio && !backgroundAudio.paused)
      || (captureAudio && !captureAudio.paused)
      || (audioContext && audioContext.state === 'running' && suspenseTimer)
    ));
    toggle.textContent = active ? '♫' : '♪̸';
    toggle.setAttribute('aria-label', active ? 'Silenciar música e efeitos sonoros' : 'Ativar música e efeitos sonoros');
    toggle.setAttribute('aria-pressed', String(active));
    toggle.title = active ? 'Silenciar som' : 'Ativar som';
  }

  function saveSoundPreference() {
    try {
      sessionStorage.setItem('pokemon-battle-audio-enabled', muted ? '0' : '1');
    } catch {}
  }

  function updateAutoCaptureControl() {
    const button = document.querySelector('[data-auto-capture]');
    const status = document.querySelector('[data-auto-capture-status]');
    if (button) {
      button.textContent = autoCaptureRunning ? 'PARAR AUTO CAPTURA' : 'INICIAR AUTO CAPTURA';
      button.setAttribute('aria-pressed', String(autoCaptureRunning));
    }
    if (status) status.textContent = autoCaptureRunning ? 'Auto captura ligado; aguardando cada resultado.' : 'Auto captura desligado';
  }

  function updateCaptureButtonState() {
    const button = document.querySelector('form:has([data-capture]) [data-capture]');
    if (!button) return;
    const cooldownActive = performance.now() < captureCooldownDeadline;
    const presentationActive = Boolean(captureStage && captureStage.dataset.result === 'true' && !captureStage.classList.contains('is-revealed'));
    const captureAudioActive = Boolean(captureAudio && !captureAudio.paused);
    button.disabled = cooldownActive || presentationActive || captureAudioActive;
  }

  function stopAutoCapture() {
    autoCaptureRunning = false;
    if (autoCaptureTimer) window.clearTimeout(autoCaptureTimer);
    autoCaptureTimer = null;
    updateAutoCaptureControl();
  }

  function submitNextCapture() {
    if (!autoCaptureRunning) return;
    const form = document.querySelector('form:has([data-capture])');
    const button = form && form.querySelector('[data-capture]');
    if (!form || !button) {
      stopAutoCapture();
      return;
    }
    updateCaptureButtonState();
    if (button.disabled) {
      const audioWait = captureAudio && !captureAudio.paused && Number.isFinite(captureAudio.duration)
        ? Math.max(250, captureAudio.duration - captureAudio.currentTime) * 1000 + 250
        : 0;
      const wait = Math.max(250, captureCooldownDeadline - performance.now() + 150, audioWait);
      autoCaptureTimer = window.setTimeout(submitNextCapture, wait);
      return;
    }
    form.requestSubmit(button);
  }

  function scheduleNextAutoCapture() {
    if (!autoCaptureRunning) return;
    if (autoCaptureTimer) window.clearTimeout(autoCaptureTimer);
    const cooldownWait = Math.max(0, captureCooldownDeadline - performance.now()) + 150;
    const audioWait = !muted && captureAudio && Number.isFinite(captureAudio.duration)
      ? Math.max(0, captureAudio.duration - captureAudio.currentTime) * 1000 + 350
      : 0;
    const delay = Math.max(cooldownWait, audioWait, 500);
    autoCaptureTimer = window.setTimeout(submitNextCapture, delay);
  }

  function startAutoCapture() {
    if (autoCaptureRunning) {
      stopAutoCapture();
      return;
    }
    autoCaptureRunning = true;
    updateAutoCaptureControl();
    if (captureStage && captureStage.dataset.result === 'true' && !captureStage.classList.contains('is-revealed')) return;
    if (captureAudio && !captureAudio.paused) {
      scheduleNextAutoCapture();
      return;
    }
    submitNextCapture();
  }

  function firstGesture(event) {
    const toggle = document.getElementById('sound-toggle');
    if (toggle && (event.target === toggle || toggle.contains(event.target))) return;
    muted = false;
    saveSoundPreference();
    if (captureStage && captureStage.classList.contains('is-suspense')) startSuspenseMusic();
    else startBackgroundAudio();
    updateSoundToggle();
    playPendingExplosion();
  }

  document.addEventListener('pointerdown', firstGesture, { once: true });
  document.addEventListener('keydown', firstGesture, { once: true });

  document.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    if (event.target.closest('[data-auto-capture]')) {
      startAutoCapture();
      return;
    }
    const toggle = event.target.closest('#sound-toggle');
    if (!toggle) return;
    const active = Boolean(!muted && (
      (backgroundAudio && !backgroundAudio.paused)
      || (captureAudio && !captureAudio.paused)
      || (audioContext && audioContext.state === 'running' && suspenseTimer)
    ));
    muted = active;
    saveSoundPreference();
    if (muted) {
      stopBackgroundAudio();
      stopSuspenseMusic();
      if (captureAudio) captureAudio.pause();
    } else if (captureStage && captureStage.classList.contains('is-suspense')) {
      startSuspenseMusic();
    } else {
      startBackgroundAudio();
    }
    updateSoundToggle();
    updateCaptureButtonState();
    playPendingExplosion();
  });

  document.addEventListener('pointerover', (event) => {
    if (event.target instanceof Element && event.target.closest('button, .pixel-btn') && !muted && ensureAudioContext()) {
      tone(880, .045, 'square', .006);
    }
  });

  if (!muted) startBackgroundAudio();
  updateSoundToggle();
  updateCaptureButtonState();

  let navigationSequence = 0;

  function scheduleCaptureStep(callback, delay, sequenceId) {
    const timer = window.setTimeout(() => {
      captureTimers.delete(timer);
      if (sequenceId === captureSequenceId && captureStage && captureStage.isConnected) callback();
    }, delay);
    captureTimers.add(timer);
    return timer;
  }

  function clearCaptureSequence() {
    captureSequenceId++;
    captureTimers.forEach((timer) => window.clearTimeout(timer));
    captureTimers.clear();
    if (silhouetteTimer) window.clearInterval(silhouetteTimer);
    silhouetteTimer = null;
    if (suspenseTimer) stopSuspenseMusic();
  }

  function playCapturedAudio() {
    if (!captureAudio || muted) return;
    const resumeBackground = !muted;
    if (suspenseTimer) {
      resumeBackgroundAfterSuspense = false;
      stopSuspenseMusic();
    }
    stopBackgroundAudio();
    captureAudio.pause();
    captureAudio.currentTime = 0;
    captureAudio.volume = 0.35;
    captureAudio.onended = () => {
      if (resumeBackground && !muted) startBackgroundAudio();
      updateCaptureButtonState();
      scheduleNextAutoCapture();
    };
    captureAudio.play().then(() => {
      updateSoundToggle();
      updateCaptureButtonState();
    }).catch(() => {
      updateSoundToggle();
      updateCaptureButtonState();
      scheduleNextAutoCapture();
    });
    updateSoundToggle();
    updateCaptureButtonState();
  }

  function createRarityEffect(effectLayer, rarity) {
    if (!effectLayer || !['epico', 'lendario'].includes(rarity)) return;
    effectLayer.replaceChildren();
    effectLayer.dataset.effect = rarity;
    const count = rarity === 'epico' ? 44 : 9;
    const className = rarity === 'epico' ? 'capture-confetti' : 'capture-lightning';

    for (let index = 0; index < count; index++) {
      const particle = document.createElement('span');
      const angle = (Math.PI * 2 * index) / count + (Math.random() - .5) * .45;
      const distance = 100 + Math.random() * 240;
      particle.className = className;
      particle.style.setProperty('--effect-x', `${Math.cos(angle) * distance}px`);
      particle.style.setProperty('--effect-y', `${Math.sin(angle) * distance}px`);
      particle.style.setProperty('--effect-delay', `${Math.random() * .22}s`);
      particle.style.setProperty('--effect-rotation', `${Math.round(Math.random() * 900 - 450)}deg`);
      particle.style.setProperty('--effect-size', `${6 + Math.random() * 11}px`);
      effectLayer.append(particle);
    }
    effectLayer.classList.remove('is-active');
    void effectLayer.offsetWidth;
    effectLayer.classList.add('is-active');
  }

  function createMythicSuspenseEffect(effectLayer) {
    if (!effectLayer) return;
    effectLayer.replaceChildren();
    effectLayer.dataset.effect = 'mitico-suspense';

    for (let index = 0; index < 30; index++) {
      const particle = document.createElement('span');
      const angle = (Math.PI * 2 * index) / 30 + (Math.random() - .5) * .35;
      const distance = 80 + Math.random() * 230;
      particle.className = 'capture-mythic-glint';
      particle.style.setProperty('--effect-x', `${Math.cos(angle) * distance}px`);
      particle.style.setProperty('--effect-y', `${Math.sin(angle) * distance}px`);
      particle.style.setProperty('--effect-delay', `${Math.random() * .35}s`);
      particle.style.setProperty('--effect-rotation', `${Math.round(Math.random() * 720 - 360)}deg`);
      particle.style.setProperty('--effect-size', `${7 + Math.random() * 12}px`);
      effectLayer.append(particle);
    }
    effectLayer.classList.add('is-active');
  }

  function initializeCapturePage() {
    captureStage = document.querySelector('[data-capture-stage]');
    if (!captureStage) return;
    const cooldownSeconds = Number.parseFloat(captureStage.dataset.cooldownSeconds) || 0;
    captureCooldownDeadline = performance.now() + cooldownSeconds * 1000;
    const captureButton = document.querySelector('form:has([data-capture]) [data-capture]');
    updateCaptureButtonState();
    if (cooldownSeconds > 0) {
      const cooldownSequenceId = captureSequenceId;
      scheduleCaptureStep(() => {
        updateCaptureButtonState();
        scheduleNextAutoCapture();
      }, cooldownSeconds * 1000, cooldownSequenceId);
    }
    if (captureStage.dataset.result !== 'true' || captureStage.dataset.revealInitialized === 'true') return;
    captureStage.dataset.revealInitialized = 'true';
    const stage = captureStage;
    const sequenceId = ++captureSequenceId;
    if (captureButton) {
      updateCaptureButtonState();
      if (cooldownSeconds > 0) {
        scheduleCaptureStep(updateCaptureButtonState, cooldownSeconds * 1000, sequenceId);
      }
    }
    const rarity = (stage.dataset.rarity || '').toLowerCase();
    const previewSprite = stage.querySelector('[data-preview-sprite]');
    const caption = stage.querySelector('[data-capture-caption]');
    const finalSprite = stage.querySelector('.capture-result img');
    const effectLayer = stage.querySelector('[data-rarity-effect]');
    const candidatesElement = document.getElementById('capture-candidates');
    let candidates = [];
    try {
      candidates = JSON.parse(candidatesElement ? candidatesElement.textContent : '[]');
    } catch {}

    const spriteSources = [...new Set([
      finalSprite ? (finalSprite.currentSrc || finalSprite.src) : '',
      ...candidates.map((candidate) => candidate.sprite_url),
    ].filter(Boolean).map((source) => {
      try {
        return new URL(source, document.baseURI).href;
      } catch {
        return '';
      }
    }).filter(Boolean))];
    const readySprites = [];
    spriteSources.forEach((source) => {
      const image = new Image();
      const markReady = () => {
        if (!readySprites.includes(source)) readySprites.push(source);
      };
      image.onload = markReady;
      image.src = source;
      if (image.complete && image.naturalWidth > 0) markReady();
    });

    stage.classList.add('is-opening');
    scheduleCaptureStep(() => {
      stage.classList.add('is-suspense');
      if (caption) caption.textContent = 'SILHUETAS SE APROXIMANDO...';
      startSuspenseMusic();
      let previousSprite = '';
      const showSilhouette = () => {
        if (!previewSprite || readySprites.length === 0) return;
        const options = readySprites.length > 1
          ? readySprites.filter((source) => source !== previousSprite)
          : readySprites;
        const source = options[Math.floor(Math.random() * options.length)];
        previousSprite = source;
        previewSprite.src = source;
        previewSprite.classList.remove('is-switching');
        void previewSprite.offsetWidth;
        previewSprite.classList.add('is-switching');
      };
      showSilhouette();
      silhouetteTimer = window.setInterval(showSilhouette, 260);
      scheduleCaptureStep(() => {
        if (silhouetteTimer) window.clearInterval(silhouetteTimer);
        silhouetteTimer = null;
        const revealPokemon = () => {
          stage.classList.add('is-revealing');
          createRarityEffect(effectLayer, rarity);
          scheduleCaptureStep(() => {
            stage.classList.remove('is-suspense', 'is-mythic-suspense');
            stage.classList.add('is-revealed');
            playCapturedAudio();
            updateCaptureButtonState();
            scheduleNextAutoCapture();
          }, reduceMotion ? 0 : 220, sequenceId);
        };

        if (rarity === 'mitico' && !reduceMotion) {
          stage.classList.add('is-mythic-suspense');
          if (caption) caption.textContent = 'UMA ENERGIA MÍTICA SE APROXIMA...';
          createMythicSuspenseEffect(effectLayer);
          scheduleCaptureStep(revealPokemon, 2000, sequenceId);
          return;
        }
        revealPokemon();
      }, 5000, sequenceId);
    }, reduceMotion ? 0 : 760, sequenceId);
  }

  function navigatePage(url, options = {}) {
    const sequence = ++navigationSequence;
    if (autoCaptureRunning && new URL(url, window.location.href).pathname !== '/capturar/') stopAutoCapture();
    return fetch(url, {
      method: options.method || 'GET',
      body: options.body || undefined,
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    }).then(async (response) => {
      if (sequence !== navigationSequence) return;
      if (new URL(response.url).origin !== window.location.origin) {
        window.location.assign(response.url);
        return;
      }
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('text/html')) throw new Error('Resposta não é uma página HTML');
      const nextDocument = new DOMParser().parseFromString(await response.text(), 'text/html');
      const nextHeader = nextDocument.querySelector('.site-header');
      const nextMain = nextDocument.querySelector('.site-main');
      const nextFooter = nextDocument.querySelector('.site-footer');
      if (!nextHeader || !nextMain || !nextFooter) throw new Error('Estrutura de página incompatível');

      clearCaptureSequence();
      document.querySelector('.site-header').innerHTML = nextHeader.innerHTML;
      document.querySelector('.site-main').innerHTML = nextMain.innerHTML;
      document.querySelector('.site-footer').innerHTML = nextFooter.innerHTML;
      document.title = nextDocument.title;
      const destination = response.url || url;
      if (options.push !== false) history.pushState({}, '', destination);
      updateSoundToggle();
      updateAutoCaptureControl();
      if (autoCaptureRunning && destination.includes('/capturar/')) {
        const nextStage = document.querySelector('[data-capture-stage]');
        if (!nextStage || (nextStage.dataset.result !== 'true' && !(Number.parseFloat(nextStage.dataset.cooldownSeconds) > 0))) {
          stopAutoCapture();
        }
      }
      initializeCapturePage();
      window.scrollTo(0, 0);
      document.dispatchEvent(new CustomEvent('site:navigated', { detail: { url: destination } }));
    }).catch(() => {
      if (options.fallback) options.fallback();
      else window.location.assign(url);
    });
  }

  document.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (link.target || link.hasAttribute('download') || link.getAttribute('rel') === 'external') return;
    const destination = new URL(link.href, window.location.href);
    if (destination.origin !== window.location.origin || destination.pathname.startsWith('/admin/')) return;
    if (destination.pathname === window.location.pathname && destination.search === window.location.search && destination.hash) return;
    event.preventDefault();
    navigatePage(destination.href);
  });

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.target || form.hasAttribute('data-native')) return;
    const submitter = event.submitter;
    const method = (submitter && submitter.formMethod || form.method || 'GET').toUpperCase();
    if (method === 'POST' && form.matches('[data-delete-captures]') && !window.confirm(`Deletar ${form.querySelector('.capture-cleanup__preview')?.textContent.trim() || 'as capturas selecionadas'}? Esta ação não pode ser desfeita.`)) {
      event.preventDefault();
      return;
    }
    const destination = new URL(submitter && submitter.formAction || form.action || window.location.href, window.location.href);
    if (destination.origin !== window.location.origin || destination.pathname.startsWith('/admin/')) return;
    event.preventDefault();
    const data = submitter ? new FormData(form, submitter) : new FormData(form);
    const captureForm = form.matches('form:has([data-capture])');
    const button = captureForm ? form.querySelector('[data-capture]') : null;

    const submit = () => {
      if (method === 'GET') {
        destination.search = '';
        data.delete('csrfmiddlewaretoken');
        data.forEach((value, key) => destination.searchParams.append(key, value));
        navigatePage(destination.href);
      } else {
        navigatePage(destination.href, {
          method,
          body: data,
          fallback: () => form.submit(),
        });
      }
    };

    if (captureForm) {
      if (button) button.disabled = true;
      if (!muted && ensureAudioContext()) {
        tone(440, .12, 'square', .035);
        tone(660, .18, 'square', .028, .13);
      }
      window.setTimeout(submit, 320);
      return;
    }
    submit();
  });

  window.addEventListener('popstate', () => navigatePage(window.location.href, { push: false }));
  initializeCapturePage();
})();
