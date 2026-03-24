import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SongCard from '../components/SongCard';
import Pagination from '../components/Pagination';
import SongDetailModal from '../components/SongDetailModal';
import type { RecommendResponse } from '../types';

const PER_PAGE = 10;

interface Props {
  results: RecommendResponse | null;
}

export default function ResultsPage({ results }: Props) {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [detailFilename, setDetailFilename] = useState<string | null>(null);

  if (!results || results.total === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-lg text-warm-gray">
          {results?.total === 0
            ? 'No songs match your range. Try widening it.'
            : 'No results yet.'}
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-2 rounded-full text-sm font-medium bg-gradient-to-r
                     from-blush-500 to-lavender-400 text-white shadow-md"
        >
          ← Set up profile
        </button>
      </div>
    );
  }

  const totalPages = Math.ceil(results.total / PER_PAGE);
  const start = (page - 1) * PER_PAGE;
  const pageResults = results.results.slice(start, start + PER_PAGE);

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-plum-900">
              Recommendations
            </h1>
            <p className="text-sm text-warm-gray">
              {results.total} song{results.total !== 1 && 's'} found, ranked best → worst
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2 rounded-full text-sm font-medium
                       bg-white/70 border border-blush-200 text-plum-900
                       hover:bg-blush-50 transition-colors"
          >
            ← Edit Profile
          </button>
        </div>

        {/* Cards */}
        <div className="space-y-3">
          {pageResults.map((song) => (
            <SongCard
              key={song.filename}
              song={song}
              onViewDetail={setDetailFilename}
            />
          ))}
        </div>

        {/* Pagination */}
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      </div>

      {/* Detail modal */}
      <SongDetailModal
        filename={detailFilename}
        onClose={() => setDetailFilename(null)}
      />
    </div>
  );
}
