class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export function qs(params: Record<string, string | number | null | undefined>) {
  const s = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== "") s.set(k, String(v));
  }
  const out = s.toString();
  return out ? `?${out}` : "";
}

export type Overview = {
  devices: number;
  devices_online: number;
  hours_recorded: number;
  recording_since: string;
  n_species: number;
  n_detections: number;
  countries: number;
  clusters: number;
  sites: number;
  updated_at: number;
};

export type Cluster = {
  id: string;
  label: string;
  country: string;
  lat: number;
  lon: number;
  n_sites: number;
  hours: number;
  last_recording: string | null;
  detections: number;
  n_species: number;
  habitats: string[] | null;
};

export type SpeciesRow = {
  species: string;
  common_en: string | null;
  common_fr: string | null;
  common_es: string | null;
  common_nl: string | null;
  common_no: string | null;
  n_detections: number;
  n_sites: number;
  n_countries: number;
  threshold: number;
  threshold_source: "calibrated" | "calibrated_low" | "default";
  n_validated: number;
  n_correct: number;
  precision_at_threshold: number | null;
  calibrated: boolean;
};

export type SpeciesInfo = {
  wiki_title: string | null;
  wiki_url: string | null;
  extract: string | null;
  image_url: string | null;
  image_page: string | null;
  image_artist: string | null;
  image_license: string | null;
  image_license_url: string | null;
};

export type Trend =
  | { label: "uncertain"; reason: string }
  | {
      label: "rising" | "falling" | "steady";
      ratio: number;
      from_year: number;
      to_year: number;
      weeks_compared: number;
      rate_from: number;
      rate_to: number;
    };

export type Ecology = {
  iucn: string | null;
  iucn_label: string | null;
  migration: string | null;
  migration_label: string | null;
  habitats: string[];
  diet: string[];
  lifestyle: string | null;
  trait_source: string | null;
  peak_hour: number | null;
  night_share: number | null;
  active_months: Record<string, number[]>;
  how_to_read: string[];
};

export type SpeciesDetail = SpeciesRow & {
  info: SpeciesInfo | null;
  ecology: Ecology | null;
  hours_recorded: number;
  hours_with_species: number;
  hour_share: number;
  hour_share_range: [number, number];
  n_sites_occupied: number;
  trend: Trend;
  by_country: { country: string; n: number; n_clusters: number }[];
  media: {
    ml_photo_asset: string | null;
    ml_audio_asset: string | null;
    photo_credit: string | null;
    audio_credit: string | null;
  } | null;
};

export type Week = {
  week: number;
  n: number;
  minutes: number;
  rate: number | null;
  low_effort: boolean;
};

export type PhenologyGroup = {
  id: string;
  label: string;
  country: string | null;
  lat: number | null;
  total: number;
  peak_rate: number;
  onset_week: number | null;
  peak_week: number | null;
  end_week: number | null;
  sparse: boolean;
  weeks: Week[];
};

export type MigrationFit = {
  n: number;
  clear: boolean;
  days_per_degree?: number | null;
  intercept?: number | null;
  r2?: number | null;
  km_per_day?: number | null;
  points?: { id: string | null; lat: number; day: number }[] | null;
  reason?: string | null;
};

export type Migration = {
  kind: string | null;
  show_waves: boolean;
  reason: string | null;
  spring: MigrationFit;
  autumn: MigrationFit;
};

export type SpeciesPhenology = {
  species: string;
  migration: Migration;
  season_start_week: number;
  level: "cluster" | "country" | "site";
  year: number | null;
  years: number[];
  week_starts: string[];
  groups: PhenologyGroup[];
};

export type PlaceProfile = {
  level: string;
  id: string;
  year: number | null;
  years: number[];
  week_starts: string[];
  effort_weeks: number[];
  species: {
    species: string;
    common_en: string | null;
    total: number;
    cells: (number | null)[];
  }[];
  diel_species: string | null;
  diel: (number | null)[][];
};

export type Clip = {
  clip_id: string;
  species: string;
  common_en: string | null;
  cluster_id: string;
  cluster: string | null;
  country: string;
  recorded_on: string;
  confidence: number;
  validated: boolean;
  window_start: number;
  window_end: number;
};

export type Device = {
  device: string;
  device_id: string;
  deployment_id: string;
  country: string;
  cluster: string;
  site: string;
  site_id: string | null;
  cluster_id: string | null;
  lat: number;
  lon: number;
  status: "Online" | "Offline" | string;
  last_file: string | null;
  days_since_last: number | null;
  total_recordings: number | null;
  habitat: string | null;
};

export type Activity = {
  dates: string[];
  rows: {
    country: string;
    device: string;
    device_id: string;
    cluster: string | null;
    site: string | null;
    values: number[];
  }[];
};

export type Dataset = {
  total: { total_recordings?: number; total_size_bytes?: number };
  devices: {
    device_id: string;
    device: string;
    total_recordings: number;
    total_size_gb: number;
    avg_file_size_mb: number;
    earliest_recording: string;
    latest_recording: string;
    country: string | null;
    cluster: string | null;
    site: string | null;
  }[];
  monthly_hours: { country: string; month: string; hours: number }[];
};

export type SiteRow = {
  site_id: string;
  site: string;
  cluster: string;
  cluster_id: string;
  country: string;
  lat: number;
  lon: number;
  active: boolean;
  habitat: string | null;
  n_deployments: number;
  n_photos: number;
  status: "Online" | "Offline" | null;
  days_since_last: number | null;
};

export type SiteDetail = SiteRow & {
  deployment_ids: string[];
  device_ids: string[];
  deployments: {
    deployment_id: string;
    device_id: string;
    lat: number;
    lon: number;
    active: boolean;
    habitat: string | null;
    mic_height_cm: number | null;
    mic_direction: string | null;
    coord_uncertainty_m: number | null;
    begin_ts: string | null;
    end_ts: string | null;
    comments: string | null;
  }[];
  photos: { photo_id: string; device_id: string; picture_type: string }[];
  effort: { hours: number | null; first: string | null; last: string | null };
};

export type Validations = {
  by_country: {
    country: string;
    source: string;
    n_validated: number;
    n_correct: number;
    n_species: number;
  }[];
  by_species: {
    species: string;
    common_en: string | null;
    n_validated: number;
    n_correct: number;
    threshold: number | null;
    threshold_source: string | null;
  }[];
};
