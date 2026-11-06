"""Plain-language ecological context to help read the phenology charts."""

import json

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

IUCN_LABELS = {
    "LC": "Least Concern",
    "NT": "Near Threatened",
    "VU": "Vulnerable",
    "EN": "Endangered",
    "CR": "Critically Endangered",
    "EW": "Extinct in the Wild",
    "EX": "Extinct",
    "DD": "Data Deficient",
}

MIGRATION_LABELS = {
    "long_distance": "Long-distance migrant",
    "short_distance": "Short-distance migrant",
    "partial": "Partial migrant",
    "migrant": "Migrant",
    "resident": "Resident",
}

MIGRATION_TEXT = {
    "long_distance": (
        "A long-distance migrant that winters south of the Sahara. The amber spring "
        "wave marks the onset of the vocal season moving north, while the coral autumn "
        "wave marks its end, earlier in the north. Recordings show when birds fall "
        "silent, which can be weeks before they leave; some species call at night on migration."
    ),
    "short_distance": (
        "A short-distance migrant, with many birds wintering in southern and western "
        "Europe. The amber spring wave marks the onset of the vocal season moving "
        "north, while the coral autumn wave marks its end, earlier in the north. "
        "Recordings show when birds fall silent, sometimes weeks before they leave; "
        "some species call at night on migration."
    ),
    "partial": (
        "A partial migrant: some populations stay year-round while others move south, "
        "so the waves may be blurred or absent. Recordings show when birds fall silent, "
        "not necessarily when they leave."
    ),
    "migrant": (
        "The amber spring wave marks the onset of the vocal season moving north, while "
        "the coral autumn wave marks its end, earlier in the north. Recordings show "
        "when birds fall silent, which can be weeks before they leave; some species "
        "call at night on migration."
    ),
    "resident": (
        "A resident species is present all year, so no migration wave is expected. "
        "Peaks show when it is most vocal (usually the breeding season), not arrival or departure."
    ),
}


def _month_span(months: list[int]) -> str:
    if not months:
        return ""
    if len(months) >= 11:
        return "all year"
    # Find the longest run, allowing wrap-around (e.g. Oct–Feb).
    ms = sorted(set(months))
    runs, run = [], [ms[0]]
    for m in ms[1:]:
        if m == run[-1] + 1:
            run.append(m)
        else:
            runs.append(run)
            run = [m]
    runs.append(run)
    if len(runs) > 1 and runs[0][0] == 1 and runs[-1][-1] == 12:
        runs[0] = runs[-1] + runs[0]
        runs.pop()
    main = max(runs, key=len)
    span = (
        MONTHS[main[0] - 1]
        if len(main) == 1
        else f"{MONTHS[main[0] - 1]}–{MONTHS[main[-1] - 1]}"
    )
    return span if len(runs) == 1 else f"mainly {span}"


def describe(eco: dict | None) -> dict | None:
    """Labels and a short 'how to read the chart' text for a species."""
    if not eco:
        return None
    migration = eco.get("migration")
    paragraphs = []
    if migration in MIGRATION_TEXT:
        paragraphs.append(MIGRATION_TEXT[migration])

    observed = []
    peak = eco.get("peak_hour")
    night = eco.get("night_share")
    if night is not None and night >= 0.35:
        observed.append(f"mostly at night (peak around {peak:02d}:00)")
    elif peak is not None:
        when = (
            "at dawn"
            if 3 <= peak <= 7
            else "in the evening"
            if 17 <= peak <= 22
            else "during the day"
        )
        observed.append(f"mostly {when} (peak around {peak:02d}:00)")

    active = json.loads(eco["active_months"]) if eco.get("active_months") else {}
    order = ["Spain", "France", "Netherlands", "Norway"]
    spans = [f"{c} {_month_span(active[c])}" for c in order if active.get(c)]
    if observed or spans:
        text = (
            "In TABMON recordings it is heard " + "; ".join(observed)
            if observed
            else "In TABMON recordings"
        )
        if spans:
            text += (
                ". Most active: " if observed else " it is most active: "
            ) + ", ".join(spans)
        paragraphs.append(text + ".")

    return {
        "iucn": eco.get("iucn"),
        "iucn_label": IUCN_LABELS.get(eco.get("iucn") or ""),
        "migration": migration,
        "migration_label": MIGRATION_LABELS.get(migration or ""),
        "habitats": eco.get("habitats") or [],
        "diet": eco.get("diet") or [],
        "lifestyle": eco.get("lifestyle"),
        "trait_source": eco.get("trait_source"),
        "peak_hour": peak,
        "night_share": night,
        "active_months": active,
        "how_to_read": paragraphs,
    }
