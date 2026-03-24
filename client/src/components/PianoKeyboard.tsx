import { useState, useRef, useEffect } from 'react';
import type { PianoMode } from '../types';
import {
  midiToNoteName,
  isBlackKey,
  isWhiteKey,
  allPianoMidis,
  whiteKeyIndex,
  totalWhiteKeys,
  leftWhiteKeyOf,
} from '../utils/midi';

interface Props {
  mode: PianoMode;
  rangeLow: number | null;
  rangeHigh: number | null;
  favorites: Set<number>;
  avoids: Set<number>;
  onRangeChange: (low: number | null, high: number | null) => void;
  onToggleFavorite: (midi: number) => void;
  onToggleAvoid: (midi: number) => void;
}

const WHITE_KEY_W = 24;
const WHITE_KEY_H = 140;
const BLACK_KEY_W = 14;
const BLACK_KEY_H = 90;

export default function PianoKeyboard({
  mode,
  rangeLow,
  rangeHigh,
  favorites,
  avoids,
  onRangeChange,
  onToggleFavorite,
  onToggleAvoid,
}: Props) {
  const [hoveredMidi, setHoveredMidi] = useState<number | null>(null);
  const [rangeStep, setRangeStep] = useState<'low' | 'high'>('low');
  const scrollRef = useRef<HTMLDivElement>(null);

  const numWhite = totalWhiteKeys();
  const totalW = numWhite * WHITE_KEY_W;

  useEffect(() => {
    if (scrollRef.current) {
      const center = totalW / 2 - scrollRef.current.clientWidth / 2;
      scrollRef.current.scrollLeft = Math.max(0, center);
    }
  }, [totalW]);

  const inRange = (midi: number) => {
    if (rangeLow === null || rangeHigh === null) return true;
    return midi >= rangeLow && midi <= rangeHigh;
  };

  const handleClick = (midi: number) => {
    // Clicking an already-marked key always un-marks it, regardless of mode
    if (favorites.has(midi)) {
      onToggleFavorite(midi);
      return;
    }
    if (avoids.has(midi)) {
      onToggleAvoid(midi);
      return;
    }

    // New markings use the current mode
    if (mode === 'range') {
      if (midi === rangeLow && midi === rangeHigh) {
        onRangeChange(null, null);
        setRangeStep('low');
        return;
      }
      if (midi === rangeLow) {
        onRangeChange(null, rangeHigh);
        setRangeStep('low');
        return;
      }
      if (midi === rangeHigh) {
        onRangeChange(rangeLow, null);
        setRangeStep('high');
        return;
      }
      if (rangeStep === 'low') {
        onRangeChange(midi, rangeHigh);
        setRangeStep('high');
      } else {
        let low = rangeLow ?? midi;
        let high = midi;
        if (low > high) [low, high] = [high, low];
        onRangeChange(low, high);
        setRangeStep('low');
      }
    } else if (mode === 'favorites') {
      if (!inRange(midi)) return;
      onToggleFavorite(midi);
    } else if (mode === 'avoid') {
      if (!inRange(midi)) return;
      onToggleAvoid(midi);
    }
  };

  const keyColor = (midi: number): string => {
    const fav = favorites.has(midi);
    const avoid = avoids.has(midi);
    const black = isBlackKey(midi);
    const dimmed = rangeLow !== null && rangeHigh !== null && !inRange(midi);

    if (fav) return dimmed ? 'rgba(52,211,153,0.3)' : '#34d399';
    if (avoid) return dimmed ? 'rgba(251,113,133,0.3)' : '#fb7185';

    if (black) {
      return dimmed ? '#9ca3af' : '#2d2235';
    }
    return dimmed ? '#e5e7eb' : '#fffbf5';
  };

  const textColor = (midi: number): string => {
    const fav = favorites.has(midi);
    const avoid = avoids.has(midi);
    if (fav) return '#064e3b';
    if (avoid) return '#881337';
    return isBlackKey(midi) ? '#fdf2f8' : '#4b3649';
  };

  const allMidis = allPianoMidis();

  const whiteKeys = allMidis.filter(isWhiteKey);
  const blackKeys = allMidis.filter(isBlackKey);

  const rangeMessage = (): string => {
    if (mode !== 'range') return '';
    if (rangeLow === null && rangeHigh === null) {
      return rangeStep === 'low'
        ? 'Click your lowest note'
        : 'Click your highest note';
    }
    return rangeStep === 'low'
      ? 'Click to set new lowest note'
      : 'Click your highest note';
  };

  return (
    <div className="flex flex-col items-center gap-2 w-full">
      {mode === 'range' && (
        <p className="text-sm text-blush-600 font-medium animate-pulse">
          {rangeMessage()}
        </p>
      )}

      <div
        ref={scrollRef}
        className="overflow-x-auto w-full rounded-xl"
        style={{ maxWidth: '100%' }}
      >
        <svg
          width={totalW}
          height={WHITE_KEY_H + 30}
          viewBox={`0 0 ${totalW} ${WHITE_KEY_H + 30}`}
          className="block"
        >
          {/* White keys */}
          {whiteKeys.map((midi) => {
            const idx = whiteKeyIndex(midi);
            const x = idx * WHITE_KEY_W;
            const hovered = hoveredMidi === midi;
            return (
              <g
                key={midi}
                onClick={() => handleClick(midi)}
                onMouseEnter={() => setHoveredMidi(midi)}
                onMouseLeave={() => setHoveredMidi(null)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  x={x}
                  y={0}
                  width={WHITE_KEY_W}
                  height={WHITE_KEY_H}
                  fill={keyColor(midi)}
                  stroke={hovered ? '#ec4899' : '#d1c4c4'}
                  strokeWidth={hovered ? 2 : 0.5}
                  rx={2}
                />
                <text
                  x={x + WHITE_KEY_W / 2}
                  y={WHITE_KEY_H - 8}
                  textAnchor="middle"
                  fontSize={8}
                  fontWeight={500}
                  fill={textColor(midi)}
                  style={{ userSelect: 'none', pointerEvents: 'none' }}
                >
                  {midiToNoteName(midi)}
                </text>
              </g>
            );
          })}

          {/* Black keys */}
          {blackKeys.map((midi) => {
            const leftWhite = leftWhiteKeyOf(midi);
            const lwIdx = whiteKeyIndex(leftWhite);
            const x = lwIdx * WHITE_KEY_W + WHITE_KEY_W - BLACK_KEY_W / 2;
            const hovered = hoveredMidi === midi;
            return (
              <g
                key={midi}
                onClick={() => handleClick(midi)}
                onMouseEnter={() => setHoveredMidi(midi)}
                onMouseLeave={() => setHoveredMidi(null)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  x={x}
                  y={0}
                  width={BLACK_KEY_W}
                  height={BLACK_KEY_H}
                  fill={keyColor(midi)}
                  stroke={hovered ? '#ec4899' : '#1a1a1a'}
                  strokeWidth={hovered ? 2 : 0.5}
                  rx={2}
                />
                {hovered && (
                  <text
                    x={x + BLACK_KEY_W / 2}
                    y={BLACK_KEY_H + 14}
                    textAnchor="middle"
                    fontSize={8}
                    fontWeight={600}
                    fill="#ec4899"
                    style={{ userSelect: 'none', pointerEvents: 'none' }}
                  >
                    {midiToNoteName(midi)}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
