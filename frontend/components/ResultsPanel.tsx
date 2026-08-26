"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChangeBox } from "./CompareSlider";

export interface AnalyzeResponse {
  demo_data: boolean;
  location_id: string;
  before_date: string;
  after_date: string;
  stats: {
    changed_pct: number;
    ndvi_before: number;
    ndvi_after: number;
    ndvi_change_pct: number;
    mean_diff: number;
    channel_diffs: Record<string, number>;
  };
  boxes: ChangeBox[];
  images: { before: string; after: string; overlay: string };
}

interface Props {
  result: AnalyzeResponse | null;
  loading: boolean;
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg bg-slate-800 p-3">
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 text-xl font-semibold text-slate-100">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-400">{hint}</div>}
    </div>
  );
}

export default function ResultsPanel({ result, loading }: Props) {
  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center rounded-lg bg-slate-800/60 text-sm text-slate-300">
        Running demo analysis…
      </div>
    );
  }
  if (!result) return null;

  const { stats, boxes, images } = result;
  const chartData = Object.entries(stats.channel_diffs).map(([band, diff]) => ({
    band: band[0].toUpperCase() + band.slice(1),
    diff,
  }));
  const vegDelta = stats.ndvi_change_pct;

  return (
    <div className="space-y-4">
      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="Changed area"
          value={`${stats.changed_pct.toFixed(1)}%`}
          hint="pixels above threshold"
        />
        <StatCard label="Pseudo-NDVI before" value={stats.ndvi_before.toFixed(3)} />
        <StatCard label="Pseudo-NDVI after" value={stats.ndvi_after.toFixed(3)} />
        <StatCard
          label="Vegetation change"
          value={`${vegDelta > 0 ? "+" : ""}${vegDelta.toFixed(1)}%`}
          hint={vegDelta > 0 ? "greening" : vegDelta < 0 ? "browning / loss" : "no change"}
        />
      </div>

      {/* Chart + detected regions */}
      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-lg bg-slate-800 p-3">
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
            Mean per-band difference
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="band" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} width={40} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", border: "none", fontSize: 12 }}
                formatter={(v) => [typeof v === "number" ? v.toFixed(4) : v, "mean abs diff"]}
              />
              <Bar dataKey="diff" fill="#38bdf8" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg bg-slate-800 p-3">
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
            Detected change regions ({boxes.length})
          </div>
          {boxes.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">No regions above threshold.</p>
          ) : (
            <ul className="max-h-36 space-y-1 overflow-y-auto pr-1 text-sm">
              {boxes.map((b, i) => (
                <li key={i} className="flex justify-between rounded bg-slate-900/70 px-2 py-1">
                  <span>Region #{i + 1}</span>
                  <span className="text-slate-400">
                    score {b.score.toFixed(3)} · {(b.w * b.h * 100).toFixed(1)}% of frame
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Overlay image */}
      <div>
        <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
          Change overlay ({result.after_date})
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={images.overlay}
          alt="Change overlay"
          className="aspect-square w-full rounded-lg object-cover"
        />
      </div>
    </div>
  );
}
