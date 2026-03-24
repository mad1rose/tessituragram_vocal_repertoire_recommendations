import {
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { midiToNoteName } from '../utils/midi';

interface Props {
  normalizedVector: Record<string, number>;
  idealVector: Record<string, number>;
  minMidi: number;
  maxMidi: number;
}

export default function TessiturogramChart({
  normalizedVector,
  idealVector,
  minMidi,
  maxMidi,
}: Props) {
  const data = [];
  for (let m = minMidi; m <= maxMidi; m++) {
    data.push({
      name: midiToNoteName(m),
      midi: m,
      song: normalizedVector[String(m)] ?? 0,
      ideal: idealVector[String(m)] ?? 0,
    });
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={data} margin={{ top: 10, right: 20, bottom: 60, left: 20 }}>
        <XAxis
          dataKey="name"
          angle={-45}
          textAnchor="end"
          tick={{ fontSize: 10, fill: '#4b3649' }}
          interval={0}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#4b3649' }}
          label={{
            value: 'Proportion',
            angle: -90,
            position: 'insideLeft',
            style: { fontSize: 11, fill: '#4b3649' },
          }}
        />
        <Tooltip
          contentStyle={{
            background: '#fdf2f8',
            border: '1px solid #f9a8d4',
            borderRadius: 12,
            fontSize: 12,
          }}
          formatter={(value, name) => [
            `${(Number(value) * 100).toFixed(1)}%`,
            name === 'song' ? 'Song' : 'Ideal',
          ]}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
        />
        <Bar
          dataKey="song"
          name="Song (normalized)"
          fill="#f9a8d4"
          radius={[3, 3, 0, 0]}
        />
        <Line
          dataKey="ideal"
          name="Ideal vector"
          type="monotone"
          stroke="#e8a87c"
          strokeWidth={2.5}
          dot={{ r: 3, fill: '#e8a87c', stroke: '#fff', strokeWidth: 1 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
