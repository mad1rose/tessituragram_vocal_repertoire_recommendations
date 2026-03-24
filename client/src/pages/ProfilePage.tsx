import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PianoKeyboard from '../components/PianoKeyboard';
import AlphaSlider from '../components/AlphaSlider';
import { midiToNoteName } from '../utils/midi';
import type { PianoMode, VocalProfile, RecommendResponse } from '../types';

interface Props {
  profile: VocalProfile;
  setProfile: React.Dispatch<React.SetStateAction<VocalProfile>>;
  setResults: React.Dispatch<React.SetStateAction<RecommendResponse | null>>;
}

export default function ProfilePage({ profile, setProfile, setResults }: Props) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<PianoMode>('range');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRangeChange = (low: number | null, high: number | null) => {
    setProfile((p) => ({ ...p, rangeLow: low, rangeHigh: high }));
  };

  const toggleFavorite = (midi: number) => {
    setProfile((p) => {
      const next = new Set(p.favorites);
      if (next.has(midi)) next.delete(midi);
      else next.add(midi);
      return { ...p, favorites: next };
    });
  };

  const toggleAvoid = (midi: number) => {
    setProfile((p) => {
      const next = new Set(p.avoids);
      if (next.has(midi)) next.delete(midi);
      else next.add(midi);
      return { ...p, avoids: next };
    });
  };

  const clearAll = () => {
    setProfile({
      rangeLow: null,
      rangeHigh: null,
      favorites: new Set(),
      avoids: new Set(),
      alpha: 0,
    });
    setMode('range');
  };

  const canSubmit = profile.rangeLow !== null && profile.rangeHigh !== null;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError('');

    const body = {
      min_note: midiToNoteName(profile.rangeLow!),
      max_note: midiToNoteName(profile.rangeHigh!),
      favorite_notes: [...profile.favorites].map(midiToNoteName),
      avoid_notes: [...profile.avoids].map(midiToNoteName),
      alpha: profile.alpha,
    };

    try {
      const res = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Request failed');
      }
      const data: RecommendResponse = await res.json();
      setResults(data);
      navigate('/results');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const sortedFavs = [...profile.favorites].sort((a, b) => a - b);
  const sortedAvoids = [...profile.avoids].sort((a, b) => a - b);

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blush-600 via-lavender-400 to-rosegold bg-clip-text text-transparent">
            Tessituragram Recommender
          </h1>
          <p className="text-sm text-warm-gray max-w-lg mx-auto">
            Set your vocal range, mark your favorite and avoid notes, then get
            personalized song recommendations.
          </p>
        </div>

        {/* Mode selector */}
        <div className="flex items-center justify-center gap-2">
          {(['range', 'favorites', 'avoid'] as PianoMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all
                ${
                  mode === m
                    ? m === 'favorites'
                      ? 'bg-mint-400 text-white shadow-md'
                      : m === 'avoid'
                        ? 'bg-coral-400 text-white shadow-md'
                        : 'bg-gradient-to-r from-blush-500 to-lavender-400 text-white shadow-md'
                    : 'bg-white/70 text-warm-gray border border-blush-200 hover:bg-blush-50'
                }`}
            >
              {m === 'range' && '🎹 Range'}
              {m === 'favorites' && '💚 Favorites'}
              {m === 'avoid' && '🚫 Avoid'}
            </button>
          ))}

          <button
            onClick={clearAll}
            className="ml-4 px-4 py-2 rounded-full text-sm text-warm-gray
                       bg-white/50 border border-blush-200 hover:bg-coral-50
                       hover:text-coral-500 transition-all"
          >
            Clear all
          </button>
        </div>

        {/* Piano */}
        <div className="bg-white/60 backdrop-blur-sm rounded-3xl p-6 shadow-sm border border-blush-100">
          <PianoKeyboard
            mode={mode}
            rangeLow={profile.rangeLow}
            rangeHigh={profile.rangeHigh}
            favorites={profile.favorites}
            avoids={profile.avoids}
            onRangeChange={handleRangeChange}
            onToggleFavorite={toggleFavorite}
            onToggleAvoid={toggleAvoid}
          />
        </div>

        {/* Selection summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <div className="bg-white/70 rounded-2xl p-4 border border-blush-100">
            <span className="text-[10px] uppercase tracking-wider text-warm-gray block mb-1">
              Range
            </span>
            <span className="font-semibold text-plum-900">
              {profile.rangeLow !== null && profile.rangeHigh !== null
                ? `${midiToNoteName(profile.rangeLow)} – ${midiToNoteName(profile.rangeHigh)}`
                : 'Not set'}
            </span>
          </div>
          <div className="bg-white/70 rounded-2xl p-4 border border-blush-100">
            <span className="text-[10px] uppercase tracking-wider text-warm-gray block mb-1">
              Favorites
            </span>
            <span className="font-semibold text-mint-500">
              {sortedFavs.length > 0
                ? sortedFavs.map(midiToNoteName).join(', ')
                : 'None'}
            </span>
          </div>
          <div className="bg-white/70 rounded-2xl p-4 border border-blush-100">
            <span className="text-[10px] uppercase tracking-wider text-warm-gray block mb-1">
              Avoid
            </span>
            <span className="font-semibold text-coral-400">
              {sortedAvoids.length > 0
                ? sortedAvoids.map(midiToNoteName).join(', ')
                : 'None'}
            </span>
          </div>
        </div>

        {/* Alpha slider */}
        <div className="bg-white/60 backdrop-blur-sm rounded-3xl p-6 shadow-sm border border-blush-100">
          <AlphaSlider
            value={profile.alpha}
            onChange={(v) => setProfile((p) => ({ ...p, alpha: v }))}
          />
        </div>

        {/* Submit */}
        {error && (
          <p className="text-center text-coral-500 text-sm">{error}</p>
        )}

        <div className="text-center">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || loading}
            className="px-10 py-3.5 rounded-full text-base font-semibold text-white
                       bg-gradient-to-r from-blush-500 via-blush-400 to-lavender-400
                       shadow-lg hover:shadow-xl hover:scale-[1.02]
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-all duration-200"
          >
            {loading ? 'Finding songs...' : '🎶 Get Recommendations'}
          </button>
        </div>
      </div>
    </div>
  );
}
