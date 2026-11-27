-- Local fork changelog. The newest entry is announced in all-chat at match start:
--   [OHA Local <revision>] Updates: <changes>
-- To ship a change, add a new entry at the TOP of `history` (keep the older ones).
-- revision = 'YYYY.MM.DD.N' (N counts releases on the same day); keep changes short.
-- Keep the upstream Workshop version in version.ts unchanged.
local history = {
    { revision = '2026.11.26.1', changes = 'Patch 7.42 update; bots no longer freeze at Watchers while jungle farming.' },
    { revision = '2026.10.12.1', changes = 'Roshan readiness uses nearby allies; pit safety and base-defense priority.' },
}

return {
    revision = history[1].revision,
    changes = history[1].changes,
    history = history,
}
