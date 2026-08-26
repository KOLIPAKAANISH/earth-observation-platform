"use client";

import { useEffect, useRef } from "react";
import maplibregl, { type Map as MlMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export interface DemoLocation {
  id: string;
  name: string;
  kind: string;
  lat: number;
  lon: number;
  description: string;
}

interface Props {
  locations: DemoLocation[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function MapPicker({ locations, selectedId, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const markersRef = useRef<Record<string, maplibregl.Marker>>({});

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: [-98, 36.5],
      zoom: 4,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Add a marker per demo location; clicking selects it.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const created: Record<string, maplibregl.Marker> = {};
    for (const loc of locations) {
      const el = document.createElement("button");
      el.className =
        "rounded-full border-2 border-white shadow-lg cursor-pointer transition-transform hover:scale-110 " +
        (loc.id === selectedId ? "w-5 h-5 bg-amber-400" : "w-4 h-4 bg-sky-500");
      el.title = loc.name;
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        onSelect(loc.id);
        map.flyTo({ center: [loc.lon, loc.lat], zoom: 11, duration: 900 });
      });

      const popup = new maplibregl.Popup({ offset: 12 }).setHTML(
        `<strong>${loc.name}</strong><br/><span style="color:#555">${loc.description}</span>`
      );

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([loc.lon, loc.lat])
        .setPopup(popup)
        .addTo(map);
      created[loc.id] = marker;
    }
    markersRef.current = created;

    return () => {
      for (const m of Object.values(created)) m.remove();
      markersRef.current = {};
    };
  }, [locations, selectedId, onSelect]);

  // Fly to the selected location when selection changes from elsewhere.
  useEffect(() => {
    const loc = locations.find((l) => l.id === selectedId);
    if (loc && mapRef.current) {
      mapRef.current.flyTo({
        center: [loc.lon, loc.lat],
        zoom: 11,
        duration: 900,
      });
    }
  }, [selectedId, locations]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full rounded-lg" />
      <div className="pointer-events-none absolute bottom-2 left-2 rounded bg-slate-900/85 px-2 py-1 text-[10px] uppercase tracking-wide text-amber-300">
        Demo locations — DEMO DATA
      </div>
    </div>
  );
}
