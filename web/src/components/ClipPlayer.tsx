"use client";

import { CheckCircle2, Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import WaveSurfer from "wavesurfer.js";
import { fetcher, qs, type Clip } from "@/lib/api";
import { displayName } from "@/lib/format";

export function ClipList({
  species,
  clusterId,
  month,
  limit = 6,
  title = "Listen",
}: {
  species?: string | null;
  clusterId?: string | null;
  month?: number | null;
  limit?: number;
  title?: string;
}) {
  const { data, isLoading } = useSWR<Clip[]>(
    `/api/public/clips${qs({ species, cluster_id: clusterId, month, limit })}`,
    fetcher,
  );
  const [active, setActive] = useState<string | null>(null);

  return (
    <div>
      <p className="eyebrow mb-3">{title}</p>
      {isLoading && <p className="text-sm text-white/40">Loading recordings…</p>}
      {data && data.length === 0 && (
        <p className="text-sm text-white/40">No example recordings for this selection yet.</p>
      )}
      <ul className="space-y-2">
        {data?.map((c) => (
          <li key={c.clip_id}>
            <ClipRow clip={c} active={active === c.clip_id} onPlay={() => setActive(c.clip_id)} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function ClipRow({ clip, active, onPlay }: { clip: Clip; active: boolean; onPlay: () => void }) {
  const container = useRef<HTMLDivElement>(null);
  const ws = useRef<WaveSurfer | null>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!active || !container.current) return;
    const w = WaveSurfer.create({
      container: container.current,
      url: `/api/clips/${clip.clip_id}.mp3`,
      height: 36,
      waveColor: "rgba(78,205,196,0.35)",
      progressColor: "#4ecdc4",
      cursorWidth: 0,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
    });
    w.on("ready", () => w.play());
    w.on("play", () => setPlaying(true));
    w.on("pause", () => setPlaying(false));
    w.on("finish", () => setPlaying(false));
    w.on("error", () => setError(true));
    ws.current = w;
    return () => {
      w.destroy();
      ws.current = null;
      setPlaying(false);
    };
  }, [active, clip.clip_id]);

  return (
    <div className={`card flex items-center gap-3 px-3 py-2 ${active ? "border-teal/40" : ""}`}>
      <button
        aria-label={playing ? "Pause" : "Play"}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal/15 text-teal hover:bg-teal/25"
        onClick={() => (active && ws.current ? ws.current.playPause() : onPlay())}
      >
        {playing ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
      </button>
      <div className="min-w-0 flex-1">
        {active ? (
          error ? (
            <p className="text-xs text-coral">Recording unavailable</p>
          ) : (
            <div ref={container} />
          )
        ) : (
          <>
            <p className="truncate text-sm">{displayName(clip)}</p>
            <p className="truncate text-xs text-white/45">
              {clip.cluster ?? clip.cluster_id} · {clip.country} ·{" "}
              {new Date(clip.recorded_on).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
            </p>
          </>
        )}
      </div>
      {clip.validated ? (
        <span title="Checked by a validator" className="flex items-center gap-1 text-[11px] text-teal">
          <CheckCircle2 className="h-3.5 w-3.5" /> checked
        </span>
      ) : (
        <span className="text-[11px] tabular-nums text-white/40">{Math.round(clip.confidence * 100)}%</span>
      )}
    </div>
  );
}
