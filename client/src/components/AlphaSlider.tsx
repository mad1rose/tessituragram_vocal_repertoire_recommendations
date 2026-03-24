interface Props {
  value: number;
  onChange: (v: number) => void;
}

export default function AlphaSlider({ value, onChange }: Props) {
  return (
    <div className="w-full max-w-md mx-auto">
      <label className="block text-sm font-semibold text-plum-900 mb-1">
        Alpha (avoid penalty weight)
      </label>
      <p className="text-xs text-warm-gray mb-3">
        Controls how much time spent on avoided notes hurts a song's ranking.
        0 = ignore avoids, 1 = heavy penalty.
      </p>
      <div className="flex items-center gap-4">
        <span className="text-xs text-warm-gray w-6">0.0</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="flex-1 h-2 rounded-full appearance-none cursor-pointer
                     bg-gradient-to-r from-blush-200 via-blush-400 to-lavender-400
                     [&::-webkit-slider-thumb]:appearance-none
                     [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                     [&::-webkit-slider-thumb]:rounded-full
                     [&::-webkit-slider-thumb]:bg-blush-500
                     [&::-webkit-slider-thumb]:shadow-md
                     [&::-webkit-slider-thumb]:border-2
                     [&::-webkit-slider-thumb]:border-white
                     [&::-webkit-slider-thumb]:cursor-pointer"
        />
        <span className="text-xs text-warm-gray w-6">1.0</span>
        <span className="text-sm font-bold text-blush-600 w-10 text-right tabular-nums">
          {value.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
