const NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'];

export function midiToNoteName(midi: number): string {
  const octave = Math.floor(midi / 12) - 1;
  return `${NOTE_NAMES[midi % 12]}${octave}`;
}

export function isBlackKey(midi: number): boolean {
  const pc = midi % 12;
  return [1, 3, 6, 8, 10].includes(pc);
}

export function isWhiteKey(midi: number): boolean {
  return !isBlackKey(midi);
}

/** MIDI 21 (A0) through 108 (C8) — standard 88-key piano */
export const PIANO_MIN = 21;
export const PIANO_MAX = 108;

export function allPianoMidis(): number[] {
  const midis: number[] = [];
  for (let m = PIANO_MIN; m <= PIANO_MAX; m++) midis.push(m);
  return midis;
}

export function whiteKeyIndex(midi: number): number {
  let count = 0;
  for (let m = PIANO_MIN; m < midi; m++) {
    if (isWhiteKey(m)) count++;
  }
  return count;
}

export function totalWhiteKeys(): number {
  let count = 0;
  for (let m = PIANO_MIN; m <= PIANO_MAX; m++) {
    if (isWhiteKey(m)) count++;
  }
  return count;
}

/**
 * Return the MIDI number of the white key immediately to the left
 * of a given black key, used for positioning.
 */
export function leftWhiteKeyOf(blackMidi: number): number {
  for (let m = blackMidi - 1; m >= PIANO_MIN; m--) {
    if (isWhiteKey(m)) return m;
  }
  return PIANO_MIN;
}
