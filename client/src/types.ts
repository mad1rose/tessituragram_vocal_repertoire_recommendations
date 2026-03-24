export interface SongSummary {
  rank: number;
  filename: string;
  composer: string;
  title: string;
  final_score: number;
  cosine_similarity: number;
  avoid_penalty: number;
  favorite_overlap: number;
  explanation: string;
}

export interface SongDetail extends SongSummary {
  tessituragram: Record<string, number>;
  normalized_vector: Record<string, number>;
  statistics: {
    total_duration: number;
    pitch_range: {
      min: string;
      max: string;
      min_midi: number;
      max_midi: number;
    };
    unique_pitches: number;
  };
  ideal_vector: Record<string, number>;
  user_min_midi: number;
  user_max_midi: number;
}

export interface RecommendResponse {
  total: number;
  results: SongSummary[];
  user_min_midi: number;
  user_max_midi: number;
}

export type PianoMode = 'range' | 'favorites' | 'avoid';

export interface VocalProfile {
  rangeLow: number | null;
  rangeHigh: number | null;
  favorites: Set<number>;
  avoids: Set<number>;
  alpha: number;
}
