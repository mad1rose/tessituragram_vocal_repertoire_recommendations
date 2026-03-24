interface Props {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ currentPage, totalPages, onPageChange }: Props) {
  if (totalPages <= 1) return null;

  const pages: (number | '...')[] = [];
  for (let i = 1; i <= totalPages; i++) {
    if (
      i === 1 ||
      i === totalPages ||
      (i >= currentPage - 1 && i <= currentPage + 1)
    ) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...');
    }
  }

  return (
    <div className="flex items-center justify-center gap-2 mt-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-1.5 text-sm rounded-lg bg-white/60 text-plum-900
                   border border-blush-200 hover:bg-blush-100 disabled:opacity-30
                   disabled:cursor-not-allowed transition-colors"
      >
        ← Prev
      </button>

      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`dots-${i}`} className="text-warm-gray text-sm px-1">…</span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`w-9 h-9 text-sm rounded-lg font-medium transition-all
              ${
                p === currentPage
                  ? 'bg-gradient-to-br from-blush-500 to-lavender-400 text-white shadow-md'
                  : 'bg-white/60 text-plum-900 border border-blush-200 hover:bg-blush-100'
              }`}
          >
            {p}
          </button>
        ),
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-1.5 text-sm rounded-lg bg-white/60 text-plum-900
                   border border-blush-200 hover:bg-blush-100 disabled:opacity-30
                   disabled:cursor-not-allowed transition-colors"
      >
        Next →
      </button>
    </div>
  );
}
