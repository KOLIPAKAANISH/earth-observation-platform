"use client";

import { useCallback, useRef, useState } from "react";

export interface ChangeBox {
  x: number; // normalized [0..1]
  y: number;
  w: number;
  h: number;
  score: number;
}

interface Props {
  beforeUrl: string | null;
  afterUrl: string | null;
  boxes?: ChangeBox[];
}

/** Draggable before/after comparison slider. Boxes are drawn on the after side. */
export default function CompareSlider({ beforeUrl, afterUrl, boxes = [] }: Props) {
  const [split, setSplit] = useState(50);
  const draggingRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const updateFromEvent = useCallback((clientX: number) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setSplit(Math.min(100, Math.max(0, pct)));
  }, []);

  if (!beforeUrl || !afterUrl) {
    return (
      <div className="flex aspect-square w-full items-center justify-center rounded-lg bg-slate-800 text-sm text-slate-400">
        Run an analysis to compare images
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="relative aspect-square w-full select-none overflow-hidden rounded-lg"
      onMouseDown={(e) => {
        draggingRef.current = true;
        updateFromEvent(e.clientX);
      }}
      onMouseMove={(e) => draggingRef.current && updateFromEvent(e.clientX)}
      onMouseUp={() => (draggingRef.current = false)}
      onMouseLeave={() => (draggingRef.current = false)}
      onTouchStart={(e) => updateFromEvent(e.touches[0].clientX)}
      onTouchMove={(e) => updateFromEvent(e.touches[0].clientX)}
    >
      {/* Before (base layer) */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={beforeUrl} alt="Before" className="absolute inset-0 h-full w-full object-cover" />

      {/* After, clipped to the right of the handle — boxes clip with it */}
      <div
        className="absolute inset-0"
        style={{ clipPath: `inset(0 0 0 ${split}%)` }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={afterUrl} alt="After" className="absolute inset-0 h-full w-full object-cover" />
        {boxes.map((b, i) => (
          <div
            key={i}
            className="absolute border-2"
            style={{
              left: `${b.x * 100}%`,
              top: `${b.y * 100}%`,
              width: `${b.w * 100}%`,
              height: `${b.h * 100}%`,
              borderColor: i % 2 === 0 ? "#ff4040" : "#ffaa00",
            }}
          >
            <span
              className="absolute -top-0.5 left-0.5 px-1 text-[10px] font-bold text-white"
              style={{ backgroundColor: i % 2 === 0 ? "#ff4040" : "#ffaa00" }}
            >
              #{i + 1}
            </span>
          </div>
        ))}
      </div>

      {/* Handle */}
      <div
        className="absolute inset-y-0 z-10 w-0.5 cursor-ew-resize bg-white"
        style={{ left: `${split}%` }}
      >
        <div className="absolute top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-slate-900/80 text-center text-xs leading-7 text-white">
          ↔
        </div>
      </div>

      <span className="absolute left-2 top-2 rounded bg-black/60 px-1.5 py-0.5 text-xs">
        Before
      </span>
      <span className="absolute right-2 top-2 rounded bg-black/60 px-1.5 py-0.5 text-xs">
        After
      </span>
    </div>
  );
}
