/* 88-key piano keyboard component (A0 = MIDI 21  to  C8 = MIDI 108) */

const NOTE_NAMES = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'];
const WHITE_PCS  = new Set([0, 2, 4, 5, 7, 9, 11]);
const BLACK_PCS  = new Set([1, 3, 6, 8, 10]);

const MIDI_LOW  = 21;   // A0
const MIDI_HIGH = 108;  // C8

const KEY_W  = 24;      // white key width
const KEY_H  = 130;     // white key height
const BK_W   = 14;      // black key width
const BK_H   = 82;      // black key height

function midiToNoteName(midi) {
  const octave = Math.floor(midi / 12) - 1;
  return NOTE_NAMES[midi % 12] + octave;
}

function isWhite(midi) { return WHITE_PCS.has(midi % 12); }

/* ── State ──────────────────────────────────────────────────────────────── */
const pianoState = {
  mode: 'range',         // 'range' | 'favorites' | 'avoids'
  rangeStart: null,
  rangeEnd: null,
  favorites: new Set(),
  avoids: new Set(),
  keys: {},              // midi -> DOM element
  _rangeClicks: 0,
};

/* ── Build keyboard ─────────────────────────────────────────────────────── */
function buildPiano() {
  const container = document.getElementById('piano');
  if (!container) return;

  let whiteIndex = 0;
  const whitePositions = {};

  for (let m = MIDI_LOW; m <= MIDI_HIGH; m++) {
    if (isWhite(m)) {
      whitePositions[m] = whiteIndex;
      whiteIndex++;
    }
  }

  const totalWidth = whiteIndex * KEY_W;
  container.style.width = totalWidth + 'px';
  container.style.height = KEY_H + 'px';

  for (let m = MIDI_LOW; m <= MIDI_HIGH; m++) {
    const el = document.createElement('div');
    el.className = 'piano-key';
    el.dataset.midi = m;
    el.dataset.note = midiToNoteName(m);

    if (isWhite(m)) {
      el.classList.add('white-key');
      el.style.left = (whitePositions[m] * KEY_W) + 'px';
      el.style.width = KEY_W + 'px';
      el.style.height = KEY_H + 'px';

      if (m % 12 === 0) {
        const lbl = document.createElement('span');
        lbl.className = 'key-label';
        lbl.textContent = midiToNoteName(m);
        lbl.style.pointerEvents = 'none';
        el.appendChild(lbl);
      }
    } else {
      el.classList.add('black-key');
      const leftWhite = whitePositions[m - 1];
      if (leftWhite !== undefined) {
        el.style.left = (leftWhite * KEY_W + KEY_W - BK_W / 2) + 'px';
      }
      el.style.width = BK_W + 'px';
      el.style.height = BK_H + 'px';
    }

    el.title = midiToNoteName(m) + ' (MIDI ' + m + ')';
    el.addEventListener('click', () => onKeyClick(m));
    container.appendChild(el);
    pianoState.keys[m] = el;
  }

  scrollToMiddleC();
  loadExisting();
}

function scrollToMiddleC() {
  const scroll = document.getElementById('piano-scroll');
  if (!scroll) return;
  const c4 = pianoState.keys[60];
  if (c4) {
    const offset = c4.offsetLeft - scroll.clientWidth / 2 + KEY_W / 2;
    scroll.scrollLeft = Math.max(0, offset);
  }
}

/* ── Key click handler ──────────────────────────────────────────────────── */
function onKeyClick(midi) {
  const mode = pianoState.mode;

  if (mode === 'range') {
    handleRangeClick(midi);
  } else if (mode === 'favorites') {
    handleMarkClick(midi, 'favorites');
  } else if (mode === 'avoids') {
    handleMarkClick(midi, 'avoids');
  }
}

function handleRangeClick(midi) {
  const s = pianoState;

  if (s.rangeStart === null || s._rangeClicks >= 2) {
    s.rangeStart = midi;
    s.rangeEnd = null;
    s._rangeClicks = 1;
    s.favorites.clear();
    s.avoids.clear();
  } else if (s.rangeEnd === null) {
    if (midi < s.rangeStart) {
      s.rangeEnd = s.rangeStart;
      s.rangeStart = midi;
    } else if (midi > s.rangeStart) {
      s.rangeEnd = midi;
    } else {
      return;
    }
    s._rangeClicks = 2;
  }

  refreshKeyStyles();
  updateReadouts();
  if (typeof updateNextButton === 'function') updateNextButton();
}

function handleMarkClick(midi, which) {
  const s = pianoState;
  if (s.rangeStart === null || s.rangeEnd === null) return;
  if (midi < s.rangeStart || midi > s.rangeEnd) return;

  const set = s[which];
  const other = which === 'favorites' ? 'avoids' : 'favorites';

  if (set.has(midi)) {
    set.delete(midi);
  } else {
    s[other].delete(midi);
    set.add(midi);
  }

  refreshKeyStyles();
  updateReadouts();
}

/* ── Styling ────────────────────────────────────────────────────────────── */
function refreshKeyStyles() {
  const s = pianoState;
  const hasRange = s.rangeStart !== null && s.rangeEnd !== null;

  for (let m = MIDI_LOW; m <= MIDI_HIGH; m++) {
    const el = s.keys[m];
    if (!el) continue;

    el.classList.remove('dimmed', 'range-edge', 'favorite', 'avoid');

    if (hasRange) {
      if (m < s.rangeStart || m > s.rangeEnd) {
        el.classList.add('dimmed');
      } else if (s.favorites.has(m)) {
        el.classList.add('favorite');
      } else if (s.avoids.has(m)) {
        el.classList.add('avoid');
      }

      if (m === s.rangeStart || m === s.rangeEnd) {
        el.classList.add('range-edge');
      }
    } else if (s.rangeStart !== null && m === s.rangeStart) {
      el.classList.add('range-edge');
    }
  }
}

/* ── Readouts ───────────────────────────────────────────────────────────── */
function updateReadouts() {
  const s = pianoState;

  const rangeEl = document.querySelector('#range-readout .note-list');
  if (rangeEl) {
    if (s.rangeStart !== null && s.rangeEnd !== null) {
      rangeEl.textContent = midiToNoteName(s.rangeStart) + ' – ' + midiToNoteName(s.rangeEnd);
    } else if (s.rangeStart !== null) {
      rangeEl.textContent = midiToNoteName(s.rangeStart) + ' – (click high note)';
    } else {
      rangeEl.textContent = 'Click two keys to set your range';
    }
  }

  const favEl = document.querySelector('#favorites-readout .note-list');
  if (favEl) {
    const arr = Array.from(s.favorites).sort((a, b) => a - b);
    favEl.textContent = arr.length ? arr.map(midiToNoteName).join(', ') : 'None';
  }

  const avoidEl = document.querySelector('#avoids-readout .note-list');
  if (avoidEl) {
    const arr = Array.from(s.avoids).sort((a, b) => a - b);
    avoidEl.textContent = arr.length ? arr.map(midiToNoteName).join(', ') : 'None';
  }
}

/* ── Mode switching ─────────────────────────────────────────────────────── */
function setMode(mode) {
  pianoState.mode = mode;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('mode-' + mode);
  if (btn) btn.classList.add('active');
}

/* ── Reset ──────────────────────────────────────────────────────────────── */
function resetRange() {
  pianoState.rangeStart = null;
  pianoState.rangeEnd = null;
  pianoState._rangeClicks = 0;
  pianoState.favorites.clear();
  pianoState.avoids.clear();
  pianoState.mode = 'range';
  setMode('range');
  refreshKeyStyles();
  updateReadouts();
  if (typeof updateNextButton === 'function') updateNextButton();
}

/* ── Load existing profile data ─────────────────────────────────────────── */
function loadExisting() {
  if (typeof EXISTING === 'undefined' || !EXISTING || !EXISTING.min_midi) return;
  const e = EXISTING;

  pianoState.rangeStart = e.min_midi;
  pianoState.rangeEnd = e.max_midi;
  pianoState._rangeClicks = 2;

  if (e.favorite_midis) e.favorite_midis.forEach(m => pianoState.favorites.add(m));
  if (e.avoid_midis) e.avoid_midis.forEach(m => pianoState.avoids.add(m));

  refreshKeyStyles();
  updateReadouts();
  if (typeof updateNextButton === 'function') updateNextButton();

  const scroll = document.getElementById('piano-scroll');
  const lowKey = pianoState.keys[e.min_midi];
  if (scroll && lowKey) {
    const offset = lowKey.offsetLeft - 60;
    scroll.scrollLeft = Math.max(0, offset);
  }
}

/* ── Init ───────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', buildPiano);
