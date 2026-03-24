import { useEffect, useState } from 'react';
import type { SongDetail } from '../types';
import TessiturogramChart from './TessiturogramChart';

interface Props {
  filename: string | null;
  onClose: () => void;
}

export default function SongDetailModal({ filename, onClose }: Props) {
  const [detail, setDetail] = useState<SongDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!filename) {
      setDetail(null);
      return;
    }
    setLoading(true);
    fetch(`/api/song/${encodeURIComponent(filename)}`)
      .then((r) => r.json())
      .then((d) => setDetail(d))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [filename]);

  if (!filename) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4
                 bg-plum-900/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-3xl shadow-2xl w-full max-w-3xl max-h-[90vh]
                   overflow-y-auto border border-blush-200"
        onClick={(e) => e.stopPropagation()}
      >
        {loading && (
          <div className="p-12 text-center text-blush-400">Loading...</div>
        )}

        {detail && (
          <>
            <div className="sticky top-0 bg-white/95 backdrop-blur rounded-t-3xl
                            px-6 pt-5 pb-4 border-b border-blush-100 flex
                            items-start justify-between z-10">
              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-blush-400">
                    #{detail.rank}
                  </span>
                  <h2 className="text-lg font-bold text-plum-900">
                    {detail.title}
                  </h2>
                </div>
                <p className="text-sm text-warm-gray">{detail.composer}</p>
              </div>
              <button
                onClick={onClose}
                className="text-2xl leading-none text-warm-gray hover:text-blush-500
                           transition-colors p-1"
              >
                ×
              </button>
            </div>

            <div className="px-6 py-4 space-y-5">
              {/* Score badges */}
              <div className="flex flex-wrap gap-3">
                <Badge
                  label="Final Score"
                  value={`${(detail.final_score * 100).toFixed(0)}%`}
                  color="bg-gradient-to-r from-blush-500 to-lavender-400 text-white"
                />
                <Badge
                  label="Cosine"
                  value={detail.cosine_similarity.toFixed(3)}
                  color="bg-blush-100 text-plum-900"
                />
                {detail.avoid_penalty > 0 && (
                  <Badge
                    label="Avoid Penalty"
                    value={`${(detail.avoid_penalty * 100).toFixed(1)}%`}
                    color="bg-coral-300/30 text-coral-500"
                  />
                )}
                {detail.favorite_overlap > 0 && (
                  <Badge
                    label="Favorite Overlap"
                    value={`${(detail.favorite_overlap * 100).toFixed(1)}%`}
                    color="bg-mint-300/30 text-mint-500"
                  />
                )}
              </div>

              <p className="text-sm text-warm-gray leading-relaxed">
                {detail.explanation}
              </p>

              {/* Chart */}
              <div className="bg-blush-50/50 rounded-2xl p-4">
                <h3 className="text-sm font-semibold text-plum-900 mb-2">
                  Tessituragram vs. Ideal Vector
                </h3>
                <TessiturogramChart
                  normalizedVector={detail.normalized_vector}
                  idealVector={detail.ideal_vector}
                  minMidi={detail.user_min_midi}
                  maxMidi={detail.user_max_midi}
                />
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-3 gap-3 text-xs text-warm-gray">
                <div className="bg-blush-50/50 rounded-xl p-3">
                  <span className="block text-[10px] uppercase tracking-wider mb-1">
                    Song Range
                  </span>
                  <span className="font-semibold text-plum-900">
                    {detail.statistics?.pitch_range?.min} – {detail.statistics?.pitch_range?.max}
                  </span>
                </div>
                <div className="bg-blush-50/50 rounded-xl p-3">
                  <span className="block text-[10px] uppercase tracking-wider mb-1">
                    Unique Pitches
                  </span>
                  <span className="font-semibold text-plum-900">
                    {detail.statistics?.unique_pitches}
                  </span>
                </div>
                <div className="bg-blush-50/50 rounded-xl p-3">
                  <span className="block text-[10px] uppercase tracking-wider mb-1">
                    Total Duration
                  </span>
                  <span className="font-semibold text-plum-900">
                    {detail.statistics?.total_duration?.toFixed(1)} beats
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Badge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold ${color}`}>
      <span className="text-[10px] font-normal uppercase tracking-wider opacity-70">
        {label}
      </span>
      {value}
    </span>
  );
}
