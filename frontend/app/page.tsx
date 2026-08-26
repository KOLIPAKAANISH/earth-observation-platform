"use client";

import { useCallback, useEffect, useState } from "react";
import MapPicker, { type DemoLocation } from "@/components/MapPicker";
import CompareSlider, { type ChangeBox } from "@/components/CompareSlider";
import ResultsPanel, { type AnalyzeResponse } from "@/components/ResultsPanel";

const API_BASE = "http://localhost:8000";

interface LocationsResponse {
  demo_data: boolean;
  locations: DemoLocation[];
  available_dates: string[];
}

export default function Home() {
  const [locationsData, setLocationsData] = useState<LocationsResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [beforeDate, setBeforeDate] = useState<string>("");
  const [afterDate, setAfterDate] = useState<string>("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/locations`)
      .then((r) => r.json())
      .then((data: LocationsResponse) => {
        setLocationsData(data);
        setSelectedId(data.locations[0]?.id ?? null);
        setBeforeDate(data.available_dates[0] ?? "");
        setAfterDate(data.available_dates[1] ?? "");
      })
      .catch(() =>
        setError("Could not reach the API at localhost:8000. Is the backend running?")
      );
  }, []);

  const selected = locationsData?.locations.find((l) => l.id === selectedId) ?? null;
  const dates = locationsData?.available_dates ?? [];

  const runAnalysis = useCallback(async () => {
    if (!selectedId || !beforeDate || !afterDate) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location_id: selectedId,
          before_date: beforeDate,
          after_date: afterDate,
        }),
      });
      if (!res.ok) {
        const detail = (await res.json().catch(() => null))?.detail ?? res.statusText;
        throw new Error(String(detail));
      }
      setResult((await res.json()) as AnalyzeResponse);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [selectedId, beforeDate, afterDate]);

  return (
    <main className="mx-auto max-w-6xl p-4 lg:p-6">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Satellite Change Detection</h1>
          <p className="text-sm text-slate-400">
            Pick a location, pick two dates, run a pixel-diff analysis.
          </p>
        </div>
        <span className="rounded-full border border-amber-500/60 bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-300">
          Demo Data
        </span>
      </header>

      {error && (
        <div className="mb-4 rounded-lg bg-red-900/50 px-4 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_420px]">
        {/* Left column: map + controls + comparison */}
        <section className="space-y-4">
          <div className="h-[320px] overflow-hidden rounded-lg border border-slate-700">
            <MapPicker
              locations={locationsData?.locations ?? []}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-end gap-3 rounded-lg bg-slate-800/60 p-3">
            <label className="flex flex-col text-xs text-slate-400">
              Before date
              <select
                value={beforeDate}
                onChange={(e) => setBeforeDate(e.target.value)}
                disabled={!selectedId || loading}
                className="mt-1 rounded bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
              >
                {dates.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col text-xs text-slate-400">
              After date
              <select
                value={afterDate}
                onChange={(e) => setAfterDate(e.target.value)}
                disabled={!selectedId || loading}
                className="mt-1 rounded bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
              >
                {dates.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <button
              onClick={runAnalysis}
              disabled={loading || !selectedId || beforeDate === afterDate}
              className="ml-auto rounded-md bg-sky-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-slate-600"
            >
              {loading ? "Analyzing…" : "Run Analysis"}
            </button>
          </div>

          {selected && (
            <p className="text-xs text-slate-400">
              Selected: <span className="text-slate-200">{selected.name}</span> —{" "}
              ({selected.lat.toFixed(4)}, {selected.lon.toFixed(4)}) · synthetic imagery,
              not real satellite data
            </p>
          )}

          <CompareSlider
            beforeUrl={result ? `${API_BASE}${result.images.before}` : null}
            afterUrl={result ? `${API_BASE}${result.images.after}` : null}
            boxes={(result?.boxes as ChangeBox[]) ?? []}
          />
        </section>

        {/* Right column: results */}
        <section className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Results — Demo Analysis
          </h2>
          <ResultsPanel result={result} loading={loading} />
          {!result && !loading && (
            <p className="rounded-lg bg-slate-800/60 p-4 text-sm text-slate-400">
              Select a location and two dates, then click <em>Run Analysis</em>.
              Results are produced by a naive image-diff pipeline on synthetic
              imagery and are labeled “Demo Analysis” for a reason.
            </p>
          )}
        </section>
      </div>
    </main>
  );
}
