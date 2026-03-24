import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProfilePage from './pages/ProfilePage';
import ResultsPage from './pages/ResultsPage';
import type { VocalProfile, RecommendResponse } from './types';

export default function App() {
  const [profile, setProfile] = useState<VocalProfile>({
    rangeLow: null,
    rangeHigh: null,
    favorites: new Set(),
    avoids: new Set(),
    alpha: 0,
  });

  const [results, setResults] = useState<RecommendResponse | null>(null);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <ProfilePage
              profile={profile}
              setProfile={setProfile}
              setResults={setResults}
            />
          }
        />
        <Route
          path="/results"
          element={<ResultsPage results={results} />}
        />
      </Routes>
    </BrowserRouter>
  );
}
