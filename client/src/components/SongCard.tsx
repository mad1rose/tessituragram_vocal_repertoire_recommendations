import type { SongSummary } from '../types';

interface Props {
  song: SongSummary;
  onViewDetail: (filename: string) => void;
}

export default function SongCard({ song, onViewDetail }: Props) {
  const pct = (song.final_score * 100).toFixed(0);

  return (
    <div
      className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-sm
                 border border-blush-100 hover:shadow-md hover:border-blush-300
                 transition-all duration-200 cursor-pointer"
      onClick={() => onViewDetail(song.filename)}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-baseline gap-3 min-w-0">
          <span className="text-2xl font-bold text-blush-400 shrink-0">
            #{song.rank}
          </span>
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-plum-900 truncate">
              {song.title}
            </h3>
            <p className="text-sm text-warm-gray truncate">{song.composer}</p>
          </div>
        </div>

        <div className="shrink-0 flex flex-col items-end">
          <span className="text-2xl font-bold text-blush-600">{pct}%</span>
          <span className="text-[10px] text-warm-gray uppercase tracking-wider">
            match
          </span>
        </div>
      </div>

      <p className="text-xs text-warm-gray mt-3 line-clamp-2 leading-relaxed">
        {song.explanation}
      </p>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-blush-50">
        <div className="flex gap-4 text-[10px] text-warm-gray">
          <span>
            Cosine: <b className="text-plum-900">{song.cosine_similarity.toFixed(2)}</b>
          </span>
          {song.avoid_penalty > 0 && (
            <span>
              Avoid: <b className="text-coral-400">{(song.avoid_penalty * 100).toFixed(1)}%</b>
            </span>
          )}
          {song.favorite_overlap > 0 && (
            <span>
              Favorites: <b className="text-mint-500">{(song.favorite_overlap * 100).toFixed(1)}%</b>
            </span>
          )}
        </div>
        <span className="text-xs text-blush-500 font-medium hover:text-blush-700 transition-colors">
          View details →
        </span>
      </div>
    </div>
  );
}
